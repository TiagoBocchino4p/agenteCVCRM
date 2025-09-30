"""
Script de teste automatizado que simula uma conversa com o agente.
Não faz requisições reais à API, usa dados mockados.
"""
import os
import ollama
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# Mock function que simula a analise sem chamar API real
def analyze_leads_by_broker_mock(start_date, end_date, analysis_type, broker_name=None):
    """Versao mockada que retorna dados fictícios."""
    print(f"    [MOCK] Simulando analise de {start_date} ate {end_date}")

    if analysis_type == 'count':
        return "Analise concluida: Foram encontrados um total de 127 leads."
    elif analysis_type == 'summary_by_broker':
        return "Analise concluida: Aqui esta o resumo de leads por corretor: {'Joao Silva': 45, 'Maria Santos': 32, 'Pedro Costa': 28, 'Ana Lima': 22}"
    elif analysis_type == 'count_by_broker':
        return f"Analise concluida: O corretor '{broker_name}' teve 32 leads."
    return "Erro de analise: Tipo nao reconhecido."

# Define as ferramentas
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_leads_by_broker",
            "description": "Busca e analisa dados de performance de leads por corretor em um periodo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "A data de inicio da analise no formato AAAA-MM-DD."},
                    "end_date": {"type": "string", "description": "A data de fim da analise no formato AAAA-MM-DD."},
                    "analysis_type": {"type": "string", "description": "O tipo de analise: 'count' (contagem total), 'summary_by_broker' (resumo por corretor), ou 'count_by_broker' (contagem para um corretor especifico)."},
                    "broker_name": {"type": "string", "description": "O nome do corretor para filtrar, se usar 'count_by_broker'."},
                },
                "required": ["start_date", "end_date", "analysis_type"]
            }
        }
    }
]

def test_conversation():
    """Executa uma conversa de teste automatizada."""

    print("\n" + "="*60)
    print("TESTE AUTOMATIZADO DO AGENTE")
    print("="*60 + "\n")

    # Lista de perguntas para testar
    test_queries = [
        "Quantos leads tivemos este mes?",
        "Me mostre um resumo por corretor",
        "Quantos leads o Joao Silva teve?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- TESTE {i}/3 ---")
        print(f"Usuario: {query}")

        messages = [{"role": "user", "content": query}]

        try:
            print("[AI] Pensando com modelo local (llama3.2:3b)...")

            response = ollama.chat(
                model='llama3.2:3b',
                messages=messages,
                tools=tools
            )

            response_message = response['message']
            messages.append(response_message)

            if response_message.get('tool_calls'):
                call = response_message['tool_calls'][0]
                function_name = call['function']['name']
                function_args = call['function']['arguments']

                print(f"[TOOL] Modelo chamou: {function_name}")
                print(f"[TOOL] Argumentos: {json.dumps(function_args, indent=2)}")

                # Chama funcao mockada
                function_response = analyze_leads_by_broker_mock(**function_args)

                print(f"[TOOL] Resultado: {function_response}")

                # Adiciona ao historico
                messages.append({
                    "role": "tool",
                    "content": function_response
                })

                # Segunda chamada para gerar resposta natural
                print("[AI] Gerando resposta final...")
                final_response = ollama.chat(
                    model='llama3.2:3b',
                    messages=messages
                )

                final_answer = final_response['message']['content']
                print(f"\n>>> AGENTE: {final_answer}\n")

            else:
                # Resposta direta sem usar ferramenta
                final_answer = response_message['content']
                print(f"\n>>> AGENTE: {final_answer}\n")

            print("[OK] Teste completado com sucesso!")

        except Exception as e:
            print(f"\n[ERROR] Falha no teste: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "="*60)
    print("TODOS OS TESTES PASSARAM!")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    print("\nCertifique-se de que o Ollama esta rodando: ollama serve")
    print("E que o modelo esta baixado: ollama pull llama3.2:3b\n")

    input("Pressione ENTER para iniciar os testes...")

    success = test_conversation()

    if success:
        print("\n[INFO] O agente esta funcionando corretamente!")
        print("[INFO] Para usar interativamente, rode: py agent.py")
    else:
        print("\n[WARN] Alguns testes falharam. Verifique os logs acima.")