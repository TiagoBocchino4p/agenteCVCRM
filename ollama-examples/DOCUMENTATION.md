# Agente Analytics - Documentação do Projeto

## 📋 Visão Geral

Assistente conversacional em Python que analisa dados de leads e corretores do CV CRM usando IA local (Llama3 via Ollama). Permite consultas em linguagem natural sobre performance de vendas imobiliárias.

## 🎯 Funcionalidades

- **Análise de leads por período** (este mês, mês passado, datas customizadas)
- **Performance por corretor** (ranking, contagem individual, resumos)
- **Conversação natural** em português
- **IA 100% local** (privacidade e sem custos de API)

## 🏗️ Arquitetura

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │ pergunta em português
       ▼
┌─────────────────────────────┐
│  agent.py                   │
│  ┌─────────────────────┐   │
│  │ Llama3 (Ollama)     │   │ ← IA Local
│  └──────────┬──────────┘   │
│             │ decide tool   │
│             ▼               │
│  ┌─────────────────────┐   │
│  │ analyze_leads_by    │   │ ← Ferramenta
│  │ _broker()           │   │
│  └──────────┬──────────┘   │
└─────────────┼──────────────┘
              │
              ▼
     ┌────────────────┐
     │ cv_crm_api.py  │ ← Cliente API
     └────────┬───────┘
              │ HTTP + paginação
              ▼
     ┌────────────────┐
     │   CV CRM API   │ ← Sistema externo
     │   (CVDW)       │
     └────────────────┘
```

## 📁 Estrutura de Arquivos

### **[agent.py](agent.py)** - Principal ⭐
Versão de produção usando Ollama/Llama3 local.

**Componentes principais:**
- `CVCrmAPI` (linhas 28-100): Classe de comunicação com API
- `get_date_range_from_query()` (102-123): Parser de datas relativas
- `analyze_leads_by_broker()` (127-167): Ferramenta de análise
- `run_agent()` (170-261): Loop conversacional com IA

**Tipos de análise suportados:**
- `count`: Contagem total de leads
- `summary_by_broker`: Resumo agrupado por corretor
- `count_by_broker`: Leads de um corretor específico

**Dependências:**
```bash
pip install litellm pandas python-dotenv python-dateutil requests
```

**Configuração (.env):**
```env
CV_SUBDOMAIN=bpincorporadora
CV_EMAIL=seu-email@dominio.com.br
CV_TOKEN=seu-token-aqui
```

### **[cv_crm_api.py](cv_crm_api.py)** - Cliente HTTP
Biblioteca para comunicação com CV CRM.

**Features:**
- Paginação automática (100 registros/página)
- Retry com backoff exponencial (2s → 4s → 8s → 16s → 32s)
- Tratamento de rate limiting (HTTP 429)
- Timeout de 30 segundos por request

**Métodos públicos:**
- `get_cvdw_lead_performance_by_broker(start_date, end_date)`: Busca leads do CVDW

**⚠️ Problema:** Credenciais hardcoded nas linhas 18-19 (deve usar parâmetros do construtor)

### **[agent_core.py](agent_core.py)** - Versão legada
Primeira implementação usando Gemini API (Google).

**Diferenças para agent.py:**
- Usa API cloud (Gemini) ao invés de Ollama local
- IA retorna apenas nome da ferramenta (sem tool calling formal)
- Menos flexível e robusto

**⚠️ Problemas:**
- **Credenciais expostas** nas linhas 10-13 (GEMINI_API_KEY, CV_TOKEN, etc)
- Endpoint diferente: `/cvdw/leads/corretores` vs `/cvdw/leads`

**Status:** Descontinuado, manter apenas para referência

## 🚀 Como Usar

### Pré-requisitos

1. **Instalar Ollama:**
```bash
# Windows: baixar de https://ollama.ai
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh
```

2. **Baixar modelo Llama3:**
```bash
ollama pull llama3
```

3. **Instalar dependências Python:**
```bash
pip install litellm pandas python-dotenv python-dateutil requests
```

4. **Configurar credenciais:**
Criar arquivo `.env` na raiz do projeto:
```env
CV_SUBDOMAIN=bpincorporadora
CV_EMAIL=tiago.bocchino@4pcapital.com.br
CV_TOKEN=3b10d578dcafe9a615f2471ea1e2f9da5580dc18
```

### Executar

```bash
# Certifique-se que Ollama está rodando em background
python agent.py
```

### Exemplos de uso

```
Você: Quantos leads tivemos este mês?
🤖 Agente: Foram encontrados 127 leads neste mês.

Você: Qual corretor teve mais leads no mês passado?
🤖 Agente: O corretor com mais leads em agosto foi João Silva, com 45 leads.

Você: Quantos leads a Maria teve?
🤖 Agente: A corretora Maria teve 32 leads no período analisado.
```

## 🔧 Detalhes Técnicos

### Fluxo de Execução

1. **Input do usuário** → `run_agent()` (linha 200)
2. **Primeira chamada à IA** → `litellm.completion()` (211-215)
   - Modelo analisa pergunta + tools disponíveis
   - Retorna `tool_calls` ou resposta direta
3. **Se tool_call presente:**
   - Parse dos argumentos JSON (linha 226)
   - Execução da função Python (linha 230)
   - Resultado adicionado ao histórico (233-238)
4. **Segunda chamada à IA** → `litellm.completion()` (242-245)
   - Modelo gera resposta em linguagem natural
   - Usa resultado da ferramenta como contexto
5. **Output para usuário** (linha 247)

### Parser de Datas

```python
get_date_range_from_query("quantos leads tivemos este mês?")
# → ("2025-09-01", "2025-09-30")

get_date_range_from_query("performance do mês passado")
# → ("2025-08-01", "2025-08-31")

get_date_range_from_query("leads de hoje")
# → ("2025-09-30", "2025-09-30")
```

### Estratégia de Retry (cv_crm_api.py)

Quando encontra HTTP 429 (rate limit):
```
Tentativa 1: Espera 2s  (2 × 2^0)
Tentativa 2: Espera 4s  (2 × 2^1)
Tentativa 3: Espera 8s  (2 × 2^2)
Tentativa 4: Espera 16s (2 × 2^3)
Tentativa 5: Espera 32s (2 × 2^4)
```

Máximo de 5 tentativas por página.

## 🔐 Segurança

### ✅ Boas práticas (agent.py)
- Credenciais em `.env` (não commitadas)
- Carregadas via `python-dotenv`
- Validação de presença (linha 21)

### ⚠️ Problemas existentes

**[cv_crm_api.py](cv_crm_api.py:18-19):**
```python
# ❌ NÃO FAZER:
'email': "tiago.bocchino@4pcapital.com.br",
'token': "3b10d578dcafe9a615f2471ea1e2f9da5580dc18"

# ✅ CORRETO:
'email': email,  # usar parâmetro do construtor
'token': token
```

**[agent_core.py](agent_core.py:10-13):**
```python
# ❌ Credenciais expostas - REMOVER ou mover para .env
GEMINI_API_KEY = "AIzaSyB9dApz67kUkvO-GO0c5Q_ERiqh0jTPxHQ"
CV_CRM_TOKEN = "3b10d578dcafe9a615f2471ea1e2f9da5580dc18"
```

## 📊 API CV CRM - Endpoints Usados

### `/api/v1/cvdw/leads`
Data Warehouse de leads.

**Parâmetros:**
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD
- `pagina`: número da página (começa em 1)
- `registros_por_pagina`: 100

**Resposta:**
```json
{
  "dados": [
    {
      "CorretorNome": "João Silva",
      "LeadID": 12345,
      "DataCriacao": "2025-09-15",
      ...
    }
  ]
}
```

**Rate Limits:**
- Não documentado oficialmente
- Implementado retry para HTTP 429
- Sleep de 0.5s entre páginas bem-sucedidas

## 🐛 Troubleshooting

### Erro: "Module 'litellm' not found"
```bash
pip install litellm
```

### Erro: "Connection refused" ao chamar modelo
Ollama não está rodando. Iniciar com:
```bash
ollama serve
```

### Erro: "Model 'llama3' not found"
```bash
ollama pull llama3
```

### Erro: "CV CRM credentials not found"
Criar arquivo `.env` conforme seção "Configurar credenciais".

### API retorna HTTP 429 repetidamente
- Aguardar alguns minutos
- Verificar se há outros processos fazendo requests
- Rate limit do CV CRM pode estar muito restritivo

## 🔄 Possíveis Melhorias

### Curto prazo
- [ ] Corrigir credenciais hardcoded em [cv_crm_api.py](cv_crm_api.py:18-19)
- [ ] Adicionar `.env.example` com template
- [ ] Adicionar logging estruturado (substituir `print()`)

### Médio prazo
- [ ] Suporte a mais análises (origem dos leads, taxa de conversão)
- [ ] Cache local de dados (evitar requests repetidas)
- [ ] Testes unitários para parser de datas
- [ ] Exportar relatórios em CSV/Excel

### Longo prazo
- [ ] Interface web (Streamlit/Gradio)
- [ ] Suporte a múltiplos CRMs
- [ ] Dashboards visuais (gráficos)
- [ ] Agendamento de relatórios automáticos

## 📝 Changelog

### Versão atual (agent.py)
- ✅ Migração de Gemini para Ollama (modelo local)
- ✅ Tool calling formal com JSON schema
- ✅ Credenciais em `.env`
- ✅ Parser de datas relativas
- ✅ Retry com backoff exponencial

### Versão legada (agent_core.py)
- ⚠️ Usa Gemini API (cloud, paga)
- ⚠️ Credenciais expostas no código
- ⚠️ Tool selection manual (retorna só o nome)

## 🤝 Contribuindo

Ao modificar o código:
1. **NUNCA** commitar credenciais (verificar `.gitignore`)
2. Testar com dados reais antes de mergear
3. Manter compatibilidade com formato de resposta da API
4. Adicionar docstrings em funções novas

## 📚 Referências

- [LiteLLM Docs](https://docs.litellm.ai)
- [Ollama](https://ollama.ai)
- [CV CRM API Docs](https://cvcrm.com.br/api-docs) (se disponível)
- [Pandas](https://pandas.pydata.org)

---

**Última atualização:** 2025-09-30
**Versão:** 1.0 (agent.py)
**Contato:** tiago.bocchino@4pcapital.com.br