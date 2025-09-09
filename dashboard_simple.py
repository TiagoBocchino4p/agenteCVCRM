"""
BP DASHBOARD - Simple
Dashboard mínimo que funciona sempre
"""
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="BP Dashboard Simple", layout="wide")

st.title("🚀 BP DASHBOARD - Simple")
st.write("Dashboard super simples para testar a API")

# Teste básico
st.subheader("🔧 Teste de Credenciais")

email = os.getenv('CVCRM_EMAIL')
token = os.getenv('CVCRM_TOKEN')

if email and token:
    st.success(f"✅ Email: {email[:10]}...")
    st.success(f"✅ Token: {token[:10]}...")
else:
    st.error("❌ Credenciais não encontradas no .env")
    st.stop()

# Teste de conexão
st.subheader("🌐 Teste de Conexão API")

try:
    with st.spinner("Testando conexão..."):
        url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads"
        headers = {"email": email, "token": token}
        params = {"registros_por_pagina": 5}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ API Online e Funcionando!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Leads", f"{data.get('total_de_registros', 0):,}")
            with col2:
                st.metric("Total Páginas", data.get('total_de_paginas', 0))
            with col3:
                st.metric("Por Página", len(data.get('dados', [])))
            
            # Mostra primeiros leads
            if data.get('dados'):
                st.subheader("📋 Primeiros Leads da API")
                for i, lead in enumerate(data['dados'][:3]):
                    st.write(f"**{i+1}.** {lead.get('nome', 'N/A')} - {lead.get('data_cad', 'N/A')} - {lead.get('situacao', 'N/A')}")
                    
        elif response.status_code == 429:
            st.warning("⚠️ **Rate Limit Ativo** (HTTP 429)")
            st.info("""
            **Status**: A API está online, mas temporariamente limitando requisições.
            
            **Significado**: Muitas chamadas foram feitas recentemente. Isso é normal e esperado.
            
            **Solução**: Aguarde alguns minutos e recarregue a página.
            """)
            
            # Botão para recarregar
            if st.button("🔄 Tentar Novamente"):
                st.rerun()
                
        else:
            st.error(f"❌ Erro HTTP: {response.status_code}")
            st.write("Status da resposta:", response.text[:200] if hasattr(response, 'text') else "N/A")
            
except Exception as e:
    st.error(f"❌ Erro de Conexão: {str(e)}")
    st.write("**Possíveis causas**: Problema de rede, firewall ou credenciais incorretas.")

# Info
st.markdown("---")
st.info("✅ Dashboard Simple funcionando!")
st.write(f"Atualizado: {datetime.now().strftime('%H:%M:%S')}")