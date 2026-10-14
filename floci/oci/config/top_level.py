from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from floci.core import env_value

if TYPE_CHECKING:
    from floci.oci.container import FlociOciContainer


@dataclass
class TlsConfig:
    """TLS on the emulator port, which then answers both HTTP and HTTPS.

    ``https_port`` is an extra HTTPS port inside the container; ``0`` (the module's default)
    leaves it off, since the emulator's own default, 443, cannot be bound unprivileged.
    """

    enabled: bool = False
    cert_path: str | None = None
    key_path: str | None = None
    self_signed: bool = True
    https_port: int = 0

    def apply_to(self, c: FlociOciContainer) -> None:
        c.with_env("FLOCI_OCI_TLS_ENABLED", env_value(self.enabled))
        if self.enabled:
            c.with_env("FLOCI_OCI_TLS_SELF_SIGNED", env_value(self.self_signed))
            if self.cert_path is not None:
                c.with_env("FLOCI_OCI_TLS_CERT_PATH", self.cert_path)
            if self.key_path is not None:
                c.with_env("FLOCI_OCI_TLS_KEY_PATH", self.key_path)
            c.with_env("FLOCI_OCI_TLS_HTTPS_PORT", env_value(self.https_port))
