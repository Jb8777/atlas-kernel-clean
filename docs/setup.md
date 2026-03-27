# atlas-kernel-clean — Setup

## Prerequisites

- Python 3.10+
- pip
- (Optional) Ollama installed and running for local LLM backend
- (Optional) Gemini CLI (`gemini` binary on PATH) for the Gemini backend
- (Optional) OpenRouter API key for the cloud backend

## 1. Clone the repo

```bash
git clone https://github.com/Jb8777/atlas-kernel-clean.git
cd atlas-kernel-clean
```

## 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note:** `tools/http.py` imports `certifi` which is not in `requirements.txt`. If you encounter an import error, install it manually:

```bash
pip install certifi
```

## 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
APP_ENV=development
APP_NAME=AtlasKernel
LOG_LEVEL=INFO
OPENROUTER_API_KEY=sk-or-REPLACE_ME   # required for OpenRouter backend
```

Additional env vars used in code (not in .env.example — set manually if needed):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `codellama` | Ollama model name |
| `LLM_BACKEND` | *(auto)* | Force backend: `local`, `gemini`, `openrouter`, `fallback` |
| `CONFIG_PATH` | `config/model_router.json` | Path to JSON config |
| `LOGS_DIR` | `logs` | Directory for log files |

## 5. Start the API server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

## 6. Validate health

```bash
curl http://127.0.0.1:8000/v1/health
```

Expected response:

```json
{"status": "ok", "service": "AtlasKernel", "env": "development"}
```

## 7. Use the CLI

```bash
python cli.py "debug this fastapi endpoint"
```

The CLI prints a JSON object containing:
- `routing` — the route classification and rationale
- `execution` — the execution plan (action, next steps)
- `result` — the output from the LLM or tool

## 8. Run tests

```bash
pytest
```

Tests are in the `tests/` directory.
