# atlas-kernel-clean — Troubleshooting

## API route failures

### `POST /v1/route` returns HTTP 422

Pydantic validation failure. The most common cause is an empty or missing `text` field.

Check:
- The request body is valid JSON
- `text` is present and non-empty (min_length=1 is enforced)

```bash
curl -X POST http://127.0.0.1:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"text": "your prompt here"}'
```

### `POST /v1/route` returns HTTP 500

An internal routing or execution error occurred. Check the application logs in the `logs/` directory for details.

Common causes:
- LLM backend unreachable (cascades to fallback — should not 500 in most cases)
- Unexpected exception in executor (check traceback in logs)

---

## Missing OPENROUTER_API_KEY

### Symptom

Result contains:

```json
{"status": "error", "output": "OPENROUTER_API_KEY is not set"}
```

Or the fallback stub message:

```
[FALLBACK] No LLM backend is available...
```

### Fix

Set the key in your `.env` file:

```
OPENROUTER_API_KEY=sk-or-your-key-here
```

Or as a shell environment variable:

```bash
export OPENROUTER_API_KEY=sk-or-your-key-here
```

---

## Ollama not running

### Symptom

When `LLM_BACKEND=local` is set, or when a code/debug task is routed to the local backend, the result contains:

```
ERROR: Local LLM unavailable: ...
```

The system will cascade to OpenRouter, then to the fallback stub.

### Fix

Start Ollama:

```bash
ollama serve
```

Ensure the model is pulled:

```bash
ollama pull codellama
```

Verify the host/model match your env vars (defaults: `http://localhost:11434`, model `codellama`):

```bash
OLLAMA_HOST=http://localhost:11434 OLLAMA_MODEL=codellama python cli.py "debug this"
```

---

## Gemini CLI unavailable

### Symptom

When `LLM_BACKEND=gemini` is set, or when an analyze/audit/review task is routed to Gemini, the result contains:

```
ERROR: Gemini CLI not found on PATH
```

The system will cascade to OpenRouter, then to the fallback stub.

### Fix

Install the Gemini CLI and ensure it is on your PATH:

```bash
which gemini    # should return a path
gemini --help   # should show usage
```

If the binary name or invocation differs in your installation, the current `_call_gemini()` implementation in `core/llm_client.py` assumes `gemini -p "<prompt>"` — verify this matches your Gemini CLI version.

---

## Shell commands blocked by allowlist

### Symptom

The result contains:

```
BLOCKED: Command not allowed
```

### Explanation

`tools/shell.py` checks the first word of any shell command against a hard-coded allowlist. Only these commands are permitted: `ls`, `pwd`, `whoami`, `date`, `uname`.

Any other command is blocked, regardless of context or intent. This is a safety constraint and is intentional.

### Fix

If you need to run a command that is not on the allowlist, you must edit `tools/shell.py` and add it to `ALLOWED_COMMANDS`. This should be done deliberately and with care.

---

## Config changes not affecting model choice

### Symptom

You have edited the `models` section of `config/model_router.json` to specify different models per route:

```json
{
  "models": {
    "code": "anthropic/claude-3-opus",
    "general": "openai/gpt-3.5-turbo"
  }
}
```

But the model used does not change.

### Explanation

**This is a known config/code drift.** The `models` section in `config/model_router.json` is present but is not consumed by any current implementation. `core/executor.py` calls `call_llm()` without passing a model override, and `core/llm_client.py` defaults to `openai/gpt-3.5-turbo` regardless of route.

The `routing` section (keyword lists) IS consumed and works correctly.

### Workaround

Use the `LLM_BACKEND` env var to force a specific backend, or modify `call_llm()` invocations in `core/executor.py` to pass the desired model name from config.

---

## certifi import error

### Symptom

```
ModuleNotFoundError: No module named 'certifi'
```

### Explanation

`tools/http.py` imports `certifi` for TLS verification, but `certifi` is not listed in `requirements.txt`.

### Fix

```bash
pip install certifi
```

---

## Logs not appearing

### Symptom

No log files are created in `logs/`.

### Fix

Ensure the `logs/` directory exists (it is created automatically on startup if `LOGS_DIR` is set correctly). Check `LOG_LEVEL` in `.env` — set to `DEBUG` for verbose output:

```
LOG_LEVEL=DEBUG
```
