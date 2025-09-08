"""
Configurações centralizadas - Agente PowerBI CVDW
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Carrega variáveis de ambiente
load_dotenv()

class Config:
    """Configurações centralizadas do sistema"""
    
    # API CVDW
    CVCRM_EMAIL = os.getenv('CVCRM_EMAIL')
    CVCRM_TOKEN = os.getenv('CVCRM_TOKEN')
    CVCRM_API_BASE_URL = os.getenv('CVCRM_API_BASE_URL', 'https://api.cvcrm.com.br')
    
    # URLs específicas (método Power BI)
    CVDW_BASE_URL = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw"
    CVDW_LEADS_ENDPOINT = f"{CVDW_BASE_URL}/leads"
    
    # Configurações de sistema
    USE_CVCRM_API = os.getenv('USE_CVCRM_API', 'true').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Configurações de cache e performance
    DEFAULT_CACHE_TIMEOUT = 300  # 5 minutos
    DEFAULT_PAGE_SIZE = 500
    MAX_LEADS_PER_REQUEST = 2000
    API_TIMEOUT = 30
    RATE_LIMIT_DELAY = 2  # segundos entre requests
    
    # Streamlit
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', '8501'))
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '8502'))
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Valida configurações essenciais"""
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validações obrigatórias
        if not cls.CVCRM_EMAIL:
            validation["valid"] = False
            validation["errors"].append("CVCRM_EMAIL não definido no .env")
        
        if not cls.CVCRM_TOKEN:
            validation["valid"] = False  
            validation["errors"].append("CVCRM_TOKEN não definido no .env")
        
        # Validações opcionais
        if not cls.USE_CVCRM_API:
            validation["warnings"].append("API CVCRM desabilitada - usando modo demo")
        
        return validation
    
    @classmethod
    def get_api_headers(cls) -> Dict[str, str]:
        """Retorna headers para API CVDW (método Power BI)"""
        
        return {
            "email": cls.CVCRM_EMAIL,
            "token": cls.CVCRM_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Retorna resumo das configurações"""
        
        return {
            "api_enabled": cls.USE_CVCRM_API,
            "debug_mode": cls.DEBUG,
            "cvdw_url": cls.CVDW_LEADS_ENDPOINT,
            "cache_timeout": cls.DEFAULT_CACHE_TIMEOUT,
            "max_leads": cls.MAX_LEADS_PER_REQUEST,
            "ports": {
                "main": cls.STREAMLIT_PORT,
                "dashboard": cls.DASHBOARD_PORT
            }
        }