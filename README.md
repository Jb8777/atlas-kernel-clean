# atlas-kernel-clean

AtlasKernel — intelligent prompt router and executor.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY

# 3. Start the API server
uvicorn main:app --reload --port 8000

# 4. Health check
curl http://127.0.0.1:8000/v1/health

# 5. Route a prompt
curl -X POST http://127.0.0.1:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"text": "debug this fastapi endpoint"}'

# 6. Or use the CLI
python cli.py "debug this fastapi endpoint"
```

## API Routes

| Method | Path | Description |
|---|---|---|
| GET | `/v1/health` | Service health check |
| POST | `/v1/route` | Route and execute a prompt |

## Route Categories

| Route | Examples |
|---|---|
| `code` | bug, debug, python, fastapi, refactor, pytest |
| `research` | research, summarize, compare, explain |
| `ops` | deploy, docker, kubernetes, any URL |
| `general` | everything else |

## LLM Backends

| Backend | Trigger | Requirement |
|---|---|---|
| `local` | code/debug keywords | Ollama running locally |
| `gemini` | analyze/audit keywords | `gemini` CLI on PATH |
| `openrouter` | default | `OPENROUTER_API_KEY` set |
| `fallback` | all backends down | none — static stub response |

Override: `LLM_BACKEND=local|gemini|openrouter|fallback`

## Run Tests

```bash
pytest
```

## Documentation

Additional docs live under `docs/`:

- [docs/overview.md](docs/overview.md) — purpose, key files, entrypoints, role in stack
- [docs/setup.md](docs/setup.md) — prerequisites, install, configure, start, validate
- [docs/commands.md](docs/commands.md) — all confirmed commands with examples
- [docs/architecture.md](docs/architecture.md) — module descriptions, request lifecycle, constraints
- [docs/troubleshooting.md](docs/troubleshooting.md) — failure modes and fixes
