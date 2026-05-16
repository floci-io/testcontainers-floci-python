# testcontainers-floci-python

Testcontainers module for [Floci](https://github.com/floci-io/floci) — the open-source local AWS emulator.

## Project layout

```
floci/
  __init__.py          # public re-exports (FlociContainer)
  container.py         # FlociContainer — the main class
  config/
    __init__.py        # re-exports all *Config dataclasses
    services.py        # one dataclass per AWS service
tests/
  test_container.py    # unit + integration tests
```

## Setup

```bash
uv sync --extra dev
```

## Running tests

```bash
# Unit tests (no Docker required)
pytest -m "not integration" -v

# Integration tests (Docker required)
docker pull floci/floci:latest
pytest -m integration -v
```

## Lint & type-check

```bash
ruff check .
ruff format .
mypy floci
```

CI runs all three on every PR. Fix lint and type errors before committing.

## Environment

- Always use `uv` for dependency management

## Python practices

- **Target**: Python 3.9+. Use `from __future__ import annotations` at the top of every module so PEP 604 (`X | Y`) and PEP 585 (`list[str]`) syntax works on 3.9.
- **Types**: strict mypy (`strict = true`). All public functions must be fully annotated. Use `Optional[T]` only when the file already does; prefer `T | None` in new code with the future-annotations import.
- **Style**: ruff with `line-length = 100`. Selections: `E`, `F`, `I` (isort), `UP` (pyupgrade). Run `ruff check .` and `ruff format .` before committing.
- **Fluent API**: `FlociContainer` methods return `self` typed as `"FlociContainer"` so callers can chain configuration calls.
- **No bare `except`**: catch specific exception types. Use `Exception` only as a last resort and always bind it (`except Exception as exc`).
- **No mutable default arguments**: use `None` and assign inside the function.
- **Dataclasses for config**: service configuration lives in `floci/config/services.py` as `@dataclass` classes, each with an `apply_to(container)` method. Keep them in that file.
- Do not use `os.path`; prefer `pathlib` instead`

## Testing conventions

- Unit tests must not require Docker and must not start a container. They test construction, fluent methods, and config application only.
- Integration tests are marked `@pytest.mark.integration` and use `with FlociContainer() as floci:` as a context manager.
- Use `boto3` in integration tests to verify real AWS API behaviour.
- Do not mock `DockerContainer` internals — test the public interface of `FlociContainer`.

## Adding a new AWS service

1. Add a `@dataclass` for it in `floci/config/services.py` following the existing pattern.
2. Export it from `floci/config/__init__.py`.
3. Add a `with_<service>_config` method to `FlociContainer` in `floci/container.py`.
4. Add a unit test in `tests/test_container.py` that calls the new method without starting Docker.
