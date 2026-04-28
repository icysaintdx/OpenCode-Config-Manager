# OpenCode Config Manager - Agent Guide

This file is guidance for agentic coding assistants working in this repo.
It summarizes build/lint/test commands and code style conventions observed in the codebase.

## Quick Orientation

- Primary entrypoint: `opencode_config_manager_fluent.py`
- Legacy/backup entrypoint: `opencode_config_manager_fluent_v1.4.5.py`
- Locales: `locales/en_US.json`, `locales/zh_CN.json`
- Build workflow: `.github/workflows/build.yml`
- No Cursor rules found in `.cursor/rules/` or `.cursorrules`
- No Copilot rules found in `.github/copilot-instructions.md`

## Build / Run / Test Commands

### Run Locally (source)

- Install deps: `pip install -r requirements.txt`
- Run app: `python opencode_config_manager_fluent.py`
- Python requirement: 3.8+ (README); CI uses 3.11

### Build (packaging)

- Full, platform-specific build flags live in `.github/workflows/build.yml`
- Windows (CI-style):
  - `pip install PyQt5 PyQt-Fluent-Widgets requests pyinstaller`
  - `pyinstaller --name "OCCM_<TAG>" --onefile --windowed --noconsole --upx-dir . --add-data "assets;assets" --add-data "locales;locales" --hidden-import qfluentwidgets --collect-data qfluentwidgets --exclude-module pytest --icon "assets/icon.ico" --noconfirm --clean opencode_config_manager_fluent.py`
- macOS (CI-style):
  - `pyinstaller --name "OCCM_<TAG>" --onedir --windowed --noconsole --add-data "assets:assets" --add-data "locales:locales" --icon "assets/icon.icns" --hidden-import=qfluentwidgets --collect-data qfluentwidgets --collect-data PyQt5 --strip opencode_config_manager_fluent.py`
- Linux (CI-style):
  - `pyinstaller --name "OCCM_<TAG>" --onedir --windowed --noconsole --add-data "assets:assets" --add-data "locales:locales" --hidden-import=qfluentwidgets --collect-data qfluentwidgets --collect-data PyQt5 --strip opencode_config_manager_fluent.py`

### Tests

- Test deps exist in `requirements.txt`: `pytest`, `hypothesis`
- There is no `tests/` directory today; add one for new tests
- Run all tests: `pytest`
- Run a single file: `pytest tests/path/test_file.py -v`
- Run a single test: `pytest tests/path/test_file.py::test_name -v`
- Run by keyword: `pytest -k "keyword" -v`

### Lint / Format

- No lint/format tool is configured in this repo
- If you add one, document it here and keep it in requirements or a config file

## Code Style Guidelines

### Imports

- Standard library first, then third-party, then local imports
- Keep PyQt5/QFluentWidgets imports grouped together
- Prefer `from pathlib import Path` over `os.path` for file paths
- Avoid duplicate imports (the main file currently has some legacy duplication)

### Formatting

- Follow PEP 8 line length where practical
- Use 4-space indentation
- Prefer parentheses over backslashes for multi-line expressions
- Docstrings use triple double-quotes

### Naming Conventions

- Classes: `CamelCase` (e.g., `ConfigManager`, `MainWindow`)
- Functions/methods: `snake_case`
- Private helpers: prefix with `_` (e.g., `_safe_base_url`)
- Constants: `UPPER_SNAKE_CASE` when truly constant

### Types and Data Structures

- Use `typing` annotations for public methods and shared utilities
- Use `@dataclass` for simple data carriers
- Prefer `Optional[T]` instead of nullable unions for clarity
- Prefer `Path` for filesystem paths and pass `Path` through helpers

### Error Handling

- Use custom exception types for structured failures (see `CLIExportError` family)
- Return structured results for validations (see `ValidationResult`)
- Catch exceptions only where you can provide actionable feedback to users
- For UI-facing errors, surface via dialog or info bar with localized text

### Localization

- UI strings go through `tr("...")` for localization
- When adding a new string key, update both `locales/en_US.json` and `locales/zh_CN.json`
- Keep key naming consistent with existing `common.*`, `provider.*`, `model.*` patterns

### UI and Qt Patterns

- Keep UI widgets encapsulated in page/dialog classes (`BasePage`, `BaseDialog`)
- Avoid heavy work on the UI thread; use threads or `ThreadPoolExecutor` as needed
- Reuse common UI helpers (info bars, dialogs) where possible

### JSON / Config Handling

- Parse JSON defensively; validate types and missing fields
- Preserve user data; keep backup/restore logic intact
- When changing config schema, update validation and migration logic together

### Files and Modules

- The project is currently a single large module; be cautious when splitting files
- If you extract a new module, keep import cycles in mind and update build configs if needed

## Practical Notes for Agents

- Default entrypoint for behavior changes: `opencode_config_manager_fluent.py`
- For translation/UI text, always update locale JSON files
- For build issues, check `.github/workflows/build.yml` for authoritative flags
- Avoid introducing new dependencies without adding them to `requirements.txt`

## If You Add Tests

- Place tests under `tests/`
- Name test files `test_*.py`
- Prefer pure-function tests over UI tests where possible
- For UI logic, isolate validation/transform helpers and test those

## If You Add Linting

- Pick one tool (ruff/flake8/black) and document:
  - Install command
  - Run command
  - Config file location

## If You Add Build/Release Changes

- Keep `.github/workflows/build.yml` in sync with local build commands
- Update `RELEASE.md` if release notes format changes
