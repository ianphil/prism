# CLAUDE.md

## Project

PRISM - Python 3.11, managed exclusively with `uv`.

## Structure

- `prism/` — main package
- `tests/` — tests mirroring `prism/` layout
- `configs/` — YAML configuration files

## uv Rules (Strict)

- **Never** use `pip`, `pip install`, `python -m pip`, or `conda`. Always use `uv`.
- Add dependencies: `uv add <package>`
- Add dev dependencies: `uv add --dev <package>`
- Remove dependencies: `uv remove <package>`
- Run scripts: `uv run python <script>`
- Run tools (pytest, ruff, etc.): `uv run <tool>`
- Sync environment: `uv sync`
- Do not manually edit `pyproject.toml` dependency arrays; use `uv add`/`uv remove`.
- Do not create or modify `requirements.txt` files. `uv.lock` is the lockfile.

## Python Practices

- Target Python 3.11+. Use modern syntax (match statements, `type` aliases, `|` unions).
- Max line length: 88 (enforced by black and flake8).
- Use `pathlib.Path` over `os.path`.
- Use f-strings over `.format()` or `%`.
- Type-annotate all public function signatures.
- Prefer dataclasses or Pydantic models over raw dicts for structured data.
- Use `async`/`await` for I/O-bound operations.

## Testing

- Framework: pytest (`uv run pytest`)
- Place tests in `tests/` mirroring `prism/` package structure.
- Name test files `test_<module>.py`.

## Linting & Formatting

- Linter: ruff (`uv run ruff check .`), flake8 (`uv run flake8 .`)
- Formatter: ruff (`uv run ruff format .`), black (`uv run black .`)
- Run all checks: `uv run ruff check . && uv run flake8 . && uv run black --check .`
