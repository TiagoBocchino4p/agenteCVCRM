"""
Conector CVDW - Conexão limpa e otimizada com API CVDW
Baseado no método Power BI que funciona
"""
import requests
import json
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class CVDWConnector:
    """Conector otimizado para API CVDW da BP Incorporadora"""
    
    def __init__(self, email: str = None, token: str = None):
        """Inicializa conector com credenciais"""
        
        # Usa credenciais fornecidas ou do .env
        self.email = email or os.getenv('CVCRM_EMAIL')
        self.token = token or os.getenv('CVCRM_TOKEN')
        
        if not self.email or not self.token:
            raise ValueError("Email e token são obrigatórios")
        
        # Configuração da API (método Power BI)
        self.base_url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw"
        self.headers = {
            "email": self.email,
            "token": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Cache simples
        self.cache = {}
        self.cache_timeout = 300  # 5 minutos
        
        # Status
        self.last_test_result = None
        self.total_leads_available = 0
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão com API CVDW com retry inteligente"""
        
        max_retries = 3
        base_delay = 5  # segundos
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (attempt + 1)  # 5, 10, 15 segundos
                    print(f"[RETRY {attempt+1}] Aguardando {delay}s para evitar rate limit...")
                    time.sleep(delay)
                
                # Chamada de teste com poucos registros
                response = requests.get(
                    f"{self.base_url}/leads",
                    headers=self.headers,
                    params={"registros_por_pagina": 10},
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict) and 'total_de_registros' in data:
                        self.total_leads_available = data.get('total_de_registros', 0)
                        
                        result = {
                            "status": "success",
                            "message": f"API CVDW online - {self.total_leads_available} leads disponíveis",
                            "total_leads": self.total_leads_available,
                            "total_paginas": data.get('total_de_paginas', 0),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        self.last_test_result = result
                        return result
                    else:
                        return {
                            "status": "error",
                            "message": "Formato de resposta inesperado da API"
                        }
                        
                elif response.status_code == 429:  # Rate limiting
                    if attempt < max_retries - 1:
                        print(f"[RATE LIMIT] Tentativa {attempt+1} - aguardando mais...")
                        continue
                    else:
                        return {
                            "status": "warning",
                            "message": "API temporariamente indisponível (rate limit) - tente novamente em alguns minutos",
                            "retry_suggested": True
                        }
                else:
                    return {
                        "status": "error", 
                        "message": f"API retornou status {response.status_code}"
                    }
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                return {
                    "status": "error",
                    "message": f"Erro ao conectar: {str(e)}"
                }
        
        return {
            "status": "error",
            "message": "Não foi possível conectar após múltiplas tentativas"
        }
    
    def get_leads(self, limit: int = 100, start_page: int = 1) -> Dict[str, Any]:
        """Busca leads da API CVDW com paginação"""
        
        # Verifica cache
        cache_key = f"leads_{limit}_{start_page}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_timeout:
                return cached_data['data']
        
        leads_collected = []
        page = start_page
        records_per_page = min(500, limit)  # Máximo 500 por página
        
        try:
            while len(leads_collected) < limit:
                # Controle de rate limiting
                if page > start_page:
                    time.sleep(2)  # Aguarda 2s entre páginas
                
                response = requests.get(
                    f"{self.base_url}/leads",
                    headers=self.headers,
                    params={
                        "registros_por_pagina": records_per_page,
                        "pagina": page
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'dados' in data and data['dados']:
                        page_leads = data['dados']
                        leads_collected.extend(page_leads)
                        
                        print(f"[CVDW] Página {page}: {len(page_leads)} leads (Total: {len(leads_collected)})")
                        
                        # Para se atingiu o limite ou última página
                        if len(leads_collected) >= limit or page >= data.get('total_de_paginas', 1):
                            break
                            
                        page += 1
                    else:
                        break  # Não há mais dados
                        
                elif response.status_code == 429:
                    print("[RATE LIMIT] Aguardando...")
                    time.sleep(10)
                    continue
                    
                else:
                    return {
                        "status": "error",
                        "message": f"Erro HTTP {response.status_code}"
                    }
            
            # Limita ao solicitado
            leads_collected = leads_collected[:limit]
            
            result = {
                "status": "success",
                "leads": leads_collected,
                "total_coletados": len(leads_collected),
                "metadata": {
                    "paginas_processadas": page - start_page + 1,
                    "total_disponivel": self.total_leads_available or len(leads_collected)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Atualiza cache
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Erro ao buscar leads: {str(e)}"
            }
    
    def analyze_leads(self, leads: List[Dict], query_type: str = "general") -> List[str]:
        """Analisa leads e gera insights"""
        
        if not leads:
            return ["Nenhum lead encontrado para análise"]
        
        insights = []
        insights.append(f"Total de leads analisados: {len(leads)}")
        
        # Análise por situação
        situacoes = {}
        origens = {}
        responsaveis = {}
        
        for lead in leads:
            # Situações
            situacao = lead.get('situacao', 'Não informado')
            situacoes[situacao] = situacoes.get(situacao, 0) + 1
            
            # Origens
            origem = lead.get('origem_nome', lead.get('origem', 'Não informado'))
            origens[origem] = origens.get(origem, 0) + 1
            
            # Responsáveis (verifica múltiplos campos)
            responsavel = (lead.get('corretor') or 
                         lead.get('responsavel') or 
                         lead.get('gestor') or 
                         lead.get('vendedor') or 
                         'Não informado')
            responsaveis[responsavel] = responsaveis.get(responsavel, 0) + 1
        
        # Top situações
        if situacoes:
            top_situacoes = sorted(situacoes.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"Top situações: {', '.join([f'{s}: {c}' for s, c in top_situacoes])}")
        
        # Análises específicas baseadas no tipo de query
        if "origem" in query_type.lower() and origens:
            top_origens = sorted(origens.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"Top origens: {', '.join([f'{o}: {c}' for o, c in top_origens])}")
        
        if any(word in query_type.lower() for word in ["sdr", "responsavel", "corretor"]) and responsaveis:
            top_responsaveis = sorted(responsaveis.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"Top responsáveis: {', '.join([f'{r}: {c}' for r, c in top_responsaveis])}")
        
        return insights

def create_connector(email: str = None, token: str = None) -> CVDWConnector:
    """Factory function para criar conector"""
    return CVDWConnector(email, token)