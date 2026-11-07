"""Chat interativo via CMD — Strands Agents + OpenAI.

Uso:
    1. Copie .env.example para .env e preencha OPENAI_API_KEY
    2. pip install -r requirements.txt
    3. python chat.py

Comandos no chat: 'sair'/'exit'/'quit' encerra | 'nova' limpa a sessão.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI
from strands import Agent, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager

SESSIONS_DIR = Path(__file__).parent / ".sessions"
WINDOW_SIZE = 40
DEFAULT_SYSTEM_PROMPT =  """\
Você é um assistente de clima amigável e objetivo.

Sua função é informar o clima atual e a previsão do tempo de qualquer cidade, usando a ferramenta OpenWeatherMap disponível.

Regras:
1. Quando o usuário perguntar sobre o clima, sempre consulte a ferramenta antes de responder. Nunca invente dados.
2. Se o usuário não informar a cidade, pergunte qual cidade ele quer consultar.
3. Se a cidade for ambígua (ex: "Santa Cruz"), peça o estado ou país.
4. Responda sempre em português, em tom natural e curto.
5. Use unidades métricas: temperatura em °C, vento em km/h.

Formato da resposta:
- Condição geral (ex: nublado, chuva leve)
- Temperatura atual e sensação térmica
- Umidade e vento
- Uma dica prática curta (ex: "leve guarda-chuva")

Se a ferramenta retornar erro ou não encontrar a cidade, avise o usuário de forma simples e peça para tentar outro nome.

Se a pergunta não for sobre clima, diga educadamente que só pode ajudar com informações meteorológicas.
"""


@tool
def data_hora_atual() -> str:
    """Retorna a data e a hora atuais do sistema."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


@tool
def clima_atual(cidade: str) -> str:
    """Retorna o clima em tempo real de uma cidade via OpenWeatherMap.

    Args:
        cidade: Nome da cidade, ex.: "Sao Paulo" ou "Lisboa".
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return "Clima indisponivel: configure OPENWEATHER_API_KEY no .env"
    try:
        resp = httpx.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": cidade,
                "appid": api_key,
                "units": "metric",
                "lang": "pt_br",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Cidade '{cidade}' nao encontrada."
        return f"Erro na API de clima (HTTP {exc.response.status_code})."
    except httpx.HTTPError as exc:
        return f"Falha ao consultar o clima: {exc}"
    data = resp.json()
    return (
        f"Clima em {data['name']}, {data['sys']['country']}: "
        f"{data['weather'][0]['description']}, "
        f"{data['main']['temp']:.1f}C (sensacao {data['main']['feels_like']:.1f}C), "
        f"umidade {data['main']['humidity']}%, "
        f"vento {data['wind']['speed']} m/s."
    )


def load_config() -> dict:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Erro: OPENAI_API_KEY nao encontrada.")
        print("Copie .env.example para .env e configure sua chave da OpenAI.")
        sys.exit(1)
    return {
        "api_key": api_key,
        "model_id": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "session_id": os.getenv("SESSION_ID", "default"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "max_retries": int(os.getenv("OPENAI_MAX_RETRIES", "3")),
        "max_tokens": int(os.getenv("MAX_TOKENS", "500")),
        "system_prompt": os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
    }


def check_openai_connection(cfg: dict) -> None:
    try:
        OpenAI(api_key=cfg["api_key"]).models.list()
    except Exception as exc:
        print(f"Erro: nao foi possivel conectar a OpenAI ({exc})")
        print("Verifique a OPENAI_API_KEY e sua conexao com a internet.")
        sys.exit(1)


def build_agent(cfg: dict, session_id: str) -> Agent:
    model = OpenAIModel(
        client_args={
            "api_key": cfg["api_key"],
            "max_retries": cfg["max_retries"],
            "timeout": 30.0,
        },
        model_id=cfg["model_id"],
        params={
            "temperature": cfg["temperature"],
            "max_tokens": cfg["max_tokens"],
        },
    )
    return Agent(
        model=model,
        callback_handler=None,
        session_manager=FileSessionManager(
            session_id=session_id, storage_dir=str(SESSIONS_DIR)
        ),
        conversation_manager=SlidingWindowConversationManager(
            window_size=WINDOW_SIZE
        ),
        tools=[data_hora_atual, clima_atual],
        system_prompt=cfg["system_prompt"],
    )


def reset_session(cfg: dict, session_id: str) -> Agent:
    shutil.rmtree(SESSIONS_DIR / session_id, ignore_errors=True)
    return build_agent(cfg, session_id)


def build_agent_safe(cfg: dict, session_id: str) -> Agent:
    try:
        return build_agent(cfg, session_id)
    except Exception as exc:
        print(f"Aviso: nao foi possivel carregar a sessao salva ({exc})")
        resp = input("Criar uma nova sessao? [s/n] ").strip().lower()
        if resp == "s":
            return reset_session(cfg, session_id)
        sys.exit(1)


def chat_loop(agent: Agent, cfg: dict, session_id: str) -> None:
    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo!")
            break
        if not user_input:
            continue
        cmd = user_input.lower()
        if cmd in ("sair", "exit", "quit"):
            print("Até logo!")
            break
        if cmd == "nova":
            agent = reset_session(cfg, session_id)
            print("Sessão limpa. Como posso ajudar?\n")
            continue
        try:
            print(f"Agente: {agent(user_input)}\n")
        except Exception as exc:
            print(f"Erro ao contactar o modelo: {exc}\n")


def main() -> None:
    cfg = load_config()
    check_openai_connection(cfg)
    agent = build_agent_safe(cfg, cfg["session_id"])
    print("=== Chat Agente (Strands + OpenAI) ===")
    print("Digite 'sair' para encerrar ou 'nova' para limpar a sessão.\n")
    chat_loop(agent, cfg, cfg["session_id"])


if __name__ == "__main__":
    main()
