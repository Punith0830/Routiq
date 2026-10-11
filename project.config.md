# Routiq project configuration

- Project name: Routiq
- Project root: `projects/routiq/`, relative to the UX Agent Orchestration workspace.
- Original source location: `input/` within this project.
- Derived artifact location: `output/` within this project, using stages 01–08.
- Shared project memory: `project-memory/` within this project.
- Canonical runtime and approval record: `project.state.md`.
- Historical approval provenance: `project-memory/project-state.md`, retained unchanged.
- Project documentation: `docs/README.md`.
- Human-selected design system: `input/designs/DESIGN-figma.md` (SRC-002); use as the design reference when prototype/application design begins, preserving source limitations and approved product scope.
- Isolated skill-validation assets: `tests/` within this project, only when explicitly requested.
- Shared workflow authorities: workspace-root `AGENTS.md`, `agents/`, `skills/`, `phases/` and `gates/`.

Data paths in shared workflow instructions resolve against this Routiq root when working on Routiq. Authority paths resolve against the workspace root. Keep Routiq sources, artifacts, memory, IDs and approval records separate from other projects. This configuration does not change existing project scope or approval status.

## Workflow

- Orchestrator: `../../AGENTS.md`; agent definitions: `../../agents`; task skills: `../../skills`; shared standards: `../../skills/shared/ux-skill-standards.md`.
- Supported phases: Empathize, Define, Ideate, Prototype, Test, defined under `../../phases`.
- Human review gates: Gates 01–08, defined under `../../gates`. Separate screen-inventory and pre-session test-plan reviews remain required.

## Constraints

- BRD requirements and proposed user groups are not validated participant findings. Secondary sources have population and applicability limits.
- Requirements-led hypotheses remain provisional; missing product, permission, privacy, metric, and technical rules cannot be invented.
- Human gate decisions apply only to reviewed versions and approved scope. Approval does not establish validation.
- Do not create unsupported claims, phases, gates, agents, skills, or requirements.

## Canonical paths

- Input folder: `input`; outputs: `output/01-project`, `output/02-research`, `output/03-analysis`, `output/04-strategy`, `output/05-architecture`, `output/06-prototype`, `output/07-testing`, `output/08-iteration`.
- Review packages reside in their stage output folders; historical decisions reside in `project-memory/project-state.md`, with current routing and subsequent decisions in `project.state.md`.

## Configuration governance

- This file is stable configuration, not runtime status. Change it only when the user explicitly changes scope, workflow structure, constraints, or canonical paths.
- Read this file and `project.state.md` at the start of every Routiq run. Update runtime state after actual workflow events; do not treat memory as research evidence.
- Stop affected routing and request clarification if configuration and runtime state conflict.
