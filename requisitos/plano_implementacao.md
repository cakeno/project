# Plano de Implementação — Chat Interativo CMD (Strands + OpenAI)

**Documento:** plano_implementacao.md
**Base:** requisitos01.md + design_rf01.md
**Responsável técnico:** Tech Lead (Devin — orquestração)
**Data:** 2026-11-07
**Status:** Decisões D-01..D-06 fechadas (2026-11-07); Fase 1 concluída; aguardando B-01/B-02 para executar

---

## 1. Visão Executiva

Implementar o chat CLI conforme `design_rf01.md`: loop REPL em Python, agente Strands com `OpenAIModel` (gpt-4o-mini), sessão persistida em `./.sessions/` via `FileSessionManager`, tool `data_hora_atual`, credenciais em `.env`.

**Meta de simplicidade:** ~1 arquivo de código (`chat.py`, ~100 linhas), 4 arquivos de suporte (`requirements.txt`, `.env.example`, `.gitignore`, `README` embutido no docstring/ajuda).

---

## 2. Pré-requisitos e Bloqueadores (Fase 0)

| # | Bloqueador | Ação | Dono |
|---|-----------|------|------|
| B-01 | Python ausente no PATH (só alias da MS Store) | Usuário instalará via `winget install Python.Python.3.12` ("Add to PATH") | **Usuário** — decidido, pendente de execução |
| B-02 | `OPENAI_API_KEY` ainda não existe | Usuário criará em platform.openai.com e colocará no `.env`; não bloqueia a escrita do código | **Usuário** — decidido, pendente de execução |
| B-03 | Inconsistência de escopo entre docs (persistência) | **RESOLVIDO** — requisitos01.md alinhado: persistência entrou no escopo | Devin ✅ |
| B-04 | Comportamentos indefinidos | **RESOLVIDO** — D-01..D-06 decididas pelo usuário (ver §3) | Usuário ✅ |

---

## 3. Decisões Fechadas pelo Usuário (2026-11-07)

| # | Questão | Decisão |
|---|---------|---------|
| D-01 | Como iniciar nova sessão? | ✅ Comando `nova` dentro do chat — limpa `.sessions/<id>` e reconstrói o Agent |
| D-02 | Crescimento do histórico | ✅ `SlidingWindowConversationManager` (window=40) combinado ao `FileSessionManager` |
| D-03 | Sessão corrompida | ✅ Aviso + pergunta `[s/n]`; `n` → exit 1 |
| D-04 | Encoding CMD/PT-BR | ✅ Padrão do sistema (sem forçar UTF-8); reabrir se acentos quebrarem |
| D-05 | Streaming | ✅ Fora do escopo v1 |
| D-06 | Validação da API key | ✅ Teste de conexão real no startup (1 chamada leve à API) |

---

## 4. Fases e Atividades

### Fase 1 — Alinhamento dos Documentos (0.5 dia, baixo risco)

| ID | Atividade | Detalhe | Agente |
|----|-----------|---------|--------|
| A-01 | Atualizar `requisitos01.md` | **CONCLUÍDO** — persistência no escopo, RF-09..RF-12, §11 com decisões | Devin ✅ |
| A-02 | Revisar `design_rf01.md` | **CONCLUÍDO** — §3.2/§3.5 (sliding window + teste de conexão), §6 fluxo s/n | Devin ✅ |

### Fase 2 — Setup do Projeto (0.5 dia)

| ID | Atividade | Detalhe | Agente |
|----|-----------|---------|--------|
| A-03 | Criar `.gitignore` | `.env`, `.sessions/`, `__pycache__/`, `*.pyc`, `venv/` | `subagent_general` |
| A-04 | Criar `requirements.txt` | `strands-agents`, `openai`, `python-dotenv` — verificar versões estáveis ≥7 dias e fixar pins | `subagent_general` + `subagent_explore` (consultar PyPI/versões) |
| A-05 | Criar `.env.example` | Variáveis documentadas (OPENAI_API_KEY, OPENAI_MODEL, SESSION_ID, TEMPERATURE) | `subagent_general` |
| A-06 | Validar ambiente | `py -m venv venv` → instalar deps → smoke test `python -c "import strands"` | `subagent_general` |

### Fase 3 — Implementação do Core (1 dia)

| ID | Atividade | Detalhe | Agente |
|----|-----------|---------|--------|
| A-07 | Implementar `chat.py` | Conforme design §3: `main()`, `check_openai_connection()`, `build_agent()` (SlidingWindow + FileSession), `chat_loop()`, tool `data_hora_atual` | `subagent_general` |
| A-08 | Tratamento de erros | Tabela do design §6: key ausente, falha API, Ctrl+C, sessão corrompida, input vazio | `subagent_general` (mesma entrega que A-07) |
| A-09 | Comando `nova` | Reset de sessão em runtime conforme D-01 | `subagent_general` (mesma entrega) |

**Estrutura de `chat.py` (contrato):**

```
load_config()             → dict com config validada (exit 1 se sem key)
check_openai_connection() → chamada leve à API no startup (D-06)
build_agent(cfg,sid)      → Agent(OpenAIModel, FileSessionManager, SlidingWindow, tools)
data_hora_atual()         → @tool retornando "dd/mm/aaaa hh:mm:ss"
reset_session(sid)        → limpa .sessions/<id>, reconstrói Agent (D-01/D-03)
chat_loop(agent,cfg)      → REPL: sair | nova | <msg>
main()                    → load_config → check conn → build_agent → banner → loop
```

### Fase 4 — Verificação e Qualidade (0.5 dia)

| ID | Atividade | Detalhe | Agente |
|----|-----------|---------|--------|
| A-10 | Teste manual guiado | Roteiro dos critérios de aceite (design §7): startup, pergunta geral, hora (tool), restart c/ contexto, `nova`, `sair` | `subagent_general` executa; **usuário** valida |
| A-11 | Revisão de código | Checklist: sem `eval`, sem secrets hardcoded, `.gitignore` correto, erros amigáveis | `subagent_explore` (read-only review) |
| A-12 | Documentação mínima | Docstring de módulo com instruções de uso + atualizar docs se implementação divergir | `subagent_general` |

---

## 5. Agentes Necessários

| Agente | Perfil | Papel no projeto | Quando atua |
|--------|--------|------------------|-------------|
| **Orquestrador** | Devin (tech lead) | Decompõe tarefas, aprova entregas, resolve conflitos, reporta ao usuário | Todas as fases |
| **Pesquisador** | `subagent_explore` | Verificar versão mínima do `strands-agents` com `FileSessionManager`, checar releases do PyPI para pins, revisão de código final | A-04, A-11 |
| **Implementador** | `subagent_general` | Escrever `chat.py`, arquivos de config, ajustes nos docs, rodar testes manuais | A-01 a A-10, A-12 |
| **Usuário** | Humano | Instalar Python (B-01), fornecer `OPENAI_API_KEY` (B-02), aprovar D-01..D-06, aceite final (A-10) | Fases 0 e 4 |

> **Nota:** por se tratar de projeto simples (1 arquivo), um único `subagent_general` cobre toda a escrita de código — não justifica múltiplos implementadores. O `subagent_explore` é usado apenas para checagens pontuais (read-only), evitando conflito de escrita.

---

## 6. Dependências e Ordem de Execução

```
B-01 (Python) ──┐
                ├──► A-04/A-06 (deps + ambiente)
B-02 (API key) ─┘
B-03/B-04 ──► A-01/A-02 (docs alinhados)
                │
A-03/A-04/A-05 (arquivos base, paralelos)
                │
              A-06 (ambiente ok)
                │
        A-07/A-08/A-09 (chat.py)
                │
        A-10/A-11/A-12 (verificação) ──► ACEITE
```

**Ordem prática sugerida:**
1. Docs alinhados (A-01, A-02) — pode começar já, sem Python
2. Arquivos base (A-03, A-04, A-05) — idem
3. Quando usuário instalar Python e fornecer key → A-06
4. Implementação (A-07..A-09)
5. Verificação (A-10..A-12)

---

## 7. Definition of Done

- [ ] Todos os critérios de aceite do `design_rf01.md` §7 passam
- [ ] `python chat.py` funciona no CMD do Windows com acentos corretos
- [ ] Tool `data_hora_atual` dispara em perguntas sobre data/hora
- [ ] Reiniciar com mesmo `SESSION_ID` restaura contexto; comando `nova` limpa
- [ ] Nenhum secret no repositório; `.env` e `.sessions/` gitignored
- [ ] `requisitos01.md` e `design_rf01.md` consistentes com a implementação final

---

## 8. Riscos do Plano

| Risco | Prob. | Mitigação |
|-------|-------|-----------|
| `FileSessionManager` indisponível/incompatível na versão atual do SDK | Média | A-04 valida antes de codar; fallback documentado (RAM + JSON manual) |
| Encoding UTF-8 insuficiente no CMD legado | Baixa | Fallback `chcp 65001` documentado na mensagem de erro |
| Usuário sem API key / sem créditos OpenAI | Média | Bloqueador B-02 explicitado antes do código |
| Scope creep (pedidos de GUI, streaming, mais tools) | Média | Escopo congelado em v1; registrar melhorias em requisitos02.md futuro |
