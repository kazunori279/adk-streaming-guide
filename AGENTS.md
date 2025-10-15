# Repository Guidelines

## Project Structure & Module Organization
- `src/part1/`: setup and environment utilities (e.g., `1-3-1_environment_setup.py`).
- `src/part2/`: runnable FastAPI demo (`streaming_app.py`) and notes.
- `src/part3/`: standalone Python examples for streaming patterns.
- `docs/`: narrative guide and architecture memos.
- `.venv/`: local virtual environment (not checked in).

Naming: Python modules use `snake_case` with part-section prefixes (e.g., `3-2-1_...`). Keep examples self-contained within their part directory.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv && source .venv/bin/activate`
- Install minimal deps: `pip install google-adk fastapi uvicorn python-dotenv`
- Env check (Part 1): `python src/part1/1-3-1_environment_setup.py`
- Run demo server (Part 2): `uvicorn src.part2.streaming_app:app --reload --port 8000`
  - Open `http://localhost:8000` and send a message; JSON events stream in the log.
- Optional model/env: `export GOOGLE_API_KEY=... && export ADK_MODEL_NAME=gemini-2.5-flash`

## Coding Style & Naming Conventions
- Python 3.10+, PEP 8, 4-space indentation, type hints encouraged.
- Filenames: `snake_case` with part numbering (e.g., `3-2-1_hello_streaming.py`).
- Keep examples minimal, runnable, and documented inline with a short header.

## Testing Guidelines
- No formal test suite yet. Prefer `pytest` when adding tests.
- Place tests under `tests/` mirroring `src/` (e.g., `tests/part2/test_streaming_app.py`).
- Naming: `test_*.py`, functions `test_*`. Run with `pytest -q`.
- If adding coverage, use `pytest --maxfail=1 -q` (and `--cov=src` if coverage is configured).

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise summary. Optional prefixes (`feat:`, `fix:`, `docs:`, `chore:`) match existing history.
- PRs: clear description, rationale, and scope. Include:
  - What changed and why, any limitations.
  - Repro steps or commands (e.g., how to run the Part 2 server).
  - Linked issues; screenshots for UI changes (web UI at `/`).

## Security & Configuration Tips
- Do not commit secrets. `.env` is ignored; use `GOOGLE_API_KEY` or ADC.
- `src/part1/1-3-1_environment_setup.py` can generate `.env.example`. Copy to `.env` and edit locally.

## Agent-Specific Instructions
- On every new Codex session, scan the sibling repo `../adk-python` to align with the latest ADK APIs.
- Quick checks:
  - `git -C ../adk-python log -n 1 --oneline` (latest change)
  - `rg -n "RunConfig|Runner|LiveRequestQueue" ../adk-python` (API surface changes)
- Update examples accordingly (imports, `RunConfig` params, enums, helpers).
