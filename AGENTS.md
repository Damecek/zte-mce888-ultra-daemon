# zte-mc888-ultra-deamon Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.12 (uv-managed "python stable") + uv runtime, gmqtt (mocked client usage), Click CLI, standard logging; telemetry stored in in-memory snapshots with optional on-disk fixtures (001-initialize-boilerplate-hello)
- Python 3.12 (uv-managed) (002-we-have-boilerplate)
- Markdown examples in `docs/discover`; in-memory snapshots (002-we-have-boilerplate)
- Python 3.12 (uv-managed "python stable") + Click CLI, standard logging, gmqtt (client), pytest, ruff

## Project Structure
```
src/
tests/
```

## Commands
- uv run zte --help
- uv sync --extra dev
- uv run pytest --cov src
- ruff check .
- uvx ruff check .

## Code Style
Python 3.12 (uv-managed "python stable"): Follow standard conventions

## Recent Changes
- 003-we-need-to: Added Python 3.12 (uv-managed "python stable") + Click CLI, standard logging, gmqtt (client), pytest, ruff
- 002-we-have-boilerplate: Added Python 3.12 (uv-managed)

<!-- MANUAL ADDITIONS START -->
Recommended workflow:
1. `uv sync --extra dev` (install tooling extras)
2. `uv run pytest --cov src` (full suite with coverage)
<!-- MANUAL ADDITIONS END -->
