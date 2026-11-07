# Design Técnico — RF-01: Loop de Chat Interativo via CMD

**Documento:** design_rf01.md
**Requisito base:** RF-01 a RF-12 (requisitos01.md)
**Data:** 2026-11-07
**Status:** Aprovado — decisões D-01..D-06 fechadas

---

## 1. Visão Geral

Aplicação CLI em Python que inicia um loop de conversa no terminal ao executar `python chat.py`. O agente é construído com o **Strands Agents SDK**, usa o modelo **OpenAI** (`gpt-4o-mini` por padrão), persiste a **sessão em arquivos locais** com **janela deslizante de contexto** e expõe a tool `data_hora_atual`.

### Decisões de design (confirmadas com o usuário — 2026-11-07)

| Decisão                  | Escolha                                                              |
|--------------------------|----------------------------------------------------------------------|
| Linguagem                | Python 3.10+                                                         |
| Framework de agente      | Strands Agents SDK (`strands-agents`)                                |
| Provedor LLM             | `strands.models.openai.OpenAIModel`                                  |
| Credenciais              | `.env` via `python-dotenv`                                           |
| Memória de sessão        | `FileSessionManager` (`./.sessions/`) + `SlidingWindowConversationManager` |
| Nova sessão              | Comando `nova` dentro do chat (D-01)                                 |
| Sessão corrompida        | Aviso + pergunta `[s/n]` para criar sessão nova (D-03)               |
| Encoding                 | Padrão do sistema, sem forçar UTF-8 (D-04)                           |
| Streaming                | Fora do escopo v1 (D-05)                                             |
| Validação da API key     | Teste de conexão real no startup (D-06)                              |
| Tools                    | `data_hora_atual` (custom, via decorator `@tool`)                    |

---

## 2. Arquitetura

```
┌──────────────────────────────────────────────────────────┐
│                      chat.py (main)                      │
│  load_dotenv() → load_config() → teste de conexão        │
│  → build_agent() → chat_loop()                           │
└──────────────┬───────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│                     strands.Agent                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │ OpenAIModel (model_id="gpt-4o-mini")               │  │
│  │   → consome OPENAI_API_KEY do ambiente             │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ FileSessionManager(session_id, ./.sessions)        │  │
│  │   → persiste mensagens/estado em arquivos locais   │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ SlidingWindowConversationManager(window=40)        │  │
│  │   → limita histórico enviado ao modelo             │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ tools=[data_hora_atual]                            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
               │
               ▼
        OpenAI API (HTTPS)
```

---

## 3. Componentes

### 3.1 `chat.py` — ponto de entrada

```python
def main() -> None:
    """Carrega .env, valida config, testa conexão, instancia o Agent, roda o REPL."""

def load_config() -> dict:
    """Lê e valida variáveis de ambiente; exit 1 com msg clara se sem key."""

def check_openai_connection(cfg: dict) -> None:
    """Chamada leve à API (models.list ou ping); falha → msg clara + exit 1."""

def build_agent(cfg: dict, session_id: str) -> Agent:
    """Agent com OpenAIModel, FileSessionManager, SlidingWindow, tools."""

def reset_session(session_id: str) -> Agent:
    """Apaga .sessions/<id> e reconstrói o Agent (comando 'nova')."""

def chat_loop(agent: Agent, cfg: dict) -> None:
    """REPL: vazio→ignora | sair→encerra | nova→reset_session | msg→agent(msg)."""
```

**Responsabilidades:**
- `load_dotenv()` antes de qualquer acesso a `os.environ`.
- Validar `OPENAI_API_KEY` presente → em seguida, `check_openai_connection()` faz uma chamada leve real à API (D-06). Falha → mensagem clara + exit 1.
- Banner de boas-vindas + instruções (`sair`, `nova`).
- `try/except` ao redor da chamada ao agente → mensagem amigável (sem traceback).
- `KeyboardInterrupt`/`EOFError` → encerramento limpo (equivale a `sair`).

### 3.2 Memória de sessão — `FileSessionManager` + `SlidingWindowConversationManager`

```python
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager

session_manager = FileSessionManager(
    session_id=os.getenv("SESSION_ID", "default"),
    storage_dir="./.sessions",
)
conversation_manager = SlidingWindowConversationManager(
    window_size=40,  # ~últimas 40 mensagens (D-02)
)
agent = Agent(
    model=model,
    session_manager=session_manager,
    conversation_manager=conversation_manager,
    tools=[data_hora_atual],
)
```

- **Persistência:** o Strands serializa o estado em `.sessions/<session_id>/` — ao reabrir com o mesmo `SESSION_ID`, a conversa é restaurada (RF-03).
- **Janela deslizante:** limita o histórico enviado ao modelo às últimas ~40 mensagens, contendo custo e contexto (D-02, RF-12).
- **Nova sessão (D-01, RF-09):** comando `nova` no chat → `reset_session()` apaga `.sessions/<session_id>/` e reconstrói o Agent.
- **Sessão corrompida (D-03, RF-11):** exceção ao carregar sessão → aviso + `input("Criar nova sessão? [s/n] ")`; `s` → `reset_session()`; `n` → exit 1.
- **Git:** `.sessions/` no `.gitignore`.

