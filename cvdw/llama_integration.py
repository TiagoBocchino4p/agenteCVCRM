"""
Integração Ollama/Llama - Processamento inteligente de respostas
Melhora as respostas do agente com IA local
"""
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

class OllamaIntegration:
    """Integração com Ollama para processamento de linguagem natural"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """Inicializa integração Ollama"""
        
        self.base_url = base_url
        self.model = model
        self.available = self._test_connection()
        
        if self.available:
            print(f"[OLLAMA] Conectado - Modelo: {self.model}")
        else:
            print("[OLLAMA] Não disponível - funcionando sem IA")
    
    def _test_connection(self) -> bool:
        """Testa conexão com Ollama"""
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def enhance_response(self, user_query: str, data_analysis: str, leads_data: List[Dict]) -> str:
        """Melhora resposta usando Llama"""
        
        if not self.available:
            return data_analysis  # Retorna análise original se Ollama indisponível
        
        # Prepara contexto para Llama
        context = self._prepare_context(user_query, data_analysis, leads_data)
        
        # Prompt otimizado para análise de dados
        prompt = f"""Você é um especialista em análise de dados de marketing imobiliário. 
        
Consulta do usuário: "{user_query}"

Dados analisados:
{data_analysis}

Contexto adicional dos dados:
{context}

Sua tarefa:
1. Forneça uma resposta clara e objetiva
2. Destaque insights importantes
3. Use linguagem profissional mas acessível
4. Inclua números específicos quando relevante
5. Sugira próximos passos se apropriado

Resposta:"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Mais conservador para dados
                        "top_p": 0.9,
                        "max_tokens": 512
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced_text = result.get("response", "").strip()
                
                if enhanced_text and len(enhanced_text) > 50:
                    return f"{enhanced_text}\n\n---\n📊 Fonte: API CVDW Real | Processado com IA Local"
                else:
                    return data_analysis  # Fallback se resposta muito curta
            else:
                return data_analysis  # Fallback se erro HTTP
                
        except Exception as e:
            print(f"[OLLAMA] Erro: {str(e)}")
            return data_analysis  # Fallback se erro
    
    def _prepare_context(self, query: str, analysis: str, leads_data: List[Dict]) -> str:
        """Prepara contexto adicional para Llama"""
        
        context_parts = []
        
        # Estatísticas básicas
        if leads_data:
            total_leads = len(leads_data)
            context_parts.append(f"Total de leads analisados: {total_leads}")
            
            # Campos únicos presentes
            if leads_data:
                sample_lead = leads_data[0]
                context_parts.append(f"Dados disponíveis por lead: {len(sample_lead)} campos")
                
                # Situações únicas
                situacoes = set(lead.get('situacao', '') for lead in leads_data[:100])  # Sample
                if situacoes:
                    context_parts.append(f"Situações encontradas: {', '.join(list(situacoes)[:5])}")
                
                # Origens únicas
                origens = set(lead.get('origem_nome', '') for lead in leads_data[:100])
                if origens:
                    context_parts.append(f"Principais origens: {', '.join(list(origens)[:5])}")
        
        return "\n".join(context_parts)
    
    def generate_insights(self, leads_data: List[Dict], analysis_type: str = "general") -> List[str]:
        """Gera insights inteligentes usando Llama"""
        
        if not self.available or not leads_data:
            return []
        
        # Amostra dos dados para análise
        sample_size = min(50, len(leads_data))
        sample_leads = leads_data[:sample_size]
        
        # Estatísticas rápidas
        total_leads = len(leads_data)
        situacoes = {}
        origens = {}
        
        for lead in sample_leads:
            situacao = lead.get('situacao', 'Não informado')
            origem = lead.get('origem_nome', 'Não informado')
            
            situacoes[situacao] = situacoes.get(situacao, 0) + 1
            origens[origem] = origens.get(origem, 0) + 1
        
        # Prepara prompt para insights
        prompt = f"""Analise estes dados de leads imobiliários e gere insights valiosos:

Total de leads: {total_leads}
Amostra analisada: {sample_size} leads

Situações encontradas:
{json.dumps(situacoes, indent=2)}

Origens dos leads:
{json.dumps(origens, indent=2)}

Gere 3-5 insights práticos e acionáveis baseados nestes dados. Foque em:
- Padrões interessantes
- Oportunidades de melhoria
- Recomendações estratégicas

Formato: Lista de insights curtos e objetivos.

Insights:"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9,
                        "max_tokens": 300
                    }
                },
                timeout=25
            )
            
            if response.status_code == 200:
                result = response.json()
                insights_text = result.get("response", "").strip()
                
                # Processa resposta em lista
                insights = []
                for line in insights_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        insight = line.lstrip('-•* ').strip()
                        if len(insight) > 10:  # Filtra linhas muito curtas
                            insights.append(insight)
                
                return insights[:5]  # Máximo 5 insights
                
        except Exception as e:
            print(f"[OLLAMA] Erro ao gerar insights: {str(e)}")
            
        return []
    
    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """Classifica intenção da consulta usando Llama"""
        
        if not self.available:
            return self._basic_classification(query)
        
        prompt = f"""Analise esta consulta sobre dados de marketing imobiliário e classifique:

