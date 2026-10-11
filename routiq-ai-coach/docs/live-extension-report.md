# Milestone 1 live extension delivery

Version 0.1, REVIEW, 2026-10-11. Human APPROVED the exact milestone-1-live-extension-plan.md v0.1. This authorizes the bounded extension, not full Milestones 2–5 or paid agent-run tests.

Implemented lazy LiveSettings, a CrewAI Flow, a single Habit Coach Agent using a bounded OpenAI Responses SDK adapter, safe output validation and an explicitly injected FastAPI service. Default authentication and offline behavior remain fail closed. No data tools, personal habit records, persistence or mutation capabilities are available. Scope matching is conservative; this is not a completed intent/behavior engine.

Notebook v0.4 retains six cells and independent-cell recovery. /live displays a data-transfer/cost notice and requires ENABLE LIVE. Missing credentials leave the existing mode unchanged. /offline and exit disable provider access. Configuration/client/chat remain self-initializing. Prior notebook v0.3 and README preserved in docs/revisions. Empty module .env placeholders created without reading/copying ancestor credentials. No secrets populated by the agent.

Validated: 99 tests, zero failures/errors (live-extension-tests.xml), including real CrewAI Flow/Agent execution with mocked generation, SDK contract with a fake SDK client, mocked notebook round-trip, consent/cancellation, missing credentials, data-dependent source questions, rejected contexts, mixed scope, output guardrails, default auth denial and provider-error redaction. Existing network-blocking harness remained active. pip check passed; app Python syntax compilation passed; bounded key-pattern scan across app/notebook found zero credentials. Source JSON remained unchanged.

Initial provider-failure test caught raw exception text in framework logs. Fixed by sanitizing exceptions and validating output inside the bounded LLM adapter before framework events occur, then reran all tests successfully. Framework console output is suppressed. No actual credentials appeared in this test; the sentinel was synthetic.

Dependency plan remains local Python 3.12.14, CrewAI 1.15.27 and OpenAI SDK 2.54.0. python-dotenv 1.2.4 already existed and is now explicitly declared; no dependencies installed globally or downloaded. Runtime bridge disables AMP auth lookup before CrewAI imports because this pinned release otherwise probes unrelated credential storage. Tracing, telemetry and memory disabled; local framework files go under ignored .coach-runtime. This process-wide bridge is intentionally restricted to a dedicated local Routiq process and must be reevaluated before CrewAI upgrades or deployment.

User-specific metrics/actions/behavior fields stay empty; output validation conservatively rejects numeric output and selected unsupported claims. Semantic defenses are not exhaustive. Model selection is explicit via OPENAI_MODEL, with no fallback; account access and structured-output/model compatibility remain unverified. Real user data permissions, ownership, retention, product thresholds and metric rules remain TBD_PRODUCT_DECISION.

No real OpenAI requests, paid evaluations, live response latency checks, editor UI automation, mobile/Figma integration or production deployment were performed. Live SDK path is implemented and mock-tested, not verified against the provider. User activation can send paid requests only after /live confirmation.

Credential guidance checked against [official OpenAI API overview](https://developers.openai.com/api/reference/overview). Requests set store=False; this does not constitute a promise about all provider retention policies.
