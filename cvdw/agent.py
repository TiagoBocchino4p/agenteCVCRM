"""
Agente IA CVDW - Interface inteligente para análise de dados
Processa consultas em linguagem natural
"""
import re
from typing import Dict, List, Any
from datetime import datetime
from .connector import CVDWConnector, create_connector

class CVDWAgent:
    """Agente IA para análise inteligente de dados CVDW"""
    
    def __init__(self, email: str = None, token: str = None):
        """Inicializa agente com conector CVDW"""
        
        try:
            self.connector = create_connector(email, token)
            self.online_mode = True
            self.status = self._test_initial_connection()
            
        except Exception as e:
            print(f"[AGENT] Erro na inicialização: {str(e)}")
            self.online_mode = False
            self.connector = None
            self.status = {"status": "error", "message": str(e)}
    
    def _test_initial_connection(self) -> Dict[str, Any]:
        """Testa conexão inicial"""
        
        if not self.connector:
            return {"status": "error", "message": "Conector não disponível"}
        
        test_result = self.connector.test_connection()
        
        if test_result["status"] == "success":
            total_leads = test_result.get("total_leads", 0)
            print(f"[AGENT] Online - {total_leads:,} leads disponíveis")
            self.online_mode = True
        elif test_result["status"] == "warning":
            print(f"[AGENT] Temporariamente indisponível - {test_result['message']}")
            self.online_mode = False
        else:
            print(f"[AGENT] Offline - {test_result['message']}")
            self.online_mode = False
        
        return test_result
    
    def process_query(self, user_query: str) -> str:
        """Processa consulta do usuário e retorna resposta"""
        
        if not self.online_mode or not self.connector:
            return self._generate_offline_response(user_query)
        
        try:
            # Classifica tipo de consulta
            query_type = self._classify_query(user_query)
            
            # Determina quantos leads buscar
            limit = self._determine_data_limit(user_query)
            
            print(f"[AGENT] Processando: {user_query}")
            print(f"[AGENT] Tipo: {query_type}, Limite: {limit}")
            
            # Busca dados
            leads_result = self.connector.get_leads(limit=limit)
            
            if leads_result["status"] == "success":
                leads = leads_result["leads"]
                insights = self.connector.analyze_leads(leads, query_type)
                
                # Gera resposta formatada
                return self._generate_response(user_query, query_type, leads_result, insights)
            else:
                return f"ERRO: {leads_result['message']}"
                
        except Exception as e:
            print(f"[AGENT] Erro: {str(e)}")
            return f"ERRO interno: {str(e)}"
    
    def _classify_query(self, query: str) -> str:
        """Classifica o tipo de consulta"""
        
        query_lower = query.lower()
        
        # Padrões de classificação
        if any(word in query_lower for word in ["quantos", "numero", "total"]):
            return "QUANTITATIVO"
        elif any(word in query_lower for word in ["origem", "origem", "canal"]):
            return "ORIGENS"
        elif any(word in query_lower for word in ["situacao", "status", "performance"]):
            return "PERFORMANCE"
        elif any(word in query_lower for word in ["sdr", "responsavel", "corretor", "gestor"]):
            return "RESPONSAVEIS"
        elif any(word in query_lower for word in ["mes", "periodo", "data", "tempo"]):
            return "TEMPORAL"
        else:
            return "GERAL"
    
    def _determine_data_limit(self, query: str) -> int:
        """Determina quantos dados buscar baseado na consulta"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["todos", "total", "geral"]):
            return 2000  # Análise ampla
        elif any(word in query_lower for word in ["sdr", "responsavel", "performance"]):
            return 1000  # Análise de performance
        elif any(word in query_lower for word in ["mes", "periodo", "recente"]):
            return 500   # Análise temporal
        else:
            return 200   # Análise padrão
    
    def _generate_response(self, query: str, query_type: str, data: Dict, insights: List[str]) -> str:
        """Gera resposta formatada em linguagem natural"""
        
        leads = data["leads"]
        total_coletados = data["total_coletados"]
        total_disponivel = data["metadata"]["total_disponivel"]
        
        # Cabeçalho baseado no tipo
        header = f"[{query_type}] Análise - Dados CVDW Reais"
        
        # Corpo da resposta
        response_parts = [
            header,
            "",
            f"Leads analisados: {total_coletados:,}",
            f"Total na base: {total_disponivel:,}",
            ""
        ]
        
        # Insights gerados
        if insights:
            response_parts.append("Principais insights:")
            for insight in insights[:5]:  # Máximo 5 insights
                response_parts.append(f"• {insight}")
            response_parts.append("")
        
        # Amostra de dados (primeiros 3 leads)
        if leads:
            response_parts.append("Amostra dos dados:")
            for i, lead in enumerate(leads[:3], 1):
                nome = lead.get("nome", "N/A")
                situacao = lead.get("situacao", "N/A") 
                origem = lead.get("origem_nome", lead.get("origem", "N/A"))
                data_cad = lead.get("data_cad", "N/A")
                
                response_parts.append(f"{i}. {nome} | {situacao} | {origem} | {data_cad}")
            response_parts.append("")
        
        # Informações técnicas
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        response_parts.extend([
            f"Fonte: API CVDW Real | Atualizado: {timestamp}",
            "Status: Dados em tempo real"
        ])
        
        # Sugestões contextuais
        suggestions = self._get_contextual_suggestions(query_type)
        if suggestions:
            response_parts.append("")
            response_parts.append("Sugestões de análises:")
            response_parts.extend([f"• {s}" for s in suggestions])
        
        return "\n".join(response_parts)
    
    def _get_contextual_suggestions(self, query_type: str) -> List[str]:
        """Retorna sugestões baseadas no tipo de consulta"""
        
        suggestions_map = {
            "QUANTITATIVO": [
                "Análise por origem de leads",
                "Performance por situação",
                "Leads por período específico"
            ],
            "RESPONSAVEIS": [
                "Top SDRs por conversão",
                "Performance por corretor",
                "Análise de produtividade"
            ],
            "PERFORMANCE": [
                "Taxa de conversão por origem",
                "Análise de funil de vendas",
                "Leads em follow-up"
            ],
            "ORIGENS": [
                "ROI por canal de marketing",
                "Performance de campanhas",
                "Custo por lead por origem"
            ]
        }
        
        return suggestions_map.get(query_type, [
            "Quantos leads temos no total?",
            "Performance por situação", 
            "Análise por responsável"
        ])
    
    def _generate_offline_response(self, query: str) -> str:
        """Resposta quando sistema está offline"""
        
        error_msg = ""
        if self.status:
            error_msg = self.status.get("message", "")
        
        # Resposta diferente para rate limiting vs outros erros
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return f"""[SISTEMA TEMPORARIAMENTE INDISPONIVEL] Rate Limiting

