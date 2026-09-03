# Project

**Read when:** always — this file holds what is true of *this* repo and nowhere else.

The generic rules and the stack conventions are linked from `AGENTS.md`. This file is the
only place for project-specific facts. Keep it to what an agent cannot derive from the code.

## Layout

<!-- Where things live when it differs from the stack default, e.g.
`backend/` FastAPI · `frontend/` React · `_/compose.yml` the dev stack -->

## Running it

<!-- The one command that brings the stack up, and where the per-side commands run
(`docker compose exec api …`). -->

## Environment

<!-- Settings the app needs beyond the stack's defaults, and where they are documented. -->

## Product rules the code enforces

<!-- Domain invariants an agent must not weaken, with the file that owns each. Example:
"Once submitted an application freezes except sections a clarification reopened —
enforced in `services/application/update_section.py`, mirrored (not owned) by the UI." -->

## Deliberate departures from the stack conventions

<!-- Each with a reason. An undocumented departure reads as a mistake to fix. -->