### 3.3 Modelo — `OpenAIModel`

```python
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    client_args={"api_key": os.environ["OPENAI_API_KEY"]},
    model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    params={"temperature": float(os.getenv("TEMPERATURE", "0.7"))},
)
```

### 3.4 Tool — `data_hora_atual`

```python
from strands import tool
from datetime import datetime

@tool
def data_hora_atual() -> str:
    """Retorna a data e a hora atuais do sistema."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
```

- Zero dependências externas; o modelo decide quando invocá-la (RF-05).

### 3.5 Validação de conexão (D-06, RF-10)

```python
from openai import OpenAI

def check_openai_connection(cfg):
    client = OpenAI(api_key=cfg["api_key"])
    client.models.list()  # chamada leve; levanta exceção se key inválida/sem rede
```

- Executada uma vez no startup, antes de montar o Agent.

---

## 4. Fluxo de Dados

```
1. python chat.py
2. load_dotenv() → load_config()
   └─ OPENAI_API_KEY ausente → msg clara + exit 1
3. check_openai_connection()
   └─ falha → msg clara + exit 1
4. build_agent():
   a. OpenAIModel(api_key, model_id, temperature)
   b. FileSessionManager(session_id, ./.sessions)
      └─ sessão corrompida → aviso + pergunta [s/n] (n → exit 1)
   c. SlidingWindowConversationManager(window=40)
   d. Agent(model, session_manager, conversation_manager, tools, system_prompt)
5. Banner de boas-vindas ("sair" / "nova")
6. Loop:
   input("Você: ")
   ├─ vazio            → continua
   ├─ sair/exit/quit   → "Até logo!" → break
   ├─ nova             → reset_session() → "Sessão limpa." → continua
   └─ mensagem         → agent(mensagem)
                         ├─ Strands chama tool? → executa → volta ao LLM
                         └─ imprime "Agente: <resposta>"
7. FileSessionManager persiste o estado a cada turno (automático no SDK)
```

---

## 5. Arquivos e Configuração

### Estrutura

```
project/
├── chat.py            # único arquivo de código (simplicidade)
├── requirements.txt   # strands-agents, openai, python-dotenv (pinned)
├── .env.example
├── .env               # gitignored
├── .sessions/         # gitignored — estado das sessões
└── .gitignore         # .env, .sessions/, __pycache__/, venv/
```

### `.env`

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini        # opcional
SESSION_ID=default              # opcional — identifica a sessão persistida
TEMPERATURE=0.7                 # opcional
OPENAI_MAX_RETRIES=3            # opcional — retentativas em erro/rate limit
MAX_TOKENS=500                  # opcional — limite de tokens por resposta
```

### `requirements.txt` (versões fixadas — RNF-07)

```
strands-agents
openai
python-dotenv
```

*(pin exato a definir na implementação, conforme releases estáveis disponíveis)*

---

## 6. Tratamento de Erros

| Cenário                        | Comportamento                                                  |
|--------------------------------|----------------------------------------------------------------|
| `OPENAI_API_KEY` ausente       | "Configure OPENAI_API_KEY no .env" + exit 1                    |
| Falha no teste de conexão      | "Não foi possível conectar à OpenAI: \<motivo\>" + exit 1      |
| Falha de rede / API (5xx, 429) | "Erro ao contactar o modelo: \<motivo\>" — loop segue          |
| `Ctrl+C` / `Ctrl+D`            | Encerra com "Até logo!"                                        |
| `.sessions/` corrompido        | Aviso + pergunta `[s/n]` → `s` cria nova; `n` exit 1 (D-03)    |
| Input vazio / só espaços       | Ignorado, novo prompt                                          |

---

## 7. Critérios de Aceite

1. `python chat.py` abre o prompt `Você: ` sem erros.
2. Falha no teste de conexão (key inválida/sem rede) → msg clara + exit 1.
3. Mensagens enviadas retornam resposta `Agente: ...`.
4. "que horas são?" dispara a tool `data_hora_atual`.
5. Reiniciar com mesmo `SESSION_ID` restaura o contexto.
6. `nova` limpa o contexto (agente não lembra do que foi dito).
7. `.sessions/` é criado automaticamente na primeira execução.
8. `sair` encerra com código 0.

---

## 8. Pontos de Atenção

- **Compatibilidade do SDK:** `FileSessionManager` e a combinação `session_manager` + `conversation_manager` no `Agent` dependem de versão recente do `strands-agents` — validar na implementação; se a combinação não for suportada, priorizar `FileSessionManager` e aplicar a janela manualmente (ou documentar a limitação).
- **Encoding:** decisão foi manter o padrão do sistema (D-04). Se acentos quebrarem no CMD (cp1252), reabrir a decisão — fix simples: `sys.stdout.reconfigure(encoding="utf-8")` no `main()`.
- **Custo:** `gpt-4o-mini` + janela de 40 mensagens limitam gasto; teste de conexão no startup consome 1 request leve por execução.
- **Simplicidade:** tudo em `chat.py` (~120 linhas estimadas); separar `tools.py` apenas se o número de tools crescer.
