"""
BP DASHBOARD - Fast Version
Dashboard otimizado com leads mais recentes
"""
import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="BP Dashboard Fast", layout="wide")

st.title("🚀 BP DASHBOARD - Fast & Recent")
st.write("Dashboard otimizado mostrando leads mais RECENTES")

# Credenciais
email = os.getenv('CVCRM_EMAIL')
token = os.getenv('CVCRM_TOKEN')

if not email or not token:
    st.error("❌ Credenciais não encontradas no .env")
    st.stop()

# Cache da função de busca
@st.cache_data(ttl=300)  # Cache por 5 minutos
def fetch_recent_leads(limit=500, focus_previous_month=True):
    """Busca leads filtrados por mês anterior fechado como padrão"""

    url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads"
    headers = {"email": email, "token": token}

    # Busca primeira página para ver total
    params = {"registros_por_pagina": limit, "pagina": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            leads = data.get('dados', [])
            
            # Define período baseado no foco
            current_date = pd.Timestamp.now()

            if focus_previous_month:
                # Mês anterior fechado (mais preciso para análise)
                if current_date.month == 1:
                    # Janeiro -> pega dezembro do ano anterior
                    start_date = pd.Timestamp(current_date.year - 1, 12, 1)
                    end_date = pd.Timestamp(current_date.year, 1, 1) - pd.Timedelta(days=1)
                else:
                    # Outros meses -> pega mês anterior
                    start_date = pd.Timestamp(current_date.year, current_date.month - 1, 1)
                    if current_date.month == 12:
                        end_date = pd.Timestamp(current_date.year + 1, 1, 1) - pd.Timedelta(days=1)
                    else:
                        end_date = pd.Timestamp(current_date.year, current_date.month, 1) - pd.Timedelta(days=1)
                period_label = f"{start_date.strftime('%B %Y')} (Mês Anterior Fechado)"
            else:
                # Últimos 30 dias
                cutoff_date = current_date - pd.Timedelta(days=30)
                start_date = cutoff_date
                end_date = current_date
                period_label = "Últimos 30 dias"

            leads_filtered = []

            for lead in leads:
                try:
                    # Limpa e converte data
                    data_str = lead.get('data_cad', '')
                    if data_str:
                        # Remove possível timestamp
                        if ' ' in data_str:
                            data_str = data_str.split(' ')[0]
                        lead['data_cad_dt'] = pd.to_datetime(data_str, errors='coerce')

                        # Filtra por período definido
                        if pd.notna(lead['data_cad_dt']) and start_date <= lead['data_cad_dt'] <= end_date:
                            leads_filtered.append(lead)
                    else:
                        lead['data_cad_dt'] = pd.NaT
                        leads_filtered.append(lead)  # Inclui leads sem data por segurança
                except:
                    lead['data_cad_dt'] = pd.NaT
                    leads_filtered.append(lead)

            # Ordena por data mais recente
            leads_sorted = sorted(leads_filtered, key=lambda x: x.get('data_cad_dt', pd.Timestamp.min), reverse=True)
            
            return {
                "status": "success",
                "leads": leads_sorted,
                "total": data.get('total_de_registros', 0),
                "total_pages": data.get('total_de_paginas', 0),
                "period_label": period_label
            }
        elif response.status_code == 429:
            return {"status": "rate_limit", "message": "Rate limit ativo"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Dados CVDW - Mês Anterior Fechado")

    # Toggle para escolher período
    focus_previous = st.checkbox("Focar no mês anterior fechado (recomendado)", value=True,
                                help="Mês anterior fechado oferece análise mais precisa que 'últimos 30 dias'")

    # Busca dados do mês anterior fechado
    period_text = "mês anterior fechado" if focus_previous else "últimos 30 dias"
    with st.spinner(f"Buscando leads do {period_text}..."):
        result = fetch_recent_leads(500, focus_previous_month=focus_previous)
    
    if result["status"] == "success":
        leads = result["leads"]
        total = result["total"]
        
        period_display = result.get('period_label', period_text)
        st.success(f"✅ {len(leads)} leads de {period_display} | Base total: {total:,}")
        
        # Métricas principais
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Total Base", f"{total:,}")
        
        with col_b:
            leads_periodo = len(leads)  # Já filtrados por período
            period_short = "Mês Anterior" if focus_previous else "30 Dias"
            st.metric(f"Leads {period_short}", leads_periodo)
        
        with col_c:
            vendas = len([l for l in leads if 'VENDA' in l.get('situacao', '').upper()])
            st.metric(f"Vendas {period_short}", vendas)

        with col_d:
            reservas = len([l for l in leads if 'RESERVA' in l.get('situacao', '').upper()])
            st.metric(f"Reservas {period_short}", reservas)
        
        # Lista dos leads mais recentes do período
        st.subheader(f"🔥 Leads Mais Recentes - {period_display}")
        
        for i, lead in enumerate(leads[:10], 1):
            nome = lead.get('nome', 'N/A')
            situacao = lead.get('situacao', 'N/A')
            origem = lead.get('origem_nome', 'N/A')
            data_cad = lead.get('data_cad', 'N/A')
            
            # Emoji baseado na situação
            emoji = "✅" if 'VENDA' in situacao.upper() else "🔄" if 'FOLLOW' in situacao.upper() else "📝"
            
            st.write(f"{emoji} **{i}.** {nome} | {situacao} | {origem} | {data_cad}")
        
        # Gráfico por situação (período selecionado)
        if leads:
            situacoes = {}
            for lead in leads:
                sit = lead.get('situacao', 'N/A')
                situacoes[sit] = situacoes.get(sit, 0) + 1

            if situacoes:
                st.subheader(f"📈 Situações - {period_display}")

                df_sit = pd.DataFrame(list(situacoes.items()), columns=['Situação', 'Quantidade'])
                fig = px.bar(df_sit, x='Situação', y='Quantidade',
                           color='Quantidade',
                           title=f"Distribuição por Situação - {period_display}")
                fig.update_layout(height=400, showlegend=False)
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

                # Gráfico por origem também
                st.subheader(f"📊 Origem dos Leads - {period_display}")
                origens = {}
                for lead in leads:
                    origem = lead.get('origem_nome', 'N/A')
                    origens[origem] = origens.get(origem, 0) + 1

                df_origem = pd.DataFrame(list(origens.items()), columns=['Origem', 'Quantidade'])
                fig2 = px.pie(df_origem, values='Quantidade', names='Origem',
                            title=f"Distribuição por Origem - {period_display}")
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
    
    elif result["status"] == "rate_limit":
        st.warning("⚠️ **Rate Limit Ativo** (HTTP 429)")
        st.info("A API está temporariamente limitando requisições. Aguarde alguns minutos.")
        
        if st.button("🔄 Tentar Novamente"):
            st.cache_data.clear()
            st.rerun()
    
    else:
        st.error(f"❌ Erro: {result['message']}")

with col2:
    st.subheader("⚙️ Controles")
    
    # Botão para atualizar dados
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    # Informações
    period_info = "mês anterior fechado" if focus_previous else "últimos 30 dias"
    st.info(f"""
    **🔥 Foco em {period_info}:**
    - Análise mais precisa para insights
    - Dados mais recentes primeiro
    - Métricas de conversão
    - Cache inteligente (5 min)
    """)
    
    st.subheader("📈 Performance")
    st.metric("Cache TTL", "5 min")
    st.metric("Limite Busca", "200 leads")
    st.metric("Ordenação", "Mais recentes")
    
    # Status
    st.subheader("🔍 Status")
    st.write(f"**Email**: {email[:15]}...")
    st.write(f"**Atualizado**: {datetime.now().strftime('%H:%M:%S')}")

st.markdown("---")
st.success("✅ Dashboard Fast - Focado no MÊS ANTERIOR FECHADO para análise mais precisa!")