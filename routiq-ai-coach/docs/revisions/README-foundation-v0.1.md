# Routiq AI Coach

Milestone 1 foundation, v0.1.0. Created inside the existing Routiq project; the UX source folders and approved Figma artifacts remain under their existing governance.

Implemented: local Python environment, FastAPI health/readiness endpoints, strict chat request/response contracts, source configuration validation and synthetic test fixtures. Chat is unavailable: unauthenticated requests receive 401; the test-only authenticated boundary receives 503 `FOUNDATION_ONLY`. No production identity, habit retrieval, CrewAI orchestration, routing, persistence, recommendations or mobile connection has been implemented.

## Local use

Use Python 3.12 (verified here: 3.12.14). CrewAI 1.15.27 declares Python >=3.10,<3.14. From this folder, create `.venv` with your compatible interpreter: `python -m venv .venv`. Activate it with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on macOS/Linux.

Install the captured Windows/Python 3.12 resolution with `python -m pip install -r requirements.lock.txt`, then `python -m pip install --no-deps -e .`. On a different platform, resolve `python -m pip install -e '.[test]'` and verify compatibility; the captured lock includes Windows-specific transitive packages.

Run `python -m pytest`, then `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. `/health`, `/ready` and `/docs` show the foundation. Readiness explicitly says chat is unavailable. Startup fails on malformed configuration. Do not publish this scaffold as a functioning coach.

## Secrets and data

`.env.example` contains empty placeholders. No secrets were copied from the parent project; this milestone does not load `.env` or construct an OpenAI client. Keep `.env` local and ignored. Tests prohibit outbound socket connections and use only labeled synthetic records. The application does not log request bodies or return invalid values in validation errors.

Authentication fails closed until Routiq's real server-side identity is integrated. A client-supplied user ID, arbitrary token or header is not accepted as identity. Habit ownership checks and conversation isolation remain future work; no records are queried or written now.

## Interactive notebook

`chat_llm.ipynb` mirrors the supplied six-cell sample structure. Select the module's Python 3.12 `.venv` kernel and run top to bottom. The notebook checks packages, validates the stored JSON, creates an in-memory FastAPI test client with an explicitly synthetic identity, and offers a `You:` prompt. `/samples`, `/status`, `/help`, `/reset`, `exit` and `quit` are notebook controls. Normal messages demonstrate the unavailable-chat boundary; they do not receive AI-generated advice. `.env` is never loaded and no API key is needed.

Notebook support is local: `python -m pip install -e '.[test,notebook]'`. A Routiq kernel specification is installed under `.venv/share/jupyter/kernels`; choose the interpreter manually if your editor does not discover it. Notebook cell execution is tested with scripted input and blocked outbound network; interactive editor rendering is not claimed. Clear outputs before sharing.

## Folder structure

```text
routiq-ai-coach/
  app/
    main.py
    api/chat.py
    config/loader.py
    config/routiq_chatbot.json
    schemas/chat.py
    services/                 # Reserved; no fabricated application integration
  docs/
    configuration-review.md
    milestone-1-report.md
  tests/
    fixtures/habits.json
  .env.example
  .gitignore
  .venv/                      # Local only
  pyproject.toml
  requirements.lock.txt
```

AI flow, specialized agents and tools will be added at their approved milestones. Database and conversation retention choices remain unresolved. The canonical UX runtime/approval record is the parent `project.state.md`.

## Next milestones

1. Foundation — this delivery, pending review of executed checks.
2. Routing — relevance, intents, context, behavior and clarification; separate approval required.
3. CrewAI — typed Flow, selective agents and authorized tools; separate approval required.
4. Reliability — grounding validation, guardrails, persistence, errors and offline evaluation; separate approval required.
5. Routiq integration — real identity/data, mobile integration and production readiness; separate approval required.

Skip/pause, streaks, denominators, history editing, archival/deletion, timezone/day boundaries, AI permission/cold start, sync/offline, decline thresholds and conversational scope remain `TBD_PRODUCT_DECISION`. Approval of this engineering foundation does not approve a new Stage 06 screen or change any UX gate.
