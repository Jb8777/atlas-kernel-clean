# atlas-kernel-clean — Architecture

## High-Level Overview

```
User input (text)
       │
       ▼
 core/router.py          — classify input → RouteResult (route, rationale)
       │
       ▼
 core/executor.py        — build ExecutionPlan → run_execution()
       │
       ├─ ops + URL      → tools/http.py         (HTTP GET)
       ├─ ops + command  → tools/shell.py         (allowlisted shell)
       └─ code/research/
          ops/general    → core/llm_client.py     (LLM backend)
                               │
                    core/llm_router.py             (backend selector)
                               │
               ┌──────────────┼──────────────┐
             local          gemini       openrouter     fallback
           (Ollama)      (Gemini CLI)   (OpenRouter)  (static stub)
```

## Module Descriptions

### `main.py`

FastAPI application factory. Creates the app, registers the `/v1` prefix router from `api/routes.py`, and sets up logging during the lifespan event. The application object is `app` at module level, used by uvicorn.

### `api/routes.py`

Defines two routes under the `/v1` prefix:

- **`GET /v1/health`** — returns `{status, service, env}` from Settings. Safe to call without any LLM backend.
- **`POST /v1/route`** — accepts `{text: string}`, runs `route_text → execute_route → run_execution`, returns `{routing, execution, result}`. Raises HTTP 400 on validation errors, HTTP 500 on execution failures.

### `core/router.py`

Heuristic text classifier. Returns a frozen `RouteResult` dataclass with:
- `input` — the original text
- `route` — one of: `code`, `research`, `ops`, `general`
- `rationale` — human-readable explanation for the route choice
- `timestamp_utc` — ISO 8601 UTC timestamp

**Classification logic (in priority order):**
1. URL detection (`http` / `www` in text) → `ops`
2. Command detection (`run`, `execute`, `ls` in text) → `ops`
3. Code keyword match → `code`
4. Research keyword match → `research`
5. Ops keyword match → `ops`
6. Default → `general`

Keywords can be extended via the `routing` section of `config/model_router.json`. Config load failures silently fall back to built-in keywords — routing never fails due to config issues.

### `core/executor.py`

Execution engine. Two public functions:

**`execute_route(route, input_text) → ExecutionPlan`**
Builds the plan without performing any I/O. Safe to call in tests. For `ops` routes, selects `http_fetch` (URL present) or `run_shell`. For other routes, selects the corresponding `llm_*` action.

**`run_execution(plan, input_text) → dict`**
Full agent execution engine. Supports:

- **Task planning:** if no `then` delimiter is present and the input contains keywords like `analyze`, `audit`, `investigate`, or `review`, the LLM is asked to decompose the task into steps automatically.
- **Multi-step execution:** steps are split on `then`. Each step is independently classified and executed.
- **If/else branching:** steps starting with `if ` are evaluated as natural-language conditions by the LLM; `else` flips the skip mode.
- **Loops:** steps matching `repeat N times <cmd>` execute the inner command N times (capped at 10).
- **Context tracking:** each step's output is stored in a shared context dict (`step_N`, `last_output`, `history`).
- **Error isolation:** individual step failures are caught and recorded; they do not abort the pipeline.
- **Single-step fallback:** inputs without `then` fall through to a direct tool or LLM call.

### `core/llm_client.py`

Dispatches prompts to the configured LLM backend. Public function:

**`call_llm(prompt, *, model, system, temperature, task_type) → str`**

Backend selection (in priority order):
1. `LLM_BACKEND` env var override
2. Keyword routing via `core/llm_router.route_llm()`
3. Default: `openrouter`

On failure, cascades: primary backend → openrouter → offline fallback stub (never raises).

**Backends:**
- `local` — Ollama via HTTP POST to `OLLAMA_HOST/api/generate`
- `gemini` — Gemini CLI subprocess: `gemini -p "<prompt>"`
- `openrouter` — OpenRouter Chat Completions API (requires `OPENROUTER_API_KEY`)
- `fallback` — static stub string; used when all backends are down

### `core/llm_router.py`

Backend selector. Reads `LLM_BACKEND` env var first. Falls back to keyword matching against a routing table:

| Keywords | Backend |
|---|---|
| code, debug, refactor, python, function, class | `local` (Ollama) |
| analyze, audit, investigate, review, compare | `gemini` |
| *(everything else)* | `openrouter` |

### `core/config_loader.py`

Loads environment variables (via `python-dotenv`) and the JSON config file. Exposes:

- `get_settings() → Settings` — cached singleton; reads `APP_ENV`, `APP_NAME`, `LOG_LEVEL`, `CONFIG_PATH`, `LOGS_DIR`
- `load_json_config() → dict` — loads `config/model_router.json`; returns `{}` on any error (missing file, invalid JSON, non-object root)

### `tools/shell.py`

Safe shell executor. Checks the first word of the command against an explicit allowlist before running. Any command not starting with an allowed word is blocked.

**Allowlist:** `ls`, `pwd`, `whoami`, `date`, `uname`

Blocked commands return: `"BLOCKED: Command not allowed"`

Timeout: 10 seconds.

### `tools/http.py`

HTTP GET tool. Fetches the given URL using `requests` with `certifi` TLS verification. Response body is truncated to 2000 characters. Returns the truncated text or an error string.

**Note:** `certifi` is imported but not declared in `requirements.txt`.

## config/model_router.json

The config file has two sections:

### `routing` (consumed by code)
Extended keyword lists that are merged into the router's built-in keywords at runtime:
- `code_keywords`: adds typescript, javascript, golang, rust, lint, mypy, type error
- `research_keywords`: adds literature, survey, review, findings, hypothesis
- `ops_keywords`: adds terraform, helm, ci/cd, pipeline, rollback, slo, sla

### `models` (NOT consumed by code — known drift)
Defines per-route model names:
```json
{
  "code": "openai/gpt-4o",
  "research": "openai/gpt-4o",
  "ops": "openai/gpt-4o",
  "general": "openai/gpt-3.5-turbo"
}
```
**This section is present in config but is not read by any current implementation.** `call_llm` uses a hardcoded default of `openai/gpt-3.5-turbo` regardless of route. Route-specific model selection is not implemented.

## Request Lifecycle

1. Client sends `POST /v1/route` with `{"text": "..."}`
2. `api/routes.py` validates the payload (Pydantic, min_length=1)
3. `core/router.route_text()` classifies the text → `RouteResult`
4. `core/executor.execute_route()` builds the `ExecutionPlan` (no I/O)
5. `core/executor.run_execution()` runs the plan:
   - If `then` in text: multi-step engine
   - If planning keywords present: LLM auto-expands steps, then multi-step engine
   - Otherwise: single-step direct tool or LLM call
6. For LLM steps: `core/llm_client.call_llm()` → `core/llm_router.route_llm()` → backend
7. For shell steps: `tools/shell.py` → allowlist check → subprocess
8. For HTTP steps: `tools/http.py` → requests GET → truncated text
9. Response assembled: `{routing, execution, result}`

## Safety and Constraints

- Shell commands are restricted to a hard-coded allowlist (ls, pwd, whoami, date, uname)
- Loop repetitions are capped at 10
- HTTP responses are truncated at 2000 characters
- LLM backend failures cascade to a static stub (never raises to the caller)
- Config load failures always fall back to `{}` (never break routing)
- All backends time out at 30 seconds
