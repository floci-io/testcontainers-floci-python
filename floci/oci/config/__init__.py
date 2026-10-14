from floci.oci.config.services import (
    FunctionsConfig,
    IdentityConfig,
    KmsConfig,
    ObjectStorageConfig,
    OciMockableServiceConfig,
    OciServiceConfig,
    OkeConfig,
    QueueConfig,
    StreamingConfig,
    VaultConfig,
)
from floci.oci.config.top_level import TlsConfig

SERVICE_CONFIGS: tuple[type[OciServiceConfig], ...] = (
    FunctionsConfig,
    IdentityConfig,
    KmsConfig,
    ObjectStorageConfig,
    OkeConfig,
    QueueConfig,
    StreamingConfig,
    VaultConfig,
)
"""Every service config of the OCI emulator."""

__all__ = [
    "SERVICE_CONFIGS",
    "FunctionsConfig",
    "IdentityConfig",
    "KmsConfig",
    "ObjectStorageConfig",
    "OciMockableServiceConfig",
    "OciServiceConfig",
    "OkeConfig",
    "QueueConfig",
    "StreamingConfig",
    "TlsConfig",
    "VaultConfig",
]
