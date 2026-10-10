"""Alias of :mod:`floci.aws.config.top_level`, kept so existing imports keep working."""

from floci.aws.config.top_level import (
    StorageConfig,
    TlsConfig,
)

__all__ = [
    "TlsConfig",
    "StorageConfig",
]
