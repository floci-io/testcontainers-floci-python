# Changelog

## [0.3.0](https://github.com/floci-io/testcontainers-floci-python/compare/0.2.0...v0.3.0) (2026-10-10)


### Features

* shared core with a cloud descriptor; AWS module moves to floci.aws ([#11](https://github.com/floci-io/testcontainers-floci-python/issues/11)) ([cb8119b](https://github.com/floci-io/testcontainers-floci-python/commit/cb8119bba6a0e55db9766f3e3b9ef5903d44ead9))


### Bug Fixes

* remove Floci's sibling containers on stop; advertise a reachable RDS endpoint ([#12](https://github.com/floci-io/testcontainers-floci-python/issues/12)) ([cef0249](https://github.com/floci-io/testcontainers-floci-python/commit/cef0249e2f2bb217db345b9fb84cc289e69b8561))

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
