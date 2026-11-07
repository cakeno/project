# Requisitos — Chat Interativo via CMD (Strands Agents + OpenAI)

**Documento:** requisitos01.md
**Data:** 2026-11-07
**Status:** Refinado — decisões fechadas (ver §11), pronto para implementação

---

## 1. Objetivo

Criar um **agente de chat interativo executado via terminal (CMD)**, construído em **Python**, rodando **localmente** na máquina do usuário. O agente utilizará o **Strands Agents SDK** (framework open-source da AWS para construção de agentes) com o **modelo da OpenAI** como provedor de LLM.

O agente será **simples**: um loop de conversa no terminal, com memória de sessão persistida em arquivo local e uma tool de data/hora.

---

## 2. Escopo

### Dentro do escopo
- Aplicação de linha de comando (CLI) em Python.
- Integração com a API da OpenAI através do `OpenAIModel` do Strands Agents.
- **Memória de sessão persistida em arquivos locais** (`.sessions/`) via `FileSessionManager`, com janela deslizante de contexto.
- Tool `data_hora_atual` (retorna data e hora atuais do sistema).
- Comandos de controle no chat: `sair`/`exit`/`quit` e `nova` (limpa sessão).
- Validação da conexão com a OpenAI no startup.
- Configuração de credenciais via arquivo `.env`.

### Fora do escopo
- Interface gráfica (GUI) ou web.
- Streaming de respostas (avaliar em v2).
- Tools adicionais além de `data_hora_atual` (ex.: calculadora) — opcional/futuro.
- Uso de AWS Bedrock ou credenciais AWS (o Strands é usado apenas como framework de agentes).
- Deploy, containers, CI/CD.
- Autenticação de usuários ou multiusuário.

---

## 3. Stack Técnica

| Componente       | Escolha                                                        |
|------------------|----------------------------------------------------------------|
| Linguagem        | Python 3.10+                                                   |
| Framework agente | `strands-agents`                                               |
| Provedor LLM     | `strands.models.openai.OpenAIModel` (API OpenAI)               |
| Modelo           | `gpt-4o-mini` (configurável via `.env`)                        |
| Memória/sessão   | `FileSessionManager` + `SlidingWindowConversationManager`      |
| Config/Secrets   | `python-dotenv` + arquivo `.env`                               |
| Gerenciador deps | `pip` + `requirements.txt`                                     |

**Observação:** o provedor OpenAI do Strands requer apenas a `OPENAI_API_KEY`. Nenhuma credencial AWS é necessária.

---

## 4. Requisitos Funcionais

| ID    | Requisito                                                                                                          |
|-------|--------------------------------------------------------------------------------------------------------------------|
| RF-01 | Ao executar `python chat.py`, a aplicação inicia um loop de conversa no terminal com prompt `Você: `.             |
| RF-02 | O usuário digita mensagens e recebe a resposta do agente prefixada por `Agente: `.                                  |
| RF-03 | O contexto é mantido durante a sessão **e restaurado entre execuções** a partir de `.sessions/`.                    |
| RF-04 | O comando `sair` (ou `exit`/`quit`) encerra o programa de forma limpa.                                              |
| RF-05 | O agente possui a tool `data_hora_atual`, que retorna a data e hora atuais do sistema.                              |
| RF-06 | Ao iniciar, o agente exibe uma mensagem de boas-vindas e as instruções básicas de uso.                              |
| RF-07 | Erros de API (sem chave, sem conexão, rate limit) são capturados e exibidos como mensagem amigável, sem traceback.  |
| RF-08 | Entrada vazia é ignorada (não envia requisição à API).                                                              |
| RF-09 | O comando `nova` limpa a sessão atual (apaga `.sessions/<session_id>`) e reinicia o contexto do agente.             |
| RF-10 | No startup, uma chamada leve à API OpenAI valida a conexão/chave; falha → mensagem clara + exit 1.                  |
| RF-11 | Se a sessão persistida estiver corrompida, o usuário é avisado e perguntado `[s/n]` se deseja criar sessão nova.    |
| RF-12 | O histórico é limitado por janela deslizante (~últimas 40 mensagens) para conter custo/contexto.                    |

---

## 5. Requisitos Não-Funcionais

