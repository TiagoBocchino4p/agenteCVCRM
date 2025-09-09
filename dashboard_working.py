"""
BP DASHBOARD - Working Version
Dashboard simplificado que funciona
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="BP DASHBOARD - Working",
    page_icon="📊",
    layout="wide"
)

# CSS simples
st.markdown("""
<style>
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f2937;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def test_api_connection():
    """Teste rápido da API"""
    try:
        email = os.getenv('CVCRM_EMAIL')
        token = os.getenv('CVCRM_TOKEN')
        
        if not email or not token:
            return {"status": "error", "message": "Credenciais não encontradas"}
        
        url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads"
        headers = {"email": email, "token": token}
        params = {"registros_por_pagina": 10}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "total_leads": data.get('total_de_registros', 0),
                "total_pages": data.get('total_de_paginas', 0)
            }
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_recent_leads_sample():
    """Pega uma amostra das últimas páginas"""
    try:
        email = os.getenv('CVCRM_EMAIL')
        token = os.getenv('CVCRM_TOKEN')
        
        url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads"
        headers = {"email": email, "token": token}
        
        # Descobre total de páginas
        response = requests.get(url, headers=headers, params={"registros_por_pagina": 10}, timeout=10)
        
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
        
        total_pages = response.json().get('total_de_paginas', 0)
        
        # Pega última página
        last_page_response = requests.get(
            url, 
            headers=headers, 
            params={"registros_por_pagina": 100, "pagina": total_pages}, 
            timeout=15
        )
        
        if last_page_response.status_code == 200:
            data = last_page_response.json()
            leads = data.get('dados', [])
            
            # Filtra setembro 2025
            september_leads = [lead for lead in leads if '2025-09' in lead.get('data_cad', '')]
            
            return {
                "status": "success" if september_leads else "warning",
                "leads": september_leads,
                "total_in_page": len(leads),
                "september_count": len(september_leads)
            }
        
        return {"status": "error", "message": f"Erro na última página: {last_page_response.status_code}"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    st.title("BP DASHBOARD - Working Version")
    
    # Status da API
    with st.spinner("Testando conexão API..."):
        api_status = test_api_connection()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_status["status"] == "success":
            st.success("✅ API Online")
            st.metric("Total Leads Disponíveis", f"{api_status['total_leads']:,}")
        else:
            st.error("❌ API Offline")
            st.error(api_status["message"])
    
    with col2:
        if api_status["status"] == "success":
            st.metric("Total Páginas", api_status['total_pages'])
        else:
            st.metric("Páginas", "N/A")
    
    with col3:
        st.metric("Status", "Online" if api_status["status"] == "success" else "Erro")
    
    # Teste de dados recentes
    if api_status["status"] == "success":
        st.markdown("---")
        st.subheader("📊 Teste de Dados Recentes")
        
        with st.spinner("Buscando dados da última página..."):
            recent_data = get_recent_leads_sample()
        
        if recent_data["status"] == "success":
            st.success(f"✅ Encontrados {recent_data['september_count']} leads de setembro/2025 na última página")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Leads na Página", recent_data['total_in_page'])
            with col2:
                st.metric("Leads Setembro/2025", recent_data['september_count'])
            with col3:
                if recent_data['september_count'] > 0:
                    st.metric("Status Dados", "✅ Encontrado")
                else:
                    st.metric("Status Dados", "⚠️ Não encontrado")
            
            # Mostra alguns exemplos
            if recent_data['leads']:
                st.subheader("📋 Exemplos de Leads Setembro/2025")
                df_sample = pd.DataFrame(recent_data['leads'][:5])
                if not df_sample.empty:
                    st.dataframe(df_sample[['nome', 'data_cad', 'situacao', 'origem_nome']], use_container_width=True)
        
        elif recent_data["status"] == "warning":
            st.warning(f"⚠️ Página acessada com {recent_data['total_in_page']} leads, mas nenhum de setembro/2025")
            
        else:
            st.error(f"❌ Erro ao buscar dados: {recent_data['message']}")
    
    # Info
    st.markdown("---")
    st.info("**Dashboard Working** - Versão simplificada para testes e validação da API")
    st.write(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    main()