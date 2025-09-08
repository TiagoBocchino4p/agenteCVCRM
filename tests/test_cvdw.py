"""
Testes básicos para o sistema CVDW
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from cvdw.connector import create_connector
from cvdw.agent import create_agent
from utils.helpers import format_number, clean_text, validate_leads_data

def test_config():
    """Testa configurações"""
    print("=== TESTE: Configurações ===")
    
    validation = Config.validate()
    print(f"Configuração válida: {validation['valid']}")
    
    if validation["errors"]:
        print("Erros encontrados:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    if validation["warnings"]:
        print("Avisos:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    summary = Config.get_summary()
    print(f"API habilitada: {summary['api_enabled']}")
    print(f"URL CVDW: {summary['cvdw_url']}")
    
    return validation["valid"]

def test_connector():
    """Testa conector CVDW"""
    print("\n=== TESTE: Conector CVDW ===")
    
    try:
        connector = create_connector()
        print("Conector criado com sucesso")
        
        # Teste de conexão
        test_result = connector.test_connection()
        print(f"Status da conexão: {test_result['status']}")
        print(f"Mensagem: {test_result.get('message', 'N/A')}")
        
        if test_result["status"] == "success":
            total_leads = test_result.get("total_leads", 0)
            print(f"Total de leads disponíveis: {format_number(total_leads)}")
            
            # Teste de busca de leads
            print("\nTestando busca de leads...")
            leads_result = connector.get_leads(limit=10)
            
            if leads_result["status"] == "success":
                leads = leads_result["leads"]
                print(f"Coletados: {len(leads)} leads")
                
                if leads:
                    first_lead = leads[0]
                    print(f"Primeiro lead: {first_lead.get('nome', 'N/A')}")
                    print(f"Situação: {first_lead.get('situacao', 'N/A')}")
                    print(f"Origem: {first_lead.get('origem_nome', 'N/A')}")
                
                # Valida qualidade dos dados
                validation = validate_leads_data(leads)
                print(f"Qualidade dos dados: {validation['data_quality']['quality_score']}")
                
                return True
            else:
                print(f"Erro ao buscar leads: {leads_result['message']}")
                return False
        else:
            print("Conexão falhou")
            return False
            
    except Exception as e:
        print(f"Erro no teste do conector: {str(e)}")
        return False

def test_agent():
    """Testa agente IA"""
    print("\n=== TESTE: Agente IA ===")
    
    try:
        agent = create_agent()
        print("Agente criado com sucesso")
        
        # Status do sistema
        status = agent.get_system_status()
        print(f"Agente online: {status['online']}")
        
        if status["online"]:
            total_available = status.get("total_leads_available", 0)
            print(f"Leads disponíveis: {format_number(total_available)}")
            
            # Testa consultas
            test_queries = [
                "Quantos leads temos no total?",
                "Performance por situação"
            ]
            
            for query in test_queries:
                print(f"\nTeste: {query}")
                response = agent.process_query(query)
                
                # Mostra primeiras linhas da resposta
                response_lines = response.split('\n')
                for line in response_lines[:5]:
                    if line.strip():
                        print(f"  {clean_text(line)}")
                
                if len(response_lines) > 5:
                    print("  ...")
            
            return True
        else:
            print("Agente offline - não é possível testar consultas")
            return False
            
    except Exception as e:
        print(f"Erro no teste do agente: {str(e)}")
        return False

def test_utils():
    """Testa utilitários"""
    print("\n=== TESTE: Utilitários ===")
    
    # Teste formatação
    assert format_number(68988) == "68.988"
    print("Formatacao de numeros OK")
    
    # Teste limpeza de texto
    dirty_text = "  Texto   com\n\nespacos  extras  "
    clean = clean_text(dirty_text)
    assert clean == "Texto com espacos extras"
    print("Limpeza de texto OK")
    
    # Teste validação de dados mock
    mock_leads = [
        {"nome": "Joao Silva", "situacao": "VENDA REALIZADA"},
        {"nome": "Maria Santos", "situacao": "RESERVA"},
        {"nome": "", "situacao": ""}  # Lead com dados incompletos
    ]
    
    validation = validate_leads_data(mock_leads)
    assert validation["valid"] == True
    assert validation["total_records"] == 3
    print(f"Validacao de dados OK - Score: {validation['data_quality']['quality_score']}")
    
    return True

def run_all_tests():
    """Executa todos os testes"""
    print("INICIANDO TESTES DO SISTEMA AGENTE POWERBI")
    print("=" * 50)
    
    results = []
    
    # Testa cada componente
    results.append(("Configurações", test_config()))
    results.append(("Utilitários", test_utils()))
    results.append(("Conector CVDW", test_connector()))
    results.append(("Agente IA", test_agent()))
    
    # Relatório final
    print("\n" + "=" * 50)
    print("RELATORIO FINAL DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "PASSOU" if success else "FALHOU"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("TODOS OS TESTES PASSARAM - SISTEMA FUNCIONANDO!")
    else:
        print("ALGUNS TESTES FALHARAM - VERIFIQUE CONFIGURACOES")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()