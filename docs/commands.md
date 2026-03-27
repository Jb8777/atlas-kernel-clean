# atlas-kernel-clean — Commands

All commands assume you are in the repo root with the virtual environment activated.

## Start the API server

```bash
uvicorn main:app --reload --port 8000
```

## Health check

```bash
curl http://127.0.0.1:8000/v1/health
```

Expected response:

```json
{"status": "ok", "service": "AtlasKernel", "env": "development"}
```

## Route a prompt via the API

```bash
curl -X POST http://127.0.0.1:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"text": "debug this fastapi endpoint"}'
```

The response includes three sections:

- `routing` — route classification (code / research / ops / general), rationale, and timestamp
- `execution` — the execution plan: action name and next steps
- `result` — the actual output from the LLM or tool

Example response:

```json
{
  "routing": {
    "input": "debug this fastapi endpoint",
    "route": "code",
    "rationale": "Detected software engineering keywords.",
    "timestamp_utc": "2026-03-27T00:00:00+00:00"
  },
  "execution": {
    "route": "code",
    "action": "llm_code",
    "next_steps": ["Execute llm_code with provided input", "Return structured result to caller"]
  },
  "result": {
    "status": "success",
    "output": "...",
    "action": "llm_code"
  }
}
```

## Route a prompt via the CLI

```bash
python cli.py "debug this fastapi endpoint"
```

Same pipeline as the API, output printed as formatted JSON to stdout.

More examples:

```bash
python cli.py "research the latest papers on LLM routing"
python cli.py "fetch http://example.com"
python cli.py "run ls"
python cli.py "what is kubernetes"
```

## Run tests

```bash
pytest
```

With verbosity:

```bash
pytest -v
```

## Force a specific LLM backend

Set the `LLM_BACKEND` environment variable before running:

```bash
LLM_BACKEND=local python cli.py "refactor this function"
LLM_BACKEND=gemini python cli.py "analyze this architecture"
LLM_BACKEND=openrouter python cli.py "summarize this research"
LLM_BACKEND=fallback python cli.py "any prompt"
```

## Override Ollama settings

```bash
OLLAMA_HOST=http://localhost:11434 OLLAMA_MODEL=mistral python cli.py "refactor this code"
```
