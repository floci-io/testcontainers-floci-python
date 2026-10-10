"""Shared core of the Floci Testcontainers modules: a cloud descriptor and one lifecycle."""

from floci.core.container import DOCKER_SOCKET, FlociBaseContainer, ServiceConfig, env_value
from floci.core.descriptor import NAMESPACE_LABEL, CloudDescriptor, HostSetting, SocketService

__all__ = [
    "DOCKER_SOCKET",
    "NAMESPACE_LABEL",
    "CloudDescriptor",
    "FlociBaseContainer",
    "HostSetting",
    "ServiceConfig",
    "SocketService",
    "env_value",
]
