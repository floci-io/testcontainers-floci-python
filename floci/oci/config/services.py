"""Service configuration dataclasses for FlociOciContainer.

One dataclass per service of the OCI emulator, each an enabled switch plus a ``mock``
switch where the emulator has one. ``TOKEN`` is the emulator's name for the service in
``FLOCI_OCI_SERVICES_<TOKEN>_<SETTING>``. ``..._ENABLED`` is always emitted, every other
setting only while the service is enabled. Defaults equal the emulator's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from floci.core import env_value

if TYPE_CHECKING:
    from floci.oci.container import FlociOciContainer

_PREFIX = "FLOCI_OCI_SERVICES_"


@dataclass
class OciServiceConfig:
    """A service of the OCI emulator that can be switched on or off."""

    TOKEN: ClassVar[str]

    enabled: bool = True

    def settings(self) -> dict[str, object]:
        """The settings beyond ``ENABLED``, by setting name; emitted only while enabled."""
        return {}

    def apply_to(self, c: FlociOciContainer) -> None:
        c.with_env(f"{_PREFIX}{self.TOKEN}_ENABLED", env_value(self.enabled))
        if self.enabled:
            for setting, value in self.settings().items():
                c.with_env(f"{_PREFIX}{self.TOKEN}_{setting}", env_value(value))


@dataclass
class OciMockableServiceConfig(OciServiceConfig):
    """A container-backed service; while ``mock`` it spawns no sibling containers."""

    mock: bool = False

    def settings(self) -> dict[str, object]:
        return {"MOCK": self.mock}


@dataclass
class FunctionsConfig(OciMockableServiceConfig):
    """Functions. Invocations run on an Fn Project server sibling container."""

    TOKEN: ClassVar[str] = "FUNCTIONS"


@dataclass
class IdentityConfig(OciServiceConfig):
    """Identity and Access Management."""

    TOKEN: ClassVar[str] = "IDENTITY"


@dataclass
class KmsConfig(OciServiceConfig):
    """Key Management."""

    TOKEN: ClassVar[str] = "KMS"


@dataclass
class ObjectStorageConfig(OciServiceConfig):
    """Object Storage."""

    TOKEN: ClassVar[str] = "OBJECTSTORAGE"


@dataclass
class OkeConfig(OciMockableServiceConfig):
    """Container Engine for Kubernetes. Each cluster is a k3s sibling container."""

    TOKEN: ClassVar[str] = "OKE"


@dataclass
class QueueConfig(OciServiceConfig):
    """Queue."""

    TOKEN: ClassVar[str] = "QUEUE"


@dataclass
class StreamingConfig(OciServiceConfig):
    """Streaming."""

    TOKEN: ClassVar[str] = "STREAMING"


@dataclass
class VaultConfig(OciServiceConfig):
    """Vault and secrets."""

    TOKEN: ClassVar[str] = "VAULT"