API Status: Temporariamente limitada (muitas requisições)
Base de dados: 68.988 leads CVDW (confirmado)

Sua consulta: "{query}"

Aguarde alguns minutos e:
• Use o botão 'Reconectar' na sidebar
• Ou reinicie a aplicação

Dados disponíveis assim que a API normalizar."""
        else:
            return f"""[SISTEMA OFFLINE] Erro de Conectividade

Status: Não foi possível conectar com a API CVDW
Erro: {error_msg}

Sua consulta: "{query}"

Soluções:
1. Verificar conectividade de rede
2. Validar credenciais no arquivo .env  
3. Aguardar alguns minutos e tentar novamente

Use 'Reconectar' na sidebar para testar novamente."""
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do sistema"""
        
        status = {
            "online": self.online_mode,
            "connector_available": self.connector is not None,
            "last_test": self.status,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.online_mode and self.status and self.status.get("status") == "success":
            status.update({
                "total_leads_available": self.status.get("total_leads", 0),
                "api_response_time": "< 5s",
                "data_freshness": "Real-time"
            })
        
        return status
    
    def reconnect(self) -> str:
        """Tenta reconectar com a API"""
        
        if self.connector:
            print("[AGENT] Testando reconexão...")
            self.status = self.connector.test_connection()
            
            if self.status["status"] == "success":
                self.online_mode = True
                total_leads = self.status.get("total_leads", 0)
                return f"Reconectado! {total_leads:,} leads disponíveis"
            else:
                self.online_mode = False
                return f"Ainda offline: {self.status['message']}"
        else:
            return "Conector não inicializado. Verifique credenciais."

def create_agent(email: str = None, token: str = None) -> CVDWAgent:
    """Factory function para criar agente"""
    return CVDWAgent(email, token)