# zte-mc888-ultra-deamon Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.12 (uv-managed "python stable") + uv runtime, gmqtt (mocked client usage), Click CLI, standard logging; telemetry stored in in-memory snapshots with optional on-disk fixtures (001-initialize-boilerplate-hello)
- Python 3.12 (uv-managed) (002-we-have-boilerplate)
- Markdown examples in `docs/discover`; in-memory snapshots (002-we-have-boilerplate)

## Project Structure
```
src/
tests/
```

## Commands
- uv run zte --help
- uv run pytest
- ruff check .
- uvx ruff check .

## Code Style
Python 3.12 (uv-managed "python stable"): Follow standard conventions

## Recent Changes
- 002-we-have-boilerplate: Added Python 3.12 (uv-managed)
- 001-initialize-boilerplate-hello: Documented Python 3.12 uv toolchain with mocked gmqtt + Click CLI hello-world scaffolding

<!-- MANUAL ADDITIONS START -->
Recommended: use `uv run pytest` directly; `pytest` is part of the main
dependencies to simplify CI and local runs without extras.
<!-- MANUAL ADDITIONS END -->
