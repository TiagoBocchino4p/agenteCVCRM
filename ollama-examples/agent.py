import os
import requests
import time
import pandas as pd
import ollama
import json
from dotenv import load_dotenv
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. SETUP: LOAD CREDENTIALS (GEMINI KEY IS NO LONGER NEEDED) ---
load_dotenv()

# We no longer need the Gemini API Key
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
CV_SUBDOMAIN = os.getenv("CV_SUBDOMAIN")
CV_EMAIL = os.getenv("CV_EMAIL")
CV_TOKEN = os.getenv("CV_TOKEN")

# We remove the check for the Gemini key
if not all([CV_SUBDOMAIN, CV_EMAIL, CV_TOKEN]):
    raise ValueError("CV CRM credentials (SUBDOMAIN, EMAIL, TOKEN) not found in the .env file.")

# The genai.configure line is removed. litellm requires no configuration for Ollama.


# --- 2. THE API COMMUNICATION CLASS (REMAINS EXACTLY THE SAME) ---
class CVCrmAPI:
    """
    Handles all API communications with the CV CRM, supporting CVDW
    endpoints with robust pagination and rate-limit handling.
    """
    def __init__(self, subdomain: str, email: str, token: str):
        self.base_url = f"https://{subdomain}.cvcrm.com.br/api/v1"
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'email': email,
            'token': token
        }
        print("[OK] CVCrmAPI initialized and ready.")

    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise http_err
        except requests.exceptions.RequestException as err:
            print(f"[ERROR] A network error occurred: {err}")
            raise err

    def _fetch_all_cvdw_pages(self, endpoint: str, base_params: dict = None) -> list:
        if base_params is None: base_params = {}
        all_records = []
        page = 1
        base_params['registros_por_pagina'] = 100
        MAX_RETRIES = 5
        BASE_DELAY_SECONDS = 2
        print(f"[FETCH] Starting full data fetch from CVDW endpoint: {endpoint}...")
        while True:
            current_params = base_params.copy()
            current_params['pagina'] = page
            response = None
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"    Fetching page {page}, attempt {attempt + 1}/{MAX_RETRIES}...")
                    response = self._make_request("GET", endpoint, params=current_params)
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        wait_time = BASE_DELAY_SECONDS * (2 ** attempt)
                        print(f"    [WARN] Rate limit hit (429). Waiting for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)
                    else:
                        print(f"[ERROR] Unrecoverable HTTP error encountered: {e}")
                        raise e
            if response is None:
                print(f"[ERROR] Failed to fetch page {page} after {MAX_RETRIES} attempts. Aborting fetch.")
                break
            records_on_page = response.get("dados")
            if not records_on_page:
                print("    No more data found on the final page. Concluding fetch.")
                break
            all_records.extend(records_on_page)
            if len(records_on_page) < base_params['registros_por_pagina']:
                print("    Partial page returned, indicating this is the final page.")
                break
            page += 1
            time.sleep(0.5)
        print(f"[OK] Finished fetching. Total records retrieved: {len(all_records)}")
        return all_records

    def get_cvdw_lead_performance_by_broker(self, start_date: str, end_date: str) -> list:
        endpoint = "/cvdw/leads"
        params = { "data_inicio": start_date, "data_fim": end_date }
        return self._fetch_all_cvdw_pages(endpoint, params)

# --- 3. HELPER FUNCTION FOR DATE PARSING (REMAINS EXACTLY THE SAME) ---
def get_date_range_from_query(query: str) -> (str, str):
    """
    Analyzes a query for relative date terms and returns a start and end date.
    Returns (None, None) if no specific term is found.
    """
    today = date.today()
    query_lower = query.lower()
    start_date, end_date = None, None
    if "este mês" in query_lower or "neste mês" in query_lower:
        start_date = today.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)
    elif "mês passado" in query_lower:
        last_month_end = today.replace(day=1) - relativedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = last_month_end
    elif "hoje" in query_lower:
        start_date = today
        end_date = today
    if start_date and end_date:
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    else:
        return None, None