| ID     | Requisito                                                                                          |
|--------|----------------------------------------------------------------------------------------------------|
| RNF-01 | Execução 100% local via `python chat.py` após `pip install -r requirements.txt`.                   |
| RNF-02 | A `OPENAI_API_KEY` é lida de `.env` (nunca hardcoded). `.env` deve constar no `.gitignore`.        |
| RNF-03 | Fornecer `.env.example` documentando as variáveis esperadas.                                       |
| RNF-04 | Código em um único arquivo principal (`chat.py`) + módulo opcional de tools, mantendo simplicidade.|
| RNF-05 | Compatível com Windows (CMD/PowerShell), sem dependências nativas de compilação.                   |
| RNF-06 | Respostas e prompts em português (PT-BR), usando o encoding padrão do sistema.                     |
| RNF-07 | Versões das dependências fixadas (pinned) no `requirements.txt`.                                   |

---

## 6. Estrutura de Arquivos Sugerida

```
project/
├── chat.py              # loop principal do chat + configuração do Agent + tool
├── requirements.txt     # strands-agents, openai, python-dotenv (versões fixadas)
├── .env.example         # documenta as variáveis esperadas
├── .env                 # (local, gitignored)
├── .sessions/           # gitignored — sessões persistidas
└── .gitignore           # deve conter .env, .sessions/, __pycache__/
```

---

## 7. Configuração (.env)

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini        # opcional, default gpt-4o-mini
SESSION_ID=default              # opcional — identifica a sessão persistida
TEMPERATURE=0.7                 # opcional
OPENAI_MAX_RETRIES=3            # opcional — retentativas em erro/rate limit
MAX_TOKENS=500                  # opcional — limite de tokens por resposta
SYSTEM_PROMPT=...               # opcional, default: assistente útil em PT-BR
```

---

## 8. Fluxo Esperado (exemplo)

```
$ python chat.py
=== Chat Agente (Strands + OpenAI) ===
Digite 'sair' para encerrar ou 'nova' para limpar a sessão.

Você: que horas são?
Agente: Agora são 14:32 do dia 07/11/2026.   <- via tool data_hora_atual

Você: meu time favorito é o Flamengo
Agente: Anotado!

Você: nova
Sessão limpa. Como posso ajudar?

Você: qual meu time favorito?
Agente: Não tenho essa informação — começamos uma nova conversa.

Você: sair
Até logo!
```

---

## 9. Critérios de Aceite

1. `python chat.py` inicia o chat sem erros (com `.env` válido).
2. Falha no teste de conexão do startup (key inválida/sem rede) gera mensagem clara + exit 1.
3. Perguntas gerais são respondidas pelo modelo OpenAI.
4. Perguntas sobre data/hora disparam a tool `data_hora_atual`.
5. Reiniciar o programa com o mesmo `SESSION_ID` restaura o contexto da conversa.
6. `nova` limpa o contexto: o agente não lembra mais do que foi dito.
7. `sair` encerra o programa com código 0.
8. Ausência de `OPENAI_API_KEY` gera mensagem clara de erro (não crash silencioso).

---

## 10. Riscos / Observações

- **Custo:** cada mensagem consome tokens da API OpenAI — `gpt-4o-mini` + janela deslizante mitigam.
- **Versão do SDK:** `FileSessionManager` e a combinação com `SlidingWindowConversationManager` dependem de versão recente do `strands-agents` — validar na implementação; fallback é memória em RAM + serialização manual em JSON.
- **Segurança:** `.env` nunca versionado; `.sessions/` pode conter dados sensíveis da conversa — ambos gitignored.
- **Encoding:** usa o padrão do sistema (decisão D-04); se acentos quebrarem no CMD, reabrir a decisão e forçar UTF-8 no código.

---

## 11. Decisões Registradas (2026-11-07)

| ID   | Questão                                   | Decisão                                                              |
|------|-------------------------------------------|----------------------------------------------------------------------|
| D-01 | Como iniciar nova sessão?                  | Comando `nova` dentro do chat                                        |
| D-02 | Crescimento do histórico persistido        | `FileSessionManager` + `SlidingWindowConversationManager` (~40 msgs) |
| D-03 | Sessão corrompida na inicialização         | Avisar e perguntar `[s/n]` se cria sessão nova                       |
| D-04 | Encoding de acentos PT-BR no CMD           | Padrão do sistema (sem forçar UTF-8)                                 |
| D-05 | Streaming de respostas                     | Fora do escopo da v1                                                 |
| D-06 | Validação da `OPENAI_API_KEY`              | Teste de conexão real no startup (1 chamada leve)                    |

**Pendências de ambiente:** usuário instalará Python 3.10+ via `winget` (B-01) e criará a `OPENAI_API_KEY` (B-02) — não bloqueiam a escrita do código, apenas a execução.
