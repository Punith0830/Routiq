# Milestone 1 live Coach extension

Version: 0.1. Status: REVIEW. Prepared 2026-10-11.

Human request: include live AI replies in Milestone 1 itself. This proposes a bounded expansion of that milestone, not blanket approval of Milestones 2–5. Existing foundation reports and configuration remain historical and unchanged.

## Confirmed constraints and proposed scope

The human-selected stack remains Python, FastAPI, CrewAI Flow and OpenAI. Supplied JSON v0.2.0 remains proposed configuration, validated by the existing loader. Secrets must never be displayed. Default backend authentication still fails closed.

Proposed extension: live general habit coaching, brief greetings, application help grounded in available configuration, and optional general habit experiments. User-specific progress, streaks, behavior states and recommendations based on actual records remain unavailable because authorized habit services are not implemented. Supplied configuration does not grant these tools access to real data.

No production thresholds, metric rules, retention rules, AI permissions or other TBD_PRODUCT_DECISION items are resolved by this extension. No habit edits, writes, persistence, internet tools, mobile integration or Figma integration are included.

## Architecture and response contract

Notebook -> in-memory FastAPI app with explicitly synthetic identity -> chat service -> CrewAI Flow -> Habit Coach agent -> OpenAI -> application response validator -> existing ChatResponse JSON.

Production /api/v1/ai/chat continues requiring verified backend identity. Notebook test identity stays scoped to its own app instance. Client user IDs are never accepted. HABIT_DETAIL and conversation IDs must return an explicit unavailable response until ownership/persistence services exist; selected records are not sent to OpenAI.

Flow stages: validate input, resolve supported scope, check data availability, generate general coaching where appropriate, validate response, return JSON. Unsupported, medical, ambiguous, unresolved-rule and insufficient-data paths have explicit handling. Mixed questions retain safe supported portions where the bounded router can identify them, otherwise ask clarification. Do not claim comprehensive intent coverage in this extension.

Only Habit Coach is invoked. Progress Analyst and data-backed Recommendation Agent remain deferred. Existing sample-question intent mappings and guardrails inform routing and evaluation; configuration prose is not executed as instructions.

Application controls prohibit tools and database access. Returned insights, behavior evidence and actions remain empty. User-specific metrics and action-success claims are rejected rather than displayed. Output length and schema are validated. Model content is untrusted; validation reduces risk but cannot establish exhaustive semantic safety. This local demonstration is not production approved.

## Settings and notebook experience

Default mode stays offline. A clearly labeled notebook choice enables live mode before messages are sent. Credentials come only from the module-local .env or explicitly configured process environment, never ancestor .env files. Require OPENAI_API_KEY and OPENAI_MODEL; no hidden model substitution. API keys never enter prompts, outputs, exception text or logs. Keep .env excluded from Git.

Explain that live messages leave the computer for OpenAI and may incur API charges before activation. Enabling live mode is a user action, not something the notebook silently does when Run All is clicked. Missing credentials, timeout, authentication, rate limits and provider outages return safe messages without tracebacks or secret-bearing provider payloads. Bound output tokens and retries; no automatic evaluation requests.

Conversation remains stateless across provider requests in this extension. Local displayed history is temporary and can be cleared with /reset; it is not authoritative habit activity. CrewAI memory, tracing, telemetry and tools are disabled. Check local storage and import behavior with blocked network before delivery.

## Files and implementation sequence after approval

1. Add app/config/settings.py, app/ai/flow.py, app/ai/agents/habit_coach.py, app/ai/guardrails.py and app/services/chat_service.py with lazy provider initialization.
2. Adapt app/api/chat.py and app/main.py to accept an explicitly injected Coach service while preserving default fail-closed auth/offline behavior.
3. Update the six-cell chat_llm.ipynb with safe live/offline selection and clear status; retain independent-cell initialization and preserve v0.3.
4. Update .env.example, README.md and extension report; preserve supplied JSON and original inputs.
5. Add mocked unit/API/notebook tests before executing existing regression tests. Report exactly which integrations are mocked.

## Verification and dependencies

Use existing local Python 3.12.14 and CrewAI 1.15.27; no global installs. Verify installed CrewAI/OpenAI interfaces against local source and official documentation before implementing. A model must be explicitly supplied by the user through OPENAI_MODEL; account/model availability is unverified until a separately authorized live request.

Test default offline and missing-secret paths, supported coaching, no-data progress queries, ambiguity/scope/safety handling, attempted instructions to expose secrets or fabricate metrics, rejected habit/context ownership paths, schema validation, provider failures, and no extra agent calls. Run syntax checks, dependency checks and credential-pattern checks. Ensure ordinary network/DNS are blocked in automated tests. Execute CrewAI Flow with a mocked provider; do not represent a mocked adapter as live integration evidence.

No paid provider call is authorized for agent-run verification by this plan alone. A user may explicitly enable the notebook's live mode after implementation; an agent-run real test needs explicit authorization. Until then report live integration as implemented but unverified against OpenAI.

## Approval boundary

Review this exact v0.1 plan for the Milestone 1 live Coach extension. Implementation is pending the human decision. Full Milestones 2–5 and UX gates retain prior limits. This follows the master prompt: "Do not assume that architecture approval automatically authorizes every implementation milestone."

Official credential guidance: https://developers.openai.com/api/reference/overview (accessed 2026-10-11). Keep keys server-side and load them from an environment or key-management service.