# --- 4. THE SMART TOOL DEFINITION (REMAINS EXACTLY THE SAME) ---
cv_api = CVCrmAPI(subdomain=CV_SUBDOMAIN, email=CV_EMAIL, token=CV_TOKEN)
def analyze_leads_by_broker(
    start_date: str, end_date: str, analysis_type: str, broker_name: str = None
) -> str:
    """
    Fetches and analyzes lead performance data from the CV CRM for a given date range.

    Args:
        start_date: The start date for the analysis in YYYY-MM-DD format.
        end_date: The end date for the analysis in YYYY-MM-DD format.
        analysis_type: The type of analysis to perform. Must be one of: 
                       'count' (total leads), 
                       'summary_by_broker' (a breakdown per broker), 
                       'count_by_broker' (count for one specific broker).
        broker_name: The name of the broker to filter by when using 'count_by_broker'.
    """
    print(f"[TOOL] Starting tool 'analyze_leads_by_broker' with analysis type: '{analysis_type}'")
    all_leads = cv_api.get_cvdw_lead_performance_by_broker(start_date, end_date)
    if not all_leads:
        return "Análise concluída: Não foram encontrados leads para o período informado."
    df = pd.DataFrame(all_leads)
    try:
        if analysis_type == 'count':
            total_leads = len(df)
            return f"Análise concluída: Foram encontrados um total de {total_leads} leads."
        elif analysis_type == 'summary_by_broker':
            if 'CorretorNome' not in df.columns:
                return "Erro de análise: A coluna 'CorretorNome' não foi encontrada nos dados."
            counts_by_broker = df['CorretorNome'].value_counts().to_dict()
            return f"Análise concluída: Aqui está o resumo de leads por corretor: {counts_by_broker}"
        elif analysis_type == 'count_by_broker':
            if not broker_name:
                return "Erro de análise: Para contar os leads de um corretor específico, o nome do corretor (broker_name) é necessário."
            if 'CorretorNome' not in df.columns:
                return "Erro de análise: A coluna 'CorretorNome' não foi encontrada nos dados."
            broker_leads_df = df[df['CorretorNome'].str.contains(broker_name, case=False, na=False)]
            count = len(broker_leads_df)
            return f"Análise concluída: O corretor '{broker_name}' teve {count} leads."
        else:
            return f"Erro de análise: O tipo de análise '{analysis_type}' não é reconhecido."
    except Exception as e:
        return f"Erro inesperado durante a análise dos dados: {str(e)}"

# --- 5. THE NEW MAIN AGENT LOGIC FOR OLLAMA ---
def run_agent():
    """Initializes and runs the agent loop using a local Ollama model via litellm."""
    
    # Define the tool in the JSON format that litellm/OpenAI expects
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_leads_by_broker",
                "description": "Busca e analisa dados de performance de leads por corretor em um período.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "A data de início da análise no formato AAAA-MM-DD."},
                        "end_date": {"type": "string", "description": "A data de fim da análise no formato AAAA-MM-DD."},
                        "analysis_type": {"type": "string", "description": "O tipo de análise: 'count' (contagem total), 'summary_by_broker' (resumo por corretor), ou 'count_by_broker' (contagem para um corretor específico)."},
                        "broker_name": {"type": "string", "description": "O nome do corretor para filtrar, se usar 'count_by_broker'."},
                    },
                    "required": ["start_date", "end_date", "analysis_type"]
                }
            }
        }
    ]

    # Keep track of the conversation history
    messages = []
    
    print("\n--- Agente de Análise de Leads (Local com Ollama) ---")
    print("Ola! Estou pronto para ajudar. Digite 'sair' para terminar.")

    while True:
        user_input = input("\nVoce: ")
        if user_input.lower() in ['sair', 'exit', 'quit']:
            print("Ate logo!")
            break

        messages.append({"role": "user", "content": user_input})
        
        try:
            # --- First call to the local AI model ---
            print("[AI] Pensando com o modelo local...")
            response = ollama.chat(
                model='llama3.2:3b',
                messages=messages,
                tools=tools
            )

            # --- Manual Tool Calling Logic ---
            response_message = response['message']
            messages.append(response_message)

            if response_message.get('tool_calls'):
                call = response_message['tool_calls'][0]
                function_name = call['function']['name']

                if function_name == "analyze_leads_by_broker":
                    function_args = call['function']['arguments']
                    print(f"[TOOL] Modelo local escolheu a ferramenta: '{function_name}' com argumentos: {function_args}")

                    # Call the actual Python function with the arguments from the AI
                    function_response = analyze_leads_by_broker(**function_args)

                    # Add the tool's result to the conversation history
                    messages.append({
                        "role": "tool",
                        "content": function_response
                    })

                    # --- Second call to the model to get a natural language summary ---
                    print("[AI] Gerando a resposta final...")
                    final_response = ollama.chat(
                        model='llama3.2:3b',
                        messages=messages
                    )
                    final_answer = final_response['message']['content']
                    print(f"\nAgente: {final_answer}")
                    messages.append(final_response['message'])

            else:
                # The model gave a direct answer without using a tool
                final_answer = response_message['content']
                print(f"\nAgente: {final_answer}")

        except Exception as e:
            print(f"\n[ERROR] Ocorreu um erro: {e}")
            messages.pop() # Remove the last user message if an error occurred

if __name__ == "__main__":
    # Make sure the Ollama application is running in the background!
    run_agent()