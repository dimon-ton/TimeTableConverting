# Repository Guidelines

## Project Structure & Module Organization
- `src/` holds core Python packages: `timetable/` (conversion, AI parsing, substitute logic), `utils/` (Sheets sync, daily processing), `web/` (LINE webhook and messaging).
- `tests/` contains pytest suites; `tests/run_tests.py` is the main runner.
- `data/` stores JSON inputs (teachers, levels, real timetables); `scenarios/` holds predefined simulation cases.
- `scripts/` and `tools/` provide utilities and manual test helpers.
- `gas-webapp/` is the Google Apps Script web UI.
- `docs/` contains setup and testing guides.

## Build, Test, and Development Commands
- Setup: `python -m venv venv` then `pip install -r requirements.txt` (add `-r requirements-dev.txt` for testing tools).
- Convert Excel: `python -m src.timetable.converter timetable.xlsm output.json`.
- Run webhook: `python -m src.web.webhook`.
- Daily processing (safe read): `python -m src.utils.daily_leave_processor --test`.
- Run tests: `python tests/run_tests.py` or `pytest tests/ -v`.
- LINE test suite: `python scripts/run_line_tests.py`.
- Test report: `python tests/test_runner_with_report.py` (writes to `test_results/`).

## Coding Style & Naming Conventions
- Python uses 4-space indentation and PEP 8 conventions.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Tests follow `test_*.py` files, `Test*` classes, and `test_*` functions.
- No enforced formatter; avoid broad reformatting unless needed for the change.

## Testing Guidelines
- Pytest settings live in `pytest.ini` (coverage targets `src.web` and `src.timetable.ai_parser`).
- Real-data tests read from `data/`; keep fixtures consistent with JSON schemas.
- For LINE/Sheets integration tests, ensure `.env` and `credentials.json` are configured.

## Commit & Pull Request Guidelines
- Git history favors conventional prefixes like `feat:`, `fix:`, `docs:`, `test:`. Use `type: short summary` when possible.
- PRs should include a clear description, test commands run, and any config/data impacts.
- For `gas-webapp/` UI changes, include screenshots or a short behavior note.

## Security & Configuration Tips
- Do not commit `.env` or `credentials.json`; use `.env.example` for templates.
- Avoid adding sensitive or production data to `data/` or `test_results/`.
