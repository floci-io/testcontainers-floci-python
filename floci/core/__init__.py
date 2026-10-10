"""Shared core of the Floci Testcontainers modules: a cloud descriptor and one lifecycle."""

from floci.core.container import DOCKER_SOCKET, FlociBaseContainer, ServiceConfig, env_value
from floci.core.descriptor import CloudDescriptor, SocketService

__all__ = [
    "DOCKER_SOCKET",
    "CloudDescriptor",
    "FlociBaseContainer",
    "ServiceConfig",
    "SocketService",
    "env_value",
]
