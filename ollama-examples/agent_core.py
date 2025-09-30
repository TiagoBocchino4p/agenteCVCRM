# agent_core.py

import os
import pandas as pd
from datetime import datetime, timedelta
import ollama
from cv_crm_api import CVCrmAPI
from dotenv import load_dotenv

# --- Configuration: Load from .env ---
load_dotenv()
CV_CRM_SUBDOMAIN = os.getenv("CV_SUBDOMAIN")
CV_CRM_EMAIL = os.getenv("CV_EMAIL")
CV_CRM_TOKEN = os.getenv("CV_TOKEN")

if not all([CV_CRM_SUBDOMAIN, CV_CRM_EMAIL, CV_CRM_TOKEN]):
    raise ValueError("CV CRM credentials not found in .env file")

# --- Initialize Services ---
crm = CVCrmAPI(subdomain=CV_CRM_SUBDOMAIN, email=CV_CRM_EMAIL, token=CV_CRM_TOKEN)


# --- Analytical Tools (Functions) ---
def get_last_month_dates():
    """Helper function to get start and end dates for the previous month."""
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month.strftime('%Y-%m-%d'), last_day_of_last_month.strftime('%Y-%m-%d')

def analyze_client_origins() -> str:
    """Analisa e conta as origens de todos os clientes (pessoas) cadastrados no CRM."""
    clients_data = crm.get_all_clients()
    if not clients_data: return "Não foi possível obter a lista de clientes ou a lista está vazia."
    df = pd.DataFrame(clients_data)
    if 'origem_compra' not in df.columns: return "A coluna 'origem_compra' não foi encontrada."
    origin_counts = df['origem_compra'].value_counts().reset_index()
    origin_counts.columns = ['Origem', 'Quantidade']
    return "Análise da Origem dos Clientes:\n" + origin_counts.to_string(index=False)

def analyze_leads_by_broker() -> str:
    """Calcula e lista os corretores que mais geraram leads no mês passado, usando o endpoint de Data Warehouse (CVDW)."""
    start_date, end_date = get_last_month_dates()
    performance_data = crm.get_cvdw_lead_performance_by_broker(start_date, end_date)
    if not performance_data: return f"Nenhum dado de performance encontrado para o período ({start_date} a {end_date})."
    df = pd.DataFrame(performance_data)
    if 'corretor' not in df.columns or 'total' not in df.columns: return "Colunas esperadas ('corretor', 'total') não encontradas."
    df = df.rename(columns={'corretor': 'Corretor', 'total': 'Total de Leads'})
    df_sorted = df.sort_values(by='Total de Leads', ascending=False)
    return f"Performance dos Corretores (CVDW) ({start_date} a {end_date}):\n" + df_sorted.to_string(index=False)

# --- Tool Mapping ---
TOOLS_MAP = {
    "analyze_client_origins": analyze_client_origins,
    "analyze_leads_by_broker": analyze_leads_by_broker,
}

# --- Main Agent Logic ---
def get_agent_response(user_query: str) -> str:
    """Main function to get a response from the AI agent."""
    print(f"\n[USER] Query: '{user_query}'")
    tools_description = ""
    for name, func in TOOLS_MAP.items():
        tools_description += f"Ferramenta: {name}\nDescricao: {func.__doc__}\n---\n"

    prompt = f"""
    Voce e um assistente de analise de dados para uma imobiliaria. Sua tarefa e analisar a pergunta do usuario e escolher a melhor ferramenta para responde-la.
    Responda APENAS com o nome exato da ferramenta.

    Ferramentas disponiveis:
    ---
    {tools_description}

    Pergunta do Usuario: "{user_query}"
    Qual ferramenta devo usar?
    """

    print("[AI] Escolhendo ferramenta...")
    response = ollama.chat(
        model='llama3.2:3b',
        messages=[{'role': 'user', 'content': prompt}]
    )
    chosen_tool_name = response['message']['content'].strip()

    print(f"[TOOL] Escolhida: '{chosen_tool_name}'")
    if chosen_tool_name in TOOLS_MAP:
        tool_function = TOOLS_MAP[chosen_tool_name]
        result = tool_function()

        print("[AI] Formatando resposta final...")
        formatting_prompt = f"""
        A pergunta original do usuario foi: "{user_query}"
        O resultado da analise foi:
        ---
        {result}
        ---
        Formule uma resposta amigavel e clara para o usuario em portugues.
        """
        final_response = ollama.chat(
            model='llama3.2:3b',
            messages=[{'role': 'user', 'content': formatting_prompt}]
        )
        return final_response['message']['content']
    else:
        return "Desculpe, nao tenho uma ferramenta para responder a essa pergunta. Tente novamente."

if __name__ == "__main__":
    print("\n--- Agente de Analise CV CRM (Versao Ollama) ---")
    print("Digite 'sair' para terminar.\n")
    while True:
        user_input = input("\n> ")
        if user_input.lower() == 'sair':
            print("Ate logo!")
            break
        response = get_agent_response(user_input)
        print(f"\nAgente: {response}")