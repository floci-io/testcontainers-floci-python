from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from floci.container import FlociContainer


def _env(container: FlociContainer, key: str, value: object) -> None:
    container.with_env(key, str(value).lower() if isinstance(value, bool) else str(value))


@dataclass
class TlsConfig:
    enabled: bool = False
    cert_path: str | None = None
    key_path: str | None = None
    self_signed: bool = True

    def apply_to(self, c: FlociContainer) -> None:
        _env(c, "FLOCI_TLS_ENABLED", self.enabled)
        if self.enabled:
            _env(c, "FLOCI_TLS_SELF_SIGNED", self.self_signed)
            if self.cert_path is not None:
                _env(c, "FLOCI_TLS_CERT_PATH", self.cert_path)
            if self.key_path is not None:
                _env(c, "FLOCI_TLS_KEY_PATH", self.key_path)


@dataclass
class StorageConfig:
    host_persistent_path: str | None = None
    prune_volumes_on_delete: bool = True

    def apply_to(self, c: FlociContainer) -> None:
        if self.host_persistent_path is not None:
            _env(c, "FLOCI_STORAGE_HOST_PERSISTENT_PATH", self.host_persistent_path)
        _env(c, "FLOCI_STORAGE_PRUNE_VOLUMES_ON_DELETE", self.prune_volumes_on_delete)
