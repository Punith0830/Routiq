# Routiq AI Coach

Milestone 1 foundation plus approved live extension, notebook v0.4. The supplied configuration v0.2.0 is preserved unchanged. Previous foundation reports remain historical.

## Start the notebook

1. Open `chat_llm.ipynb` in the `routiq-ai-coach` folder.
2. Select `.venv (Python 3.12.14)` as its kernel.
3. Open `.env` in this same folder. Fill in `OPENAI_API_KEY` and `OPENAI_MODEL`, using your OpenAI API key and a Responses/structured-output compatible model available to your account. No default model is substituted. Save the file. Never paste the key into chat, code cells or screenshots.
4. Click Restart, then Run All. The notebook starts offline.
5. At `You:`, enter `/live`. Read the notice and enter `ENABLE LIVE` to enable live coaching. This loads only the module-local .env or explicitly configured process environment; it does not use the parent project's .env.
6. Ask `Help me start a reading habit`. Live messages go to OpenAI and may incur charges.
7. Use `/offline` to disable live requests or `exit` to stop. `/help`, `/samples`, `/status` and `/reset` are also available.

The configuration/client/chat cells initialize their own prerequisites. Rerunning the chat cell returns to offline mode. Each provider request is independent; prior messages are not sent. Notebook output can contain typed messages; clear outputs before sharing.

## Implemented boundaries

Live path: notebook -> in-memory FastAPI -> CrewAI Flow -> Habit Coach Agent -> bounded OpenAI SDK request -> response checks -> structured ChatResponse. Only general habit coaching is connected. Greetings and restricted/data-dependent queries have deterministic responses. The scope matcher is deliberately conservative and is not a complete intent classifier.

No personal habits, progress records, streak calculations, behavioral analytics, write tools, database, saved conversations or mobile/Figma integration are connected. No rules are invented for unresolved product decisions. HABIT_DETAIL and conversation IDs remain unavailable pending ownership/persistence services. Insights, actions and behavioral evidence remain empty. Output checks reject numerical or personal-progress claims conservatively, but are not exhaustive semantic safety guarantees.

Production authentication still fails closed. Default `app.main:app` remains offline and denies chat without verified backend identity. The notebook alone overrides identity for its own in-memory demonstration. It is not a deployable authenticated application.

Provider calls use the official OpenAI endpoint, no tools, no stored Responses, a bounded output budget, a request timeout and zero SDK retries. Secrets are not passed to CrewAI prompts. Raw provider errors and invalid generated content are redacted before entering framework events/logs. CrewAI tracing/telemetry/memory are disabled. The version-pinned runtime bridge disables AMP credential lookup before import and directs local framework storage to ignored `.coach-runtime`; this global process setup is only suitable for a dedicated Routiq process.

## Verification

99 automated unit/API/notebook tests passed with external network/DNS blocked. Real CrewAI Flow and Agent execution was tested with mocked OpenAI generation. The SDK parameter contract was tested using a fake client. No paid requests were executed; real model access, billing, provider behavior and live latency are unverified. See `docs/live-extension-report.md` and `docs/live-extension-tests.xml`.

Python 3.12.14 local environment; CrewAI 1.15.27. `python-dotenv` is an explicit existing dependency. No global packages were installed. Run `.venv\Scripts\python.exe -m pytest` on Windows, or `.venv/bin/python -m pytest` on macOS/Linux. The captured requirements lock was resolved on Windows; verify platform-specific dependency compatibility elsewhere.

## Remaining work

The full routing, authorized habit data tools, progress/recommendation agents, persistence, product-rule decisions and production/mobile integration remain under separate Milestones 2-5 approvals. This bounded extension does not approve UX gates, real user-data processing or production deployment. Canonical scope and approvals are in the parent `project.state.md`.
