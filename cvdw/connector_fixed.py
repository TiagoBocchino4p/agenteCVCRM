"""
Conector CVDW FIXED - Solução final para pegar dados de 2025
Rate limit inteligente + busca nas últimas páginas
"""
import requests
import time
import os
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CVDWConnectorFixed:
    """Conector definitivo - pega dados de 2025"""
    
    def __init__(self):
        self.email = os.getenv('CVCRM_EMAIL')
        self.token = os.getenv('CVCRM_TOKEN')
        self.base_url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw"
        self.headers = {
            "email": self.email,
            "token": self.token,
            "Accept": "application/json"
        }
    
    def wait_for_rate_limit(self, initial_delay=60):
        """Espera rate limit passar com retry inteligente"""
        delay = initial_delay
        max_attempts = 10
        
        for attempt in range(max_attempts):
            print(f"[FIXED] Tentativa {attempt+1}/{max_attempts} - aguardando {delay}s...")
            time.sleep(delay)
            
            try:
                response = requests.get(
                    f"{self.base_url}/leads",
                    headers=self.headers,
                    params={"registros_por_pagina": 5},
                    timeout=20
                )
                
                if response.status_code == 200:
                    print("[FIXED] ✅ Rate limit passou! API disponível")
                    return True
                elif response.status_code == 429:
                    delay = min(delay * 1.5, 300)  # Aumenta delay até 5min max
                    print(f"[FIXED] Ainda em rate limit, próxima tentativa em {delay}s")
                else:
                    print(f"[FIXED] Status inesperado: {response.status_code}")
                    delay = 30
                    
            except Exception as e:
                print(f"[FIXED] Erro: {str(e)}")
                delay = 30
        
        return False
    
    def get_september_2025_leads_direct(self):
        """
        Estratégia direta: Tentar múltiplas abordagens para pegar dados de 2025
        """
        
        print("[FIXED] Iniciando busca por dados de setembro/2025...")
        
        # Espera rate limit passar
        if not self.wait_for_rate_limit(30):
            return {"status": "error", "message": "Rate limit não passou"}
        
        leads_2025 = []
        total_pages = 0
        
        try:
            # Primeiro: Descobre total de páginas
            print("[FIXED] Descobrindo total de páginas...")
            response = requests.get(
                f"{self.base_url}/leads",
                headers=self.headers,
                params={"registros_por_pagina": 10},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                total_pages = data.get('total_de_paginas', 0)
                total_records = data.get('total_de_registros', 0)
                print(f"[FIXED] Total: {total_records} leads em {total_pages} páginas")
            else:
                return {"status": "error", "message": f"Erro inicial: {response.status_code}"}
            
            if total_pages == 0:
                return {"status": "error", "message": "Nenhuma página encontrada"}
            
            # Estratégia: Buscar das últimas 15 páginas
            pages_to_check = min(15, total_pages)
            print(f"[FIXED] Verificando últimas {pages_to_check} páginas...")
            
            for i in range(pages_to_check):
                page_num = total_pages - i
                
                if page_num <= 0:
                    break
                
                print(f"[FIXED] Página {page_num}/{total_pages}")
                
                # Delay entre páginas
                if i > 0:
                    time.sleep(8)  # 8 segundos entre páginas
                
                try:
                    response = requests.get(
                        f"{self.base_url}/leads",
                        headers=self.headers,
                        params={
                            "registros_por_pagina": 500,
                            "pagina": page_num
                        },
                        timeout=45
                    )
                    
                    if response.status_code == 200:
                        page_data = response.json()
                        page_leads = page_data.get('dados', [])
                        
                        print(f"[FIXED] Página {page_num}: {len(page_leads)} leads")
                        
                        # Filtra apenas leads de 2025 (setembro específico)
                        september_leads = []
                        for lead in page_leads:
                            data_cad = lead.get('data_cad', '')
                            if '2025-09' in data_cad:  # Setembro/2025
                                september_leads.append(lead)
                        
                        if september_leads:
                            leads_2025.extend(september_leads)
                            print(f"[FIXED] 🎉 Encontrou {len(september_leads)} leads de setembro/2025!")
                        
                        # Se já tem dados suficientes, para
                        if len(leads_2025) >= 1000:  # Limite razoável
                            print("[FIXED] Coletou leads suficientes")
                            break
                            
                    elif response.status_code == 429:
                        print(f"[FIXED] Rate limit na página {page_num}, aguardando...")
                        time.sleep(60)
                        continue
                    else:
                        print(f"[FIXED] Erro na página {page_num}: {response.status_code}")
                        
                except Exception as e:
                    print(f"[FIXED] Erro na página {page_num}: {str(e)}")
                    continue
            
            # Resultados
            if leads_2025:
                print(f"[FIXED] ✅ SUCESSO! {len(leads_2025)} leads de setembro/2025")
                
                # Ordena por data
                leads_2025.sort(key=lambda x: x.get('data_cad', ''), reverse=True)
                
                return {
                    "status": "success",
                    "leads": leads_2025,
                    "total_coletados": len(leads_2025),
                    "periodo": "setembro_2025",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print("[FIXED] ⚠️ Nenhum lead de setembro/2025 encontrado")
                return {
                    "status": "warning", 
                    "message": "Nenhum lead de setembro/2025 encontrado nas últimas páginas"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Erro geral: {str(e)}"}

def create_connector_fixed():
    """Factory para conector fixed"""
    return CVDWConnectorFixed()