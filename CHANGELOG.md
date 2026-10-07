# Changelog

## 0.2.0 (2026-10-07)

First release from `main`. 0.1.1 was cut from the retired `release/0.1.x` branch and predates
everything below.

### Features

* add the missing service configs `BackupConfig`, `Route53Config`, `TextractConfig` and
  `TransferFamilyConfig`, plus `TlsConfig`, `StorageConfig` and `with_log_level()` ([#1](https://github.com/floci-io/testcontainers-floci-python/issues/1))
* add `with_access_key()` and `with_secret_key()` setters ([#1](https://github.com/floci-io/testcontainers-floci-python/issues/1))

### Bug Fixes

* `with_dedicated_network()` now creates the Docker network it promises ([#1](https://github.com/floci-io/testcontainers-floci-python/issues/1))
* service ports are exposed in one place, so a config's ports are exposed exactly once ([#1](https://github.com/floci-io/testcontainers-floci-python/issues/1))

### Other

* `LICENSE`, `CODE_OF_CONDUCT.md`, `SECURITY.md` and a standardized README ([#2](https://github.com/floci-io/testcontainers-floci-python/issues/2), [#5](https://github.com/floci-io/testcontainers-floci-python/issues/5))
* CI integration tests run again (`pytest-timeout`) and install from `uv.lock` ([#6](https://github.com/floci-io/testcontainers-floci-python/issues/6), [#7](https://github.com/floci-io/testcontainers-floci-python/issues/7))
