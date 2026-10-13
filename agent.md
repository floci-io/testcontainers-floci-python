# testcontainers-floci-python

Testcontainers module for [Floci](https://github.com/floci-io) — the open-source local cloud emulators (AWS in `floci.aws`, Azure in `floci.az`).

## Project layout

```
floci/
  core/                # CloudDescriptor, FlociBaseContainer — shared by every cloud
  aws/                 # AWS descriptor, FlociContainer, config/ (one dataclass per AWS service)
  az/                  # AZ descriptor, FlociAzContainer, config/ (one dataclass per Azure service)
  __init__.py          # alias of floci.aws (FlociContainer)
  container.py         # alias of floci.aws.container
  config/              # alias of floci.aws.config
tests/
  images.py            # pinned test images, read from .github/docker-images.txt
  test_container.py    # AWS unit + integration tests
  test_core.py         # core + AWS socket detection
  test_az.py           # Azure unit + integration tests
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
grep -v '^\s*\(#\|$\)' .github/docker-images.txt | xargs -n1 docker pull
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
- **Layout**: `floci/core/` is the cloud-independent part (`CloudDescriptor`, `FlociBaseContainer`: readiness, Docker socket detection, network, namespace, log level, reset). Each cloud is a package on top of it: `floci/aws/` (`container.py` with the `AWS` descriptor and `FlociContainer`, `config/services.py`, `config/top_level.py`) and `floci/az/` (`container.py` with the `AZ` descriptor and `FlociAzContainer`, `config/`). `floci/__init__.py`, `floci/container.py` and `floci/config/` are compatibility aliases of `floci.aws`; keep them re-exporting, never put code there.
- **Dataclasses for config**: AWS service configuration lives in `floci/aws/config/services.py` as `@dataclass` classes, each with an `apply_to(container)` method (and `apply_exposed_ports` when the service publishes ports). Keep them in that file.
- Do not use `os.path`; prefer `pathlib` instead`

## Testing conventions

- Unit tests must not require Docker and must not start a container. They test construction, fluent methods, and config application only.
- Integration tests are marked `@pytest.mark.integration` and use `with FlociContainer() as floci:` as a context manager.
- Use `boto3` in integration tests to verify real AWS API behaviour, and the Azure SDK (`azure-storage-*`, dev dependencies only) for Azure.
- Integration tests run on the pinned images in `.github/docker-images.txt` (`tests/images.py`), never on `latest`.
- Do not mock `DockerContainer` internals — test the public interface of `FlociContainer`.

## Readiness

- `FlociBaseContainer.start()` waits for 200 on the descriptor's health path over HTTP. While
  `<env prefix>TLS_ENABLED` is `true` in the final env (`needs_https_wait()`), it then polls the same path over
  HTTPS with the standard library, certificate unchecked. Reason: the emulators' sniffing TLS proxy accepts
  connections before the HTTPS backend listens, so for a few hundred milliseconds after HTTP health is green TLS
  handshakes end in EOF ("TLS proxy: failed to connect to backend port ...: Connection refused" in the emulator
  log). Seen on floci 2.2.0, floci-az 0.14.0, floci-gcp 0.10.0 and floci-oci 0.4.2. Keep the wait until all four
  pins are free of it.

## Adding a new AWS service

1. Add a `@dataclass` for it in `floci/aws/config/services.py` following the existing pattern.
2. Export it from `floci/aws/config/__init__.py`, and from the `floci/config/` aliases.
3. Add a `with_<service>_config` method to `FlociContainer` in `floci/aws/container.py` that calls
   `self.with_service_config(config)`.
4. If the service spawns sibling containers, add a `SocketService` to the `AWS` descriptor's
   `socket_services` (mockable if the Java config's `requiresDockerSocket()` checks `!mock`).
5. Add a unit test that calls the new method without starting Docker.

## Azure (`floci.az`)

- Ported from Java's `testcontainers-floci-az`; the emulator's `ServicesConfig`
  (`floci-az/src/main/java/io/floci/az/config/EmulatorConfig.java`) is the source of truth for the service list.
- Each service is a dataclass in `floci/az/config/services.py` on `AzServiceConfig` (an `enabled` switch) or
  `AzMockableServiceConfig` (plus `mocked`), with a `TOKEN`; `settings()` returns what is emitted beyond `ENABLED`,
  and only while enabled. Typed settings beyond the switches are added service by service, after Java.
- The mock setting is `MOCKED` on Azure (`MOCK` on AWS); `SocketService.mock_setting` and `mocked_by_default`
  carry that, and `SocketService.spawns` holds a mode-dependent rule (Cosmos engines, SQL data-plane provider).
- Adding an Azure service: the dataclass, `SERVICE_CONFIGS` and `__all__` in `floci/az/config/__init__.py`, a
  `with_<token>_config` method on `FlociAzContainer`, a row in `SERVICES` in `tests/test_az.py`, and a
  `SocketService` in `AZ.socket_services` if it spawns containers.
- Deliberate differences from Java: `PolicyConfig` exists here because the emulator has the service (Java has no
  config for it yet); `TlsConfig.https_port` defaults to `0` (Java: 443), matching the container's default env;
  SQL socket detection also honours the emulator's deprecated `FLOCI_AZ_SERVICES_SQL_MOCKED`.
