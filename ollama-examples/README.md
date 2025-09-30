# Agente Analytics - Assistente de Análise de Leads

Assistente conversacional que analisa dados de leads do CV CRM usando IA local (Llama via Ollama).

## Status do Projeto

✅ **Código funcional** - Arquitetura e lógica implementadas
⚠️ **Performance** - Modelo LLM requer GPU ou CPU potente para execução em tempo real

## Arquitetura

```
[Usuário]
    ↓ pergunta em português
[agent.py]
    ↓ usa Ollama
[Llama 3.2 3B]
    ↓ decide chamar ferramenta
[analyze_leads_by_broker()]
    ↓ busca dados
[CV CRM API via CVDW]
    ↓ retorna dados
[Pandas processa]
    ↓ formata resposta
[Llama gera resposta natural]
    ↓
[Usuário recebe resposta]
```

## Requisitos

### Sistema
- **CPU**: i5/Ryzen 5 ou superior (mínimo 8 threads)
- **RAM**: 8 GB mínimo, 16 GB recomendado
- **GPU**: Opcional mas ALTAMENTE recomendado (NVIDIA com CUDA ou AMD com ROCm)
- **Disco**: 5 GB livres para modelos

### Software
- Python 3.9+
- Ollama 0.11+
- Dependências Python (veja [requirements.txt](requirements.txt))

## Instalação

### 1. Instalar Ollama

**Windows:**
```bash
# Baixar de https://ollama.ai e instalar
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Baixar modelo LLM

```bash
# Modelo leve (2 GB - recomendado para CPU)
ollama pull llama3.2:3b

# Modelo completo (4.7 GB - requer GPU)
ollama pull llama3
```

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciais

Criar arquivo `.env` na raiz:

```env
CV_SUBDOMAIN=bpincorporadora
CV_EMAIL=seu-email@dominio.com.br
CV_TOKEN=seu-token-aqui
```

## Uso

### Rodar Ollama (em terminal separado)

```bash
ollama serve
```

### Rodar Agente

```bash
python agent.py
```

### Exemplos de perguntas

```
Voce: Quantos leads tivemos este mes?
Agente: Foram encontrados 127 leads neste mês.

Voce: Qual corretor teve mais leads?
Agente: João Silva liderou com 45 leads.

Voce: Quantos leads a Maria teve?
Agente: A corretora Maria teve 32 leads.

Voce: sair
```

## Problemas Conhecidos

### ⚠️ Modelo muito lento / travando

**Causa:** Llama 3.2 3B (2 GB) é o menor modelo funcional mas ainda pesado para CPU fraco.

**Soluções:**

1. **GPU** (melhor opção):
   - NVIDIA: Instalar CUDA
   - AMD: Instalar ROCm
   - Ollama detecta automaticamente

2. **CPU mais potente**:
   - i7/Ryzen 7 com 12+ threads
   - 16 GB+ RAM

3. **Usar modelo menor** (experimentalHuman: pode parar os processos em background