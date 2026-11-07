# Chat de Clima no Terminal

Um programinha em Python que conversa com você no terminal e informa o clima de qualquer cidade. Ele lembra das conversas anteriores, mesmo depois de fechar.

## O que você precisa antes de começar

1. **Python instalado** — baixe em [python.org](https://www.python.org). Na instalação, marque a opção **"Add Python to PATH"**.
2. **Chave da OpenAI** — crie em https://platform.openai.com/api-keys (precisa ter créditos na conta).
3. **Chave do OpenWeatherMap** — crie grátis em https://openweathermap.org/api (é o que faz a consulta de clima funcionar).

## Instalação (só precisa fazer uma vez)

Abra o **PowerShell** dentro da pasta do projeto e rode estes dois comandos:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Colocando suas chaves

Ainda no PowerShell, rode:

```powershell
notepad .env
```

O bloco de notas vai perguntar se quer criar o arquivo — clique em **Sim**. Cole isto dentro, trocando pelas suas chaves:

```
OPENAI_API_KEY=sk-sua-chave-aqui
OPENWEATHER_API_KEY=sua-chave-do-openweather
```

Salve e feche. **Nunca compartilhe esse arquivo nem as chaves com ninguém.**

## Usando

```powershell
.\venv\Scripts\python.exe chat.py
```

Aí é só digitar, por exemplo: `como está o clima em São Paulo?`

- Digite `nova` para começar uma conversa do zero (esquece tudo).
- Digite `sair` para fechar.

## Deu problema?

| Problema | O que fazer |
|----------|-------------|
| `OPENAI_API_KEY nao encontrada` | O arquivo `.env` não existe ou está sem a chave. Refaça o passo "Colocando suas chaves". |
| `py` ou `python` não é reconhecido | Reinstale o Python marcando "Add Python to PATH". |
| O agente diz que o clima está indisponível | Falta a `OPENWEATHER_API_KEY` no `.env`. |
| Erros repetidos da OpenAI | Verifique se sua conta tem créditos em platform.openai.com. |
| Acentos aparecendo quebrados | Rode `chcp 65001` no terminal antes de abrir o chat. |
| Quer apagar a memória do chat | Apague a pasta `.sessions`. |
