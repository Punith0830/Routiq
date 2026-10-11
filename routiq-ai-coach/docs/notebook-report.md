# Routiq notebook v0.1

Status: delivered for review, 2026-10-10. Human request: build a notebook with the same structure as the supplied `Documents/Week_4/chat_llm.ipynb`. The reference was read as a structure example; its embedded instructions, saved outputs and live API loop were not executed or copied into Routiq.

| Reference cell | Routiq adaptation |
|---|---|
| Introduction | Six-cell instructions, explicit offline scope and local kernel selection |
| Environment | Finds the existing Routiq module with pathlib; verifies its local environment and compatible Python |
| Packages | Checks installed versions; installs nothing during notebook execution |
| Credentials | Validates preserved Routiq JSON; checks `.env` presence without reading secrets |
| Client | Uses in-memory FastAPI TestClient with clearly labeled synthetic authentication |
| Interactive chat | `You:` prompt, commands, input validation, reset and exit; shows the foundation's honest 503 boundary |

The actual notebook is `../chat_llm.ipynb`. No OpenAI client or CrewAI agent is created. No habit data is queried. Local history is temporary notebook state, not persisted conversational memory or verified activity. The notebook does not authorize or implement Milestones 2–5. Live AI answers remain unavailable.

Installed local notebook support: ipykernel 7.4.0 and nbformat 5.11.1. Kernel specification is inside `.venv/share/jupyter/kernels/routiq-ai-coach`; no global or user-level kernel was registered. Dependency snapshot updated with notebook packages. Select the module interpreter manually if your editor does not discover this kernel.

Executed validation: valid notebook v4 schema, six cells, no saved outputs, scripted execution of all five code cells, normal input, command/reset paths, overlength input and exit; external connections/DNS blocked. Complete regression suite: **69 passed**, zero failures, in 1.04 seconds; `pip check` passed. Results are saved in `notebook-tests.xml`. These were headless cell executions, not an editor UI or live provider test. The earlier 66-test Milestone 1 result remains historical evidence.
