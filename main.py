"""
Agente BI - Chat IA Principal
Interface conversacional para análise de dados CVDW
"""
import streamlit as st
from datetime import datetime
from config import Config
from cvdw.agent import create_agent

# Configuração da página
st.set_page_config(
    page_title="Agente BI - CVDW",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS minimalista
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.8rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    .user-message {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left: 4px solid #2196F3;
        color: #000000 !important;
    }
    .agent-message {
        background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 100%);
        border-left: 4px solid #4CAF50;
        color: #000000 !important;
    }
    .stChatMessage {
        color: #000000 !important;
    }
    .stChatMessage p {
        color: #000000 !important;
    }
    .stChatMessage div {
        color: #000000 !important;
    }
    .stChatMessage span {
        color: #000000 !important;
    }
    /* Forçar texto preto em todas as mensagens do chat */
    div[data-testid="chat-message"] {
        color: #000000 !important;
    }
    div[data-testid="chat-message"] * {
        color: #000000 !important;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def init_agent():
    """Inicializa agente CVDW"""
    
    if 'agent' not in st.session_state:
        with st.spinner('Inicializando Agente CVDW...'):
            try:
                # Valida configurações
                validation = Config.validate()
                if not validation["valid"]:
                    st.error("Erro nas configurações:")
                    for error in validation["errors"]:
                        st.error(f"• {error}")
                    st.stop()
                
                # Cria agente
                st.session_state.agent = create_agent()
                
                # Verifica status
                status = st.session_state.agent.get_system_status()
                st.session_state.system_online = status.get('online', False)
                st.session_state.total_leads = status.get('total_leads_available', 0)
                
                if st.session_state.system_online:
                    st.success(f"Conectado à API CVDW - {st.session_state.total_leads:,} leads disponíveis")
                else:
                    st.warning("Sistema offline - verifique credenciais")
                
            except Exception as e:
                st.error(f"Erro ao inicializar: {str(e)}")
                st.session_state.system_online = False

def display_message(role: str, content: str):
    """Exibe mensagem formatada"""
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 Você:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message agent-message">
            <strong>🤖 Agente IA:</strong><br>
            {content.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

def main():
    """Interface principal"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">🤖 Agente BI - CVDW</h1>', unsafe_allow_html=True)
    
    # Inicializa agente
    init_agent()
    
    # Sidebar de controle
    with st.sidebar:
        st.header("⚙️ Controles")
        
        # Status do sistema
        if st.session_state.get('system_online', False):
            st.markdown('<span class="status-online">🟢 Sistema Online</span>', unsafe_allow_html=True)
            total_leads = st.session_state.get('total_leads', 0)
            st.metric("Leads Disponíveis", f"{total_leads:,}")
        else:
            st.markdown('<span class="status-offline">🔴 Sistema Offline</span>', unsafe_allow_html=True)
            if st.button("🔄 Reconectar"):
                if 'agent' in st.session_state:
                    with st.spinner("Testando reconexão..."):
                        result = st.session_state.agent.reconnect()

                    if "Reconectado" in result:
                        st.success(result)
                        st.balloons()  # Comemoração quando reconectar
                    else:
                        st.warning(result)

                    st.rerun()
        
        st.divider()
        
        # Exemplos de consultas
        st.subheader("💬 Exemplos")
        
        example_queries = [
            "Quantos leads, reservas e vendas tivemos no mês anterior?",
            "Performance do mês anterior por origem",
            "Qual o SDR com maior quantidade de leads no mês anterior?",
            "Taxa de conversão do mês anterior fechado",
            "Análise do mês anterior de vendas e reservas"
        ]
        
        for query in example_queries:
            if st.button(f"📝 {query}", key=f"example_{hash(query)}", use_container_width=True):
                st.session_state.user_input = query
                st.rerun()
        
        st.divider()
        
        # Informações técnicas
        st.caption("**Sistema:** Agente BI v5.0")
        st.caption("**API:** CVDW BP Incorporadora") 
        st.caption("**Dados:** Tempo real")
    
    # Área principal de chat
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Inicializa histórico
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

            # Mensagem de boas-vindas
            welcome_msg = """Olá! Sou seu Assistente IA conectado à API CVDW.

Vou começar mostrando os dados do mês anterior fechado (análise mais precisa):"""

            st.session_state.chat_history.append(("agent", welcome_msg))

            # Marca que precisa carregar dados iniciais
            st.session_state.need_initial_data = True

        # Carrega dados iniciais se necessário e agente estiver pronto
        if (st.session_state.get('need_initial_data', False) and
            'agent' in st.session_state and
            st.session_state.get('system_online', False)):

            with st.spinner("Carregando dados do mês anterior fechado..."):
                auto_response = st.session_state.agent.process_query("Quantos leads, reservas e vendas tivemos no mês anterior?")

            st.session_state.chat_history.append(("agent", auto_response))
            st.session_state.need_initial_data = False
        
        # Exibe histórico
        for role, message in st.session_state.chat_history:
            display_message(role, message)
        
        # Input do usuário
        user_query = st.text_input(
            "💬 Faça sua pergunta:",
            value=st.session_state.get('user_input', ''),
            key="query_input",
            placeholder="Ex: Quantos leads temos este mês?"
        )
        
        # Limpa input após usar exemplo
        if 'user_input' in st.session_state:
            del st.session_state.user_input
        
        # Processa consulta
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            if st.button("🚀 Enviar", use_container_width=True) and user_query:
                # Adiciona pergunta do usuário
                st.session_state.chat_history.append(("user", user_query))
                
                # Processa com agente
                if 'agent' in st.session_state:
                    with st.spinner("Analisando dados..."):
                        response = st.session_state.agent.process_query(user_query)
                    
                    # Adiciona resposta
                    st.session_state.chat_history.append(("agent", response))
                else:
                    error_response = "Agente não está disponível. Tente reconectar."
                    st.session_state.chat_history.append(("agent", error_response))
                
                st.rerun()
        
        with col_clear:
            if st.button("🧹 Limpar Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        # Informações do sistema
        st.subheader("📊 Status")
        
        if st.session_state.get('system_online', False):
            st.success("API Conectada")
            
            # Métricas
            total = st.session_state.get('total_leads', 0)
            st.metric("Base Total", f"{total:,}")
            
            # Timestamp
            now = datetime.now().strftime("%H:%M:%S")
            st.caption(f"Atualizado às {now}")
        else:
            st.error("API Offline")
            st.caption("Verifique .env e credenciais")
        
        # Configurações
        with st.expander("🔧 Configurações"):
            config_summary = Config.get_summary()
            
            st.write("**API Status:**", "✅ Habilitada" if config_summary["api_enabled"] else "❌ Desabilitada")
            st.write("**Debug:**", "Sim" if config_summary["debug_mode"] else "Não")
            st.write("**Cache:**", f"{config_summary['cache_timeout']}s")
            st.write("**Máx. Leads:**", config_summary['max_leads'])

if __name__ == "__main__":
    main()