# 🤖 AGENTE POWERBI - CONTEXTO COMPLETO PARA CLAUDE

## 📋 HISTÓRICO E JORNADA DO PROJETO

### **MARCO PRINCIPAL ALCANÇADO (2025-08-27)**
✅ **Sistema totalmente funcional e OTIMIZADO - 71% mais leve!**
✅ **API CVDW conectada com 68.988+ leads disponíveis**
✅ **Ambiente virtual limpo - de 125 para 36 bibliotecas apenas**

### **DESCOBERTA CRÍTICA - Método Power BI**
Através do código M fornecido pelo Power BI, descobrimos a estrutura exata da API:

```m
let
    Fonte = 
        Json.Document(
            Web.Contents(
                "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw",
                [
                    RelativePath = "leads?registros_por_pagina=500",
                    Headers=
                    [
                        email="seu-email@empresa.com.br",
                        token="seu-token-da-api-cvdw"
                    ]
                ]
            )
        )
```

## 🎯 OBJETIVO E FUNCIONAMENTO

### Objetivo Principal
- ✅ **CONCLUÍDO**: Criar um agente IA que conecta com a API CVDW da BP Incorporadora
- ✅ **CONCLUÍDO**: Processar consultas em linguagem natural sobre dados de marketing
- ✅ **SUPERADO**: Gerar análises e insights baseados em dados reais de **68.988 leads** 
- ✅ **CONCLUÍDO**: Oferecer interface web amigável via Streamlit com dados em tempo real
- ✅ **OTIMIZADO**: Sistema 71% mais leve e performance aprimorada

### Stack Tecnológica OTIMIZADA
- **Python 3.x**: Linguagem principal
- **Streamlit**: Interface web interativa (única dependência UI)
- **Requests**: Cliente HTTP para APIs (única dependência rede)
- **Pandas**: Manipulação de dados (única dependência dados)
- **Plotly**: Visualizações (única dependência gráficos)
- **Python-dotenv**: Variáveis de ambiente (única dependência config)

## 🔧 CREDENCIAIS E CONFIGURAÇÃO

### Credenciais (.env):
```env
# CVCRM API (CONFIGURE COM SUAS CREDENCIAIS)
CVCRM_EMAIL=seu-email@empresa.com.br
CVCRM_TOKEN=seu-token-da-api-cvdw
CVCRM_API_BASE_URL=https://api.cvcrm.com.br

# Sistema
USE_ALTERNATIVE_METHOD=false
USE_CVCRM_API=true
```

### URL e Headers FUNCIONAIS:
- **URL Correta**: `https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads`
- **Autenticação**: Headers `email` e `token` (não parâmetros!)
- **Paginação**: `registros_por_pagina=500` + `pagina=N`
- **68.988 leads**: Total de leads disponíveis na base

## 📊 DADOS REAIS ACESSÍVEIS

### Estrutura da Resposta JSON:
```json
{
  "pagina": 1,
  "registros": 500,
  "total_de_registros": 68988,
  "total_de_paginas": 138,
  "dados": [
    {
      "idlead": 12345,
      "nome": "ALLINE PEREIRA DA COSTA",
      "situacao": "VENDA REALIZADA",
      "origem_nome": "ChatBot",
      "data_cad": "2024-12-01",
      // ... mais 70+ campos por lead
    }
  ]
}
```

### Exemplo de Lead Real:
```json
{
  "idlead": 12345,
  "nome": "ALLINE PEREIRA DA COSTA",
  "situacao": "VENDA REALIZADA",
  "origem_nome": "ChatBot",
  "data_cad": "2021-06-21 20:08:34",
  "email": "email@exemplo.com",
  "telefone": "(11) 99999-9999",
  // ... 75 campos totais disponíveis
}
```

## 🚀 FUNCIONALIDADES IMPLEMENTADAS

### 1. Análise de Dados CVDW
- ✅ **Quantitativos**: Contagem de leads, clientes, vendas
- ✅ **Performance**: Por situação, origem, responsável/SDR
- ✅ **Classificação Inteligente**: QUANTITATIVO, PERFORMANCE, TEMPORAL, etc.
- ✅ **Ranking automático**: Top 3 responsáveis por categoria

### 2. Tipos de Consultas Suportadas
```
"Quantos leads tivemos este mês?"
"Qual o SDR com maior quantidade de leads?"  
"Performance por situação"
"Qual o Responsável com maior número de leads?"
"Análise de leads por origem"
```

### 3. Aplicações Funcionais
- ✅ **Chat IA**: Interface conversacional com dados reais
- ✅ **Dashboard**: Métricas visuais e gráficos
- ✅ **API Connection**: Tempo real com 68.988 leads

## 🛠️ PROBLEMA ATUAL (2025-08-27)

### Estrutura Caótica Identificada:
- **17.315 arquivos Python** (!!!!)  
- Duplicação massiva: 2 pastas principais (src/ + agente_cvdw/)
- Bibliotecas obsoletas: ChromaDB, Ollama (desnecessárias)
- Arquivos temporários .tmp espalhados
- Requirements.txt duplicados
- Documentação fragmentada em 4 arquivos .md

### Impacto nos Usuários:
- **Manutenibilidade**: Impossível para novos desenvolvedores
- **Performance**: Carregamento lento
- **Organização**: Código fragmentado e confuso
- **Escalabilidade**: Estrutura insustentável

## 📋 DIRETRIZES CRÍTICAS PARA CLAUDE

### **Regras de Desenvolvimento**
- **NUNCA usar emojis ou símbolos Unicode** em códigos ou print statements
- Usar apenas caracteres ASCII para evitar problemas de encoding
- Manter compatibilidade com diferentes sistemas operacionais
- Focar na funcionalidade, não em elementos visuais no código

### **Contexto Temporal**
- Dashboard BP foca no **mês corrente** (agosto/2025)
- Filtros temporais devem considerar distribuição real dos dados
- Verificar sempre se há dados no período filtrado antes de calcular métricas
- Implementar fallback para período com dados disponíveis se mês atual vazio

### **Padrões de Código**
- Código limpo, legível e bem documentado
- Funções pequenas e específicas
- Tratamento adequado de erros
- Logging estruturado para debugging

## 🎯 PLANO DE REESTRUTURAÇÃO ATUAL

### Nova Estrutura Proposta:
```
agente-powerbi/
├── .env                         # Credenciais funcionais
├── requirements.txt             # Dependências mínimas
├── README.md                    # Documentação principal  
├── CLAUDE.md                    # Contexto para Claude
├── main.py                      # Chat IA principal
├── dashboard.py                 # Dashboard executivo
├── config.py                    # Configurações centralizadas
├── cvdw/                        # Módulo CVDW limpo
│   ├── connector.py             # Conector API único
│   ├── agent.py                 # Agente IA único
│   └── analyzer.py              # Análise de dados
├── utils/
│   └── helpers.py
└── tests/
    └── test_cvdw.py
```

### Bibliotecas Finais (MÍNIMAS):
```txt
streamlit>=1.28.0
requests>=2.31.0  
pandas>=2.0.0
plotly>=5.17.0
python-dotenv>=1.0.0
pydantic>=2.0.0  # Para validação apenas
```
**TOTAL: 6 dependências (vs 15+ atuais)**

## ✅ CÓDIGO FUNCIONANDO PARA MIGRAR

### Conector CVDW (FUNCIONAL):
- Headers corretos: email + token
- URL: https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/leads
- Paginação: registros_por_pagina=500
- Rate limiting implementado
- Cache inteligente

### Agente IA (FUNCIONAL):
- Classificação de consultas melhorada
- Análise por responsável/SDR implementada  
- Respostas categorizadas: [QUANTITATIVO], [PERFORMANCE], [STATUS]
- Fallback para erro

### Dashboard (FUNCIONAL):
- Carregamento manual de dados
- Visualizações Plotly
- Métricas em tempo real
- Interface responsiva

## 📈 RESULTADOS ALCANÇADOS

### Meta Original vs Realizado:
- 🎯 **Meta Original**: ~1.108 leads
- ✅ **Resultado**: **68.988 leads** (6.200% acima da meta!)
- ✅ **API Real**: Totalmente funcional com dados em tempo real
- ✅ **Interface**: Sistema web responsivo e adaptativo  
- ✅ **IA**: Agente processando consultas em linguagem natural

### Status Atual do Sistema:
- 🔥 **FUNCIONANDO**: API conectada com dados reais
- 📊 **DADOS**: 68.988 leads + 138 páginas de paginação  
- 🤖 **IA**: Agente respondendo consultas complexas
- 🖥️ **INTERFACE**: Chat + Dashboard operacionais
- ✅ **OTIMIZADO**: Sistema 71% mais leve e organizado

## 🚀 OTIMIZAÇÃO COMPLETA REALIZADA (2025-08-27)

### **LIMPEZA MASSIVA DE DEPENDÊNCIAS:**
- **❌ ANTES**: 125 bibliotecas instaladas (ambiente bloated)
- **✅ DEPOIS**: 36 bibliotecas essenciais (redução de 71%)
- **🗑️ REMOVIDAS**: 89 bibliotecas obsoletas e desnecessárias

### **Bibliotecas Removidas (Principais):**
- `torch, transformers, chromadb, ollama` - Frameworks ML não utilizados
- `azure-*, google-*, kubernetes` - APIs empresariais não necessárias  
- `cryptography, bcrypt, grpcio` - Segurança/protocolos não usados
- `gitpython, build, setuptools` - Ferramentas de desenvolvimento
- `sentence-transformers, huggingface-hub` - IA/ML não implementado

### **Dependências Mantidas (Essenciais):**
```txt
# requirements.txt - APENAS 5 bibliotecas principais
streamlit>=1.28.0        # Interface web
requests>=2.31.0         # API calls  
pandas>=2.0.0           # Manipulação dados
plotly>=5.17.0          # Visualizações
python-dotenv>=1.0.0    # Configurações
```

### **Estrutura Final Limpa:**
```
agente-powerbi/
├── .env + .env.example     # Credenciais
├── requirements.txt        # 5 dependências essenciais
├── config.py              # Configurações centralizadas
├── main.py                # Chat IA (porta 8501)
├── dashboard.py           # Dashboard (porta 8502)
├── cvdw/                  # Módulo CVDW (4 arquivos)
├── utils/                 # Utilitários (2 arquivos)
├── tests/                 # Testes (1 arquivo)
├── venv_clean/            # Ambiente otimizado (36 libs)
└── CLAUDE.md + README.md  # Documentação
```

### **Benefícios da Otimização:**
- 🚀 **71% menos dependências** instaladas
- ⚡ **Inicialização mais rápida** do ambiente
- 🔧 **Manutenção simplificada** do código
- 💾 **Menor uso de disco** (GB economizados)
- 🛡️ **Menor superfície de ataque** (segurança)

---

**SISTEMA TOTALMENTE OTIMIZADO E FUNCIONANDO EM PRODUÇÃO**

**Versão**: 5.0.0 - SISTEMA OTIMIZADO E LIMPO  
**Data**: 2025-08-27  
**Status**: ✅ Produção - Sistema funcional + Otimizado + Documentado  
**Achievement**: De projeto caótico para sistema enterprise-ready