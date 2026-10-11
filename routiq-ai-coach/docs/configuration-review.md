# Configuration contract v0.1

Status: structural adapter implemented for Milestone 1; behavior remains proposed.

The supplied v0.2.0 JSON is stored byte-for-byte at `app/config/routiq_chatbot.json`. SHA-256: `9BA2027729A85E1821F806E3FB6CFC74FEF1AB95427CBFAB402C6FC288FE0F15`. Source instructions are data, not executable policy. No detection-rule expression is evaluated.

The loader validates the actual document vocabulary: `product` (partial counterpart to coach), `behavior_states`, `contextual_question_intents` and intent-level handler/tool declarations. It does not pretend the document contains the master prompt's absent formal `response_schema` or separate `intent_routing` section. A strict, proposed API schema lives in `app/schemas/chat.py`; it uses plural `intents` and structured suggested questions. The source's differing singular example remains unchanged. This API contract requires client review before integration.

Checks include required sections and nested fields, registry allowlists, unique identifiers, duplicate JSON keys, normalized duplicate question text, counts, reciprocal question indices, registered state names, intent/handler/tool/context references, offline policy and enabled read-only guardrails. Invalid configuration stops startup; errors report field locations without echoing values. These checks validate structure and references, not the truth of intent labels or enforceability of agent behavior.

Known semantic limitations retained for later milestones:

- Q-079, Q-080, Q-103 and Q-170 ask for comparisons under other intent labels; review before using these as classification ground truth.
- Personalized streak, reminder, returning-user and consistency routes lack complete conditional retrieval contracts. Q-151 requires previous recommendation context. Four declared tools are not explicitly routed.
- Q-200 can overlap insufficient-data and fabricated-data handling.
- Flow source orders behavior detection before retrieval. Proposed implementation will authorize and fetch evidence first, then detect behavior.
- BEH-001–006 thresholds remain `TBD_PRODUCT_DECISION`; BEH-007–008 still depend on approved schedule/day/status rules. All eight states can coexist.
- Confidence thresholds remain `TBD_EVALUATION`. Source questions are anticipated test utterances, not validated research or a trained classifier.

No semantic routing, state detection, agent execution or metrics are enabled in Milestone 1. Configuration changes cannot enable live AI in this foundation.
