"""
Dashboard BI - Interface executiva para análise de dados CVDW
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from config import Config
from cvdw.connector import create_connector
from cvdw.analyzer import create_analyzer

# Configuração da página
st.set_page_config(
    page_title="Dashboard BI - CVDW",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para dashboard
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2196F3;
    }
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .status-online {
        background: #d4edda;
        color: #155724;
    }
    .status-offline {
        background: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

def init_connector():
    """Inicializa conector CVDW"""
    
    if 'connector' not in st.session_state:
        try:
            validation = Config.validate()
            if not validation["valid"]:
                st.error("Configuração inválida:")
                for error in validation["errors"]:
                    st.error(f"• {error}")
                return False
            
            st.session_state.connector = create_connector()
            return True
            
        except Exception as e:
            st.error(f"Erro ao inicializar conector: {str(e)}")
            return False
    
    return True

def load_data(limit: int = 500):
    """Carrega dados da API CVDW"""
    
    if not st.session_state.get('connector'):
        st.error("Conector não disponível")
        return None
    
    try:
        with st.spinner(f"Carregando {limit} leads..."):
            # Testa conexão primeiro
            test_result = st.session_state.connector.test_connection()
            
            if test_result["status"] != "success":
                st.error(f"Erro na conexão: {test_result['message']}")
                return None
            
            # Busca dados
            leads_result = st.session_state.connector.get_leads(limit=limit)
            
            if leads_result["status"] == "success":
                return leads_result
            else:
                st.error(f"Erro ao carregar dados: {leads_result['message']}")
                return None
                
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None

def create_charts(leads_data):
    """Cria visualizações dos dados"""
    
    leads = leads_data["leads"]
    df = pd.DataFrame(leads)
    
    # Preparação dos dados
    charts = {}
    
    # 1. Distribuição por situação
    if 'situacao' in df.columns:
        situacoes = df['situacao'].value_counts()
        
        fig_situacao = px.bar(
            x=situacoes.index,
            y=situacoes.values,
            title="Distribuição por Situação",
            labels={'x': 'Situação', 'y': 'Quantidade'},
            color=situacoes.values,
            color_continuous_scale='Blues'
        )
        fig_situacao.update_layout(showlegend=False, height=400)
        charts['situacao'] = fig_situacao
    
    # 2. Leads por origem
    origem_col = 'origem_nome' if 'origem_nome' in df.columns else 'origem'
    if origem_col in df.columns:
        origens = df[origem_col].value_counts().head(10)
        
        fig_origem = px.pie(
            values=origens.values,
            names=origens.index,
            title="Top 10 Origens de Leads"
        )
        fig_origem.update_layout(height=400)
        charts['origem'] = fig_origem
    
    # 3. Timeline de cadastros (se houver data)
    if 'data_cad' in df.columns:
        try:
            df['data_cad'] = pd.to_datetime(df['data_cad'])
            df['data_apenas'] = df['data_cad'].dt.date
            
            timeline = df.groupby('data_apenas').size().sort_index()
            timeline_recent = timeline.tail(30)  # Últimos 30 dias com dados
            
            fig_timeline = px.line(
                x=timeline_recent.index,
                y=timeline_recent.values,
                title="Leads Cadastrados - Últimos 30 Períodos",
                labels={'x': 'Data', 'y': 'Leads Cadastrados'}
            )
            fig_timeline.update_layout(height=400)
            charts['timeline'] = fig_timeline
            
        except Exception as e:
            st.warning(f"Não foi possível processar timeline: {str(e)}")
    
    # 4. Top responsáveis (se houver)
    responsavel_cols = ['corretor', 'responsavel', 'gestor', 'vendedor']
    responsavel_col = None
    
    for col in responsavel_cols:
        if col in df.columns and df[col].notna().any():
            responsavel_col = col
            break
    
    if responsavel_col:
        responsaveis = df[responsavel_col].value_counts().head(10)
        responsaveis = responsaveis[responsaveis.index != '']  # Remove vazios
        
        if len(responsaveis) > 0:
            fig_responsavel = px.bar(
                x=responsaveis.values,
                y=responsaveis.index,
                orientation='h',
                title=f"Top Responsáveis ({responsavel_col.title()})",
                labels={'x': 'Quantidade de Leads', 'y': 'Responsável'}
            )
            fig_responsavel.update_layout(height=400)
            charts['responsavel'] = fig_responsavel
    
    return charts

def main():
    """Interface principal do dashboard"""
    
    # Cabeçalho
    st.title("📊 Dashboard BI - CVDW")
    st.markdown("**Dashboard executivo para análise de dados BP Incorporadora**")
    st.divider()
    
    # Inicializa conector
    if not init_connector():
        st.stop()
    
    # Sidebar de controles
    with st.sidebar:
        st.header("⚙️ Controles")
        
        # Controle de dados
        st.subheader("📥 Carregamento de Dados")
        
        data_limit = st.selectbox(
            "Quantidade de leads:",
            [100, 250, 500, 1000, 2000],
            index=2  # 500 por padrão
        )
        
        load_button = st.button("🔄 Carregar Dados", use_container_width=True)
        
        if load_button:
            leads_data = load_data(limit=data_limit)
            if leads_data:
                st.session_state.dashboard_data = leads_data
                st.session_state.data_loaded = True
                st.success(f"✅ {leads_data['total_coletados']} leads carregados")
                st.rerun()
        
        # Status dos dados
        st.divider()
        st.subheader("📊 Status")
        
        if st.session_state.get('data_loaded', False):
            data = st.session_state.get('dashboard_data', {})
            st.markdown('<div class="status-badge status-online">Dados Carregados</div>', unsafe_allow_html=True)
            st.metric("Leads Analisados", data.get('total_coletados', 0))
            st.metric("Total na Base", data.get('metadata', {}).get('total_disponivel', 0))
        else:
            st.markdown('<div class="status-badge status-offline">Sem Dados</div>', unsafe_allow_html=True)
            st.info("👆 Clique em 'Carregar Dados' para começar")
        
        # Configurações
        with st.expander("🔧 Configurações"):
            config = Config.get_summary()
            st.json(config)
    
    # Área principal
    if st.session_state.get('data_loaded', False):
        leads_data = st.session_state.get('dashboard_data', {})
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        leads = leads_data["leads"]
        total_analisados = leads_data["total_coletados"]
        total_base = leads_data["metadata"]["total_disponivel"]
        
        # Calcula métricas
        vendas = sum(1 for lead in leads if lead.get('situacao') == 'VENDA REALIZADA')
        reservas = sum(1 for lead in leads if lead.get('situacao') == 'RESERVA')
        atendimento = sum(1 for lead in leads if 'ATENDIMENTO' in lead.get('situacao', ''))
        
        with col1:
            st.metric("📊 Analisados", f"{total_analisados:,}")
        
        with col2:
            st.metric("💰 Vendas", vendas, delta=f"{vendas/total_analisados*100:.1f}%")
        
        with col3:
            st.metric("📝 Reservas", reservas, delta=f"{reservas/total_analisados*100:.1f}%")
        
        with col4:
            st.metric("🎯 Em Atendimento", atendimento, delta=f"{atendimento/total_analisados*100:.1f}%")
        
        st.divider()
        
        # Análise avançada com contexto empresarial
        st.divider()
        st.subheader("🔍 Análise Empresarial Avançada")
        
        with st.spinner("Gerando insights empresariais..."):
            analyzer = create_analyzer()
            analysis = analyzer.analyze_comprehensive(leads)
        
        # Insights de negócio
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💡 Insights de Negócio**")
            insights = analysis.get("insights", [])
            for i, insight in enumerate(insights[:5], 1):
                st.write(f"{i}. {insight}")
        
        with col2:
            st.markdown("**🎯 Recomendações Acionáveis**")
            recommendations = analysis.get("recommendations", [])
            for i, rec in enumerate(recommendations[:5], 1):
                st.write(f"{i}. {rec}")
        
        # Performance detalhada
        if "performance" in analysis and analysis["performance"]:
            st.markdown("**👥 Performance por Responsável**")
            perf_data = list(analysis["performance"].values())[0]  # Pega primeiro campo válido
            
            if "top_performers" in perf_data:
                perf_df = pd.DataFrame(perf_data["top_performers"])
                
                fig_perf = px.bar(
                    perf_df, 
                    x="conversion_rate", 
                    y="name",
                    orientation='h',
                    title=f"Taxa de Conversão por {perf_data['field_name'].title()}",
                    labels={'conversion_rate': 'Taxa de Conversão (%)', 'name': 'Responsável'},
                    text="conversion_rate"
                )
                fig_perf.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_perf.update_layout(height=400)
                st.plotly_chart(fig_perf, use_container_width=True)
        
        # Health Score
        if "overview" in analysis:
            overview = analysis["overview"]
            health_score = overview.get("health_score", "N/A")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Health Score", health_score)
            with col2:
                if "conversions" in overview:
                    st.metric("Taxa Conversão", f"{overview['conversions']['rate']:.1f}%")
            with col3:
                if "hot_leads" in overview:
                    st.metric("Pipeline Ativo", f"{overview['hot_leads']['rate']:.1f}%")
        
        st.divider()
        
        # Gráficos
        charts = create_charts(leads_data)
        
        # Layout dos gráficos
        if charts:
            # Primeira linha
            col1, col2 = st.columns(2)
            
            with col1:
                if 'situacao' in charts:
                    st.plotly_chart(charts['situacao'], use_container_width=True)
            
            with col2:
                if 'origem' in charts:
                    st.plotly_chart(charts['origem'], use_container_width=True)
            
            # Segunda linha
            col1, col2 = st.columns(2)
            
            with col1:
                if 'timeline' in charts:
                    st.plotly_chart(charts['timeline'], use_container_width=True)
            
            with col2:
                if 'responsavel' in charts:
                    st.plotly_chart(charts['responsavel'], use_container_width=True)
        
        # Tabela de dados
        st.divider()
        st.subheader("📋 Dados Detalhados")
        
        if leads:
            df = pd.DataFrame(leads)
            
            # Seleciona colunas relevantes para exibição
            display_cols = []
            available_cols = df.columns.tolist()
            
            priority_cols = ['nome', 'situacao', 'origem_nome', 'data_cad', 'email', 'telefone']
            for col in priority_cols:
                if col in available_cols:
                    display_cols.append(col)
            
            # Adiciona outras colunas importantes
            other_important = ['corretor', 'responsavel', 'gestor', 'vendedor']
            for col in other_important:
                if col in available_cols and col not in display_cols:
                    display_cols.append(col)
            
            if display_cols:
                # Mostra apenas primeiros 20 registros para performance
                st.dataframe(df[display_cols].head(20), use_container_width=True)
                st.caption(f"Mostrando 20 de {len(df)} leads carregados")
            else:
                st.dataframe(df.head(20), use_container_width=True)
    
    else:
        # Interface inicial
        st.info("👋 Bem-vindo ao Dashboard BI!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 Funcionalidades
            - Conexão direta com API CVDW
            - Visualizações interativas
            - Métricas em tempo real
            - Análise por origem e situação
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Dados Disponíveis  
            - 68.988+ leads em tempo real
            - Distribuição por situação
            - Performance por origem
            - Timeline de cadastros
            """)
        
        with col3:
            st.markdown("""
            ### 🚀 Como Usar
            1. Clique em 'Carregar Dados' na sidebar
            2. Escolha a quantidade de leads
            3. Visualize métricas e gráficos
            4. Analise dados detalhados
            """)
    
    # Footer
    st.divider()
    timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    st.caption(f"💡 Dashboard atualizado em {timestamp} | Sistema: Agente BI v5.0 | API: CVDW BP Incorporadora")

if __name__ == "__main__":
    main()