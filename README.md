# 🤖 Agente PowerBI - Sistema CVDW

**Sistema de análise inteligente de dados integrado com API CVDW da BP Incorporadora**

## 🎯 Visão Geral

Sistema IA que conecta diretamente com a API CVDW para análise em tempo real de **68.988+ leads**, oferecendo:
- 💬 **Chat IA**: Interface conversacional para consultas em linguagem natural
- 📊 **Dashboard**: Visualizações executivas com métricas e gráficos interativos
- 🔄 **Tempo Real**: Dados sempre atualizados da API oficial

## 📁 Estrutura do Projeto

```
agente-powerbi/
├── .env                    # Credenciais API (não versionado)
├── requirements.txt        # Dependências mínimas (6 libs)
├── config.py              # Configurações centralizadas
├── main.py                # 💬 Aplicação Chat IA
├── dashboard.py           # 📊 Dashboard Executivo
├── CLAUDE.md              # Contexto completo para IA
├── README.md              # Esta documentação
├── cvdw/                  # Módulo CVDW
│   ├── __init__.py        
│   ├── connector.py       # Conector API limpo
│   ├── agent.py           # Agente IA otimizado
│   └── analyzer.py        # Analisador avançado
├── utils/                 # Utilitários
│   ├── __init__.py
│   └── helpers.py
├── tests/                 # Testes básicos
│   └── test_cvdw.py
└── venv/                  # Ambiente virtual
```

## 🚀 Instalação e Uso

### 1. Pré-requisitos
- Python 3.8+
- Credenciais válidas da API CVDW

### 2. Instalação
```bash
# Clone/baixe o projeto
cd agente-powerbi

# Instale dependências mínimas
pip install -r requirements.txt
```

### 3. Configuração
Copie o arquivo `.env.example` para `.env` e configure suas credenciais:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais da API CVDW
```

Configure no arquivo `.env`:
```env
CVCRM_EMAIL=seu-email@empresa.com.br
CVCRM_TOKEN=seu-token-da-api-cvdw
USE_CVCRM_API=true
```

### 4. Execução

#### 💬 Chat IA (Principal)
```bash
streamlit run main.py
```
- **URL**: http://localhost:8501
- **Funcionalidades**: Consultas em linguagem natural, análise de leads, insights automáticos

#### 📊 Dashboard Executivo  
```bash
streamlit run dashboard.py --server.port 8502
```
- **URL**: http://localhost:8502
- **Funcionalidades**: Métricas visuais, gráficos interativos, tabelas de dados

## 💡 Exemplos de Uso

### Chat IA - Consultas Suportadas:
```
"Quantos leads temos no total?"
"Qual o SDR com maior quantidade de leads?"  
"Performance por situação"
"Análise de leads por origem"
"Leads cadastrados este mês"
```

### Dashboard - Visualizações:
- 📊 Distribuição por situação (vendas, reservas, atendimento)
- 🎯 Top origens de leads (Facebook, WhatsApp, etc.)
- 📈 Timeline de cadastros
- 👥 Performance por responsável/SDR
- 🔍 **Análise Empresarial Avançada** (NOVO)
- 💡 **Insights de Negócio Automatizados** (NOVO)
- 🎯 **Recomendações Acionáveis** (NOVO)

## 🔧 Funcionalidades Técnicas

### Conector CVDW (`cvdw/connector.py`)
- ✅ Conexão validada com método Power BI
- ✅ Headers corretos: `email` + `token`
- ✅ Paginação automática (500 leads/página)
- ✅ Cache inteligente (5 minutos)
- ✅ Rate limiting com retry automático
- ✅ Tratamento robusto de erros

### Agente IA (`cvdw/agent.py`)  
- ✅ Classificação inteligente de consultas
- ✅ Análise automática de dados
- ✅ Respostas categorizadas: [QUANTITATIVO], [PERFORMANCE], [STATUS]
- ✅ Sugestões contextuais
- ✅ Fallback para modo offline

### Configurações (`config.py`)
- ✅ Validação automática de credenciais
- ✅ URLs e endpoints centralizados
- ✅ Parâmetros de cache e performance
- ✅ Configurações de timeout e rate limiting

## 🧪 Testes

```bash
# Executa todos os testes
python tests/test_cvdw.py
```

**Testes inclusos:**
- ✅ Validação de configurações
- ✅ Conectividade com API CVDW
- ✅ Funcionamento do agente IA
- ✅ Utilitários e helpers

## 📊 Dados Acessíveis

### API CVDW - Estrutura Real:
```json
{
  "total_de_registros": 68988,
  "dados": [
    {
      "idlead": 12345,
      "nome": "ALLINE PEREIRA DA COSTA",
      "situacao": "VENDA REALIZADA", 
      "origem_nome": "ChatBot",
      "data_cad": "2021-06-21 20:08:34",
      "email": "email@exemplo.com",
      "telefone": "(11) 99999-9999"
      // ... mais 70+ campos por lead
    }
  ]
}
```

### Métricas Disponíveis:
- **68.988 leads** na base total
- **138 páginas** de dados paginados  
- **75+ campos** por lead
- **Dados em tempo real** via API

## ⚙️ Configurações Avançadas

### Cache e Performance:
```python
DEFAULT_CACHE_TIMEOUT = 300      # 5 minutos
DEFAULT_PAGE_SIZE = 500          # Leads por página
MAX_LEADS_PER_REQUEST = 2000     # Máximo por consulta
RATE_LIMIT_DELAY = 2             # Delay entre requests
```

### Personalização:
- **Portas**: Modifique `STREAMLIT_PORT` e `DASHBOARD_PORT` no `.env`
- **Debug**: Ative com `DEBUG=true` para logs detalhados
- **Cache**: Ajuste `DEFAULT_CACHE_TIMEOUT` para cache mais/menos agressivo

## 🛠️ Troubleshooting

### Problemas Comuns:

**1. "Sistema Offline"**
```bash
python tests/test_cvdw.py  # Testa conectividade
```

**2. "Credenciais Inválidas"**
- Verifique arquivo `.env` 
- Confirme `CVCRM_EMAIL` e `CVCRM_TOKEN`

**3. "Rate Limiting"**
- Sistema aguarda automaticamente
- Reduzir `MAX_LEADS_PER_REQUEST` se necessário

**4. "Erro de Importação"**
```bash
pip install -r requirements_clean.txt
```

## 📈 Performance

### Benchmarks:
- **Conexão inicial**: < 3 segundos
- **Consulta típica**: < 5 segundos  
- **Dashboard carregamento**: < 10 segundos
- **Cache hit**: Instantâneo

### Otimizações:
- ✅ Apenas 6 dependências essenciais
- ✅ Cache inteligente por tipo de consulta
- ✅ Paginação otimizada da API
- ✅ Rate limiting preditivo

## 🎯 Roadmap

### Implementado ✅:
- [x] Conexão estável com API CVDW
- [x] Chat IA funcional com 68.988 leads
- [x] Dashboard com visualizações
- [x] Estrutura limpa e organizda
- [x] Testes automatizados
- [x] Documentação completa

### Próximas Funcionalidades:
- [ ] Filtros temporais avançados
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Alertas automáticos por email
- [ ] API REST para integração

## 📞 Suporte

- **Sistema**: Agente PowerBI v4.0
- **API**: CVDW BP Incorporadora  
- **Status**: Totalmente funcional com dados reais
- **Dados**: 68.988+ leads em tempo real

---

**🎉 Sistema pronto para produção!**  
Estrutura limpa, performance otimizada e totalmente funcional.