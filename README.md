# DevOps Voice Assistant

[![CI](https://github.com/karanyadavofficial/devops-voice-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/karanyadavofficial/devops-voice-assistant/actions/workflows/ci.yml)

Talk to your infrastructure. Ask out loud *"How's my CPU doing?"* or *"Which Docker containers are running?"* and get a spoken answer based on **real data** from your machine.

Built with FastAPI, WebSockets, the Gemini Live API and Docker.

## How it works

~~~
Browser (mic + speakers)
   |  WebSocket: raw audio in both directions
FastAPI server (Uvicorn)
   |  Google GenAI SDK: live streaming session
Gemini Live API (speech understanding + voice)
   |  function calling
Allowlisted, read-only tool functions
   (CPU, memory, disk, system info, Docker)
~~~

1. The browser captures microphone audio (16 kHz PCM) and streams it to the server over a WebSocket.
2. The server forwards the audio to Gemini Live and streams Gemini's voice (24 kHz) back to the browser.
3. When a question needs real data, Gemini asks the server to run one of its tool functions. The server runs it and returns the result, and Gemini speaks the answer.

Gemini never runs anything itself. It can only request functions from a fixed allowlist.

## What you can ask

- "How is my CPU and memory?"
- "How much disk space is left?"
- "Tell me about this machine."
- "Which Docker containers are running?"
- "Show me the recent logs of `demo-nginx`."
- "Are any containers stopped?"

## Safety design

The assistant touches real infrastructure, so safety is part of the design:

- **Allowlist:** only functions registered in `tools.py` can be called. Unknown tool names are refused.
- **Read-only:** the Docker tools use only `ps`, `logs` and `stats`. There is no stop, remove or exec.
- **No shell:** commands run as an argument list with `shell=False`, so spoken input can never become a shell command.
- **Input validation:** container names must match a strict pattern. Log lines are capped at 50 and output at 2000 characters.
- **Timeouts:** every Docker command has a 10 second limit.
- **Tested:** a unit test fails if anyone adds a tool to the allowlist without updating it deliberately.
- **Secrets:** the API key lives in `.env`, which is git-ignored and excluded from the Docker image.

**Known trade-off:** the container mounts the Docker socket so it can see other containers. Access to the socket is powerful, so only run this on machines you trust and never expose it to the internet.

## Run with Docker

~~~bash
cp .env.example .env        # then edit .env and add your Gemini API key
docker compose up --build -d
~~~

Open http://localhost:8000/voice, click **Start** and allow the microphone. **Use headphones**, otherwise the assistant hears itself.

Note: on macOS and Windows, Docker runs inside a Linux VM, so CPU and memory numbers describe that VM rather than the whole machine. Run it directly (below) to see your real host numbers.

## Run locally

~~~bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your Gemini API key
uvicorn main:app --reload
~~~

Get a free API key at https://aistudio.google.com.

## Tests and CI

~~~bash
pip install -r requirements-dev.txt
python -m pytest -v
~~~

GitHub Actions runs the tests on every push, then builds the Docker image and checks that the container answers on `/health`.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | FastAPI server and the browser-to-Gemini WebSocket bridge |
| `tools.py` | System tools and the tool allowlist |
| `docker_tools.py` | Read-only Docker tools with input validation |
| `static/` | Browser UI and the microphone audio processor |
| `tests/` | Unit tests |
| `Dockerfile`, `compose.yaml` | Container packaging |
| `.github/workflows/ci.yml` | CI pipeline |

## Roadmap

- Kubernetes tools (read-only pod status)
- Interruption handling, so you can talk over the assistant
- On-screen transcript
- Authentication in front of the assistant
