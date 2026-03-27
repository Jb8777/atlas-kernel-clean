# atlas-kernel-clean — Overview

## Purpose

atlas-kernel-clean is an intelligent prompt router and execution engine built with FastAPI. It classifies incoming text into one of four route categories (code, research, ops, general), builds an execution plan, and executes that plan using an appropriate LLM backend or tool (shell, HTTP fetch).

This repo is the production-clean variant of the Atlas Kernel. It is designed for clarity and correctness. The lab variant (atlas-kernel-lab) adds developer scripts and is used for experimentation.

## Key Files and Modules

| File / Directory | Role |
|---|---|
| `main.py` | FastAPI app factory; registers router under `/v1`; sets up logging via lifespan |
| `cli.py` | Command-line entrypoint; drives `route_text → execute_route → run_execution` |
| `api/routes.py` | API route handlers: `GET /v1/health`, `POST /v1/route` |
| `core/router.py` | Heuristic text classifier; returns `RouteResult` with route, rationale, timestamp |
| `core/executor.py` | Execution engine; builds `ExecutionPlan` and runs multi-step logic |
| `core/llm_client.py` | LLM backend dispatcher: local (Ollama), Gemini CLI, OpenRouter, fallback stub |
| `core/llm_router.py` | Backend selector; reads `LLM_BACKEND` env var or uses keyword routing table |
| `core/config_loader.py` | Loads `.env` and `config/model_router.json`; exposes `Settings` and `load_json_config()` |
| `tools/shell.py` | Safe shell executor; allowlist: `ls`, `pwd`, `whoami`, `date`, `uname` |
| `tools/http.py` | HTTP GET fetcher; uses `certifi` for TLS; truncates response to 2000 chars |
| `config/model_router.json` | JSON config: extended routing keywords + per-route model names (models section not yet consumed by code) |
| `.env.example` | Template for environment variables |
| `requirements.txt` | Python dependencies |

## Entrypoints

### API server

```
uvicorn main:app --reload --port 8000
```

Exposes:
- `GET /v1/health` — service health check
- `POST /v1/route` — route and execute a prompt

### CLI

```
python cli.py "<input text>"
```

Runs the same routing and execution pipeline and prints a JSON result to stdout.

## Route Categories

| Route | Trigger keywords (examples) |
|---|---|
| `code` | bug, debug, python, fastapi, api, function, class, refactor, pytest, unit test |
| `research` | research, summarize, compare, paper, sources, citations, explain |
| `ops` | deploy, kubernetes, docker, incident, monitoring, alert, latency; also any URL or run/execute/ls |
| `general` | default when no other keywords match |

Keywords can be extended via the `routing` section of `config/model_router.json`.

## Role in the Wider Stack

atlas-kernel-clean is the stable routing core. Other repos in the family:

- **atlas-kernel-lab** — development variant; adds scripts, `.vscode/`, and `LLM_TIMEOUT_S`
- **ai-agent** — standalone pentest/operator CLI tool
- **JBSEC** — multi-agent security platform; may consume the Atlas routing layer
- **jbsec-core** — minimal FastAPI health service
- **jsbox-docs** — documentation companion repo
