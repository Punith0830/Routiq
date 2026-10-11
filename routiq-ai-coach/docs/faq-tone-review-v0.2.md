# FAQ tone revision v0.2 — 2026-10-11

Human approved the proposed polite tone and asked to update the chatbot. Compared OctaKidz notebook embedded FAQ and friendly fallback wording as data only; no notebook code executed or business content copied.

Reviewed 255 Routiq entries, revised 182 answers and retained 73 already suitable answers. Added contextual courtesies, welcoming acknowledgements, softer wording and plain-language explanations for unresolved rules. Medical and fabricated-data responses retain clear limits without repetitive thanks. Questions, categories, IDs, intent mappings and original config hash are unchanged. Original technical product-decision labels remain in archived v0.1 and the original configuration; they are not approvals.

Updated local tracker built-in replies as well as the shared JSON and embedded offline demo. Supported Today summaries still calculate authoritative records; chat cannot modify habits. Standalone demo/notebook-specific answer context is preserved; this change does not connect the FAQ to live generative notebook calls or change approved AI orchestration.

Files: app/config/routiq_faq.json v0.2; demo/Routiq-Coach-Demo.html; sibling backend/app/coach.py. Previous FAQ and demo preserved in docs/revisions. faq-tone-changes-v0.2.json records every changed answer. Reusable one-time editorial script refuses to run again after revision.

Validation passed: JSON Schema, 255 IDs/questions/intents unchanged, original source SHA-256 unchanged, embedded demo dataset equals revised FAQ, no technical TBD token in user-facing FAQ answers. All 25 backend tests passed, including all 255 questions, authorization boundaries and verified metrics; one existing TestClient/httpx deprecation warning remains. Real browser verified Thanks -> You’re welcome and create-habit -> Happy to help. Screenshot: sibling docs/coach-polite-tone-preview.png. Local backend restarted on port 8001 and application remains on port 4200. No paid provider calls or habit-record modifications. Editorial change is authorized; unresolved product policies and formal UX gates remain unchanged.