Consulta: "{query}"

Classifique em uma das categorias:
- QUANTITATIVO: Perguntas sobre números, totais, contagens
- PERFORMANCE: Análise de desempenho, rankings, comparações
- TEMPORAL: Consultas sobre períodos, datas, tendências
- ORIGEM: Análise de canais, fontes, campanhas
- SITUACAO: Status de leads, funil de vendas
- RESPONSAVEL: Performance de equipe, SDRs, corretores
- GERAL: Consultas gerais ou explorações

Responda APENAS a categoria, sem explicações.

Categoria:"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Muito conservador para classificação
                        "max_tokens": 20
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result.get("response", "").strip().upper()
                
                valid_categories = ["QUANTITATIVO", "PERFORMANCE", "TEMPORAL", "ORIGEM", "SITUACAO", "RESPONSAVEL", "GERAL"]
                
                if classification in valid_categories:
                    return {
                        "category": classification,
                        "confidence": 0.8,
                        "source": "llama"
                    }
                    
        except Exception as e:
            print(f"[OLLAMA] Erro na classificação: {str(e)}")
        
        # Fallback para classificação básica
        return self._basic_classification(query)
    
    def _basic_classification(self, query: str) -> Dict[str, Any]:
        """Classificação básica sem IA"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["quantos", "total", "numero"]):
            return {"category": "QUANTITATIVO", "confidence": 0.7, "source": "basic"}
        elif any(word in query_lower for word in ["sdr", "responsavel", "corretor"]):
            return {"category": "RESPONSAVEL", "confidence": 0.7, "source": "basic"}
        elif any(word in query_lower for word in ["origem", "canal", "campanha"]):
            return {"category": "ORIGEM", "confidence": 0.7, "source": "basic"}
        elif any(word in query_lower for word in ["situacao", "status", "performance"]):
            return {"category": "PERFORMANCE", "confidence": 0.7, "source": "basic"}
        else:
            return {"category": "GERAL", "confidence": 0.5, "source": "basic"}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status da integração"""
        
        status = {
            "available": self.available,
            "model": self.model,
            "base_url": self.base_url
        }
        
        if self.available:
            try:
                # Testa modelo específico
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": "Test",
                        "stream": False,
                        "options": {"max_tokens": 5}
                    },
                    timeout=5
                )
                status["model_ready"] = response.status_code == 200
            except:
                status["model_ready"] = False
        
        return status


def create_ollama_integration(model: str = "phi3:mini") -> OllamaIntegration:
    """Factory function para criar integração Ollama"""
    return OllamaIntegration(model=model)