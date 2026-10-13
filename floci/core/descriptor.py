"""The facts that tell one Floci emulator apart from another, as data."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Optional

Setting = Callable[[str], Optional[str]]
"""Reads one setting of a service from the env, e.g. ``setting("MOCKED")``; ``None`` if unset."""


@dataclass(frozen=True)
class SocketService:
    """A service that spawns sibling containers and therefore needs the host Docker socket.

    ``token`` is the SCREAMING_SNAKE service name in ``<prefix>SERVICES_<token>_ENABLED``.
    A ``mockable`` service spawns nothing while ``<prefix>SERVICES_<token>_<mock_setting>`` is
    ``true``; while that setting is unset the emulator's default, ``mocked_by_default``, counts.
    ``spawns`` narrows it further for a service whose need depends on a mode: it gets a reader
    of the service's settings and says whether the service, enabled and not mocked, spawns
    containers.
    """

    token: str
    mockable: bool = False
    mock_setting: str = "MOCK"
    mocked_by_default: bool = False
    spawns: Callable[[Setting], bool] | None = None


@dataclass(frozen=True)
class HostSetting:
    """A service setting that must name a host the test process can reach.

    Such as the AWS RDS endpoint host: when the service is enabled and the setting is unset,
    the container sets it to the Docker host at start.
    """

    token: str
    setting: str


NAMESPACE_LABEL = "floci_namespace"
"""Label every Floci emulator puts on the siblings it spawns, holding its namespace."""


@dataclass(frozen=True)
class CloudDescriptor:
    """Everything the shared container needs to run one Floci emulator.

    A cloud module (``floci.aws``, later ``floci.az``, ``floci.gcp``, ``floci.oci``) is this
    descriptor plus its own service configs and connection helpers.
    """

    name: str
    """Short cloud name, e.g. ``aws``."""

    image: str
    """Docker image without tag, e.g. ``floci/floci``."""

    port: int
    """The emulator's single edge port."""

    env_prefix: str
    """Prefix of every setting, e.g. ``FLOCI_`` or ``FLOCI_AZ_``."""

    health_path: str
    """HTTP path that answers 200 once the emulator is ready."""

    reset_path: str | None
    """HTTP path that wipes all emulator state on POST, or ``None`` if the cloud has none."""

    log_level_env: str
    """Env var that sets the emulator's log level."""

    socket_services: tuple[SocketService, ...] = ()
    """Services that need the host Docker socket (see :class:`SocketService`)."""

    default_env: Mapping[str, str] = field(default_factory=dict)
    """Settings every container of this cloud needs, applied first so callers can override them."""

    host_settings: tuple[HostSetting, ...] = ()
    """Settings pointed at the Docker host at start, unless set or their service is disabled.

    Last, so it does not shift the positions of the fields before it.
    """

    @property
    def network_env(self) -> str:
        """Env var naming the Docker network sibling containers join."""
        return f"{self.env_prefix}SERVICES_DOCKER_NETWORK"

    @property
    def resource_namespace_env(self) -> str:
        """Env var that prefixes sibling container names, keeping parallel runs apart."""
        return f"{self.env_prefix}DOCKER_RESOURCE_NAMESPACE"

    @property
    def tls_enabled_env(self) -> str:
        """Env var that turns on TLS; the emulator port then answers both HTTP and HTTPS."""
        return f"{self.env_prefix}TLS_ENABLED"

    def tls_enabled(self, env: Mapping[str, str]) -> bool:
        """Whether TLS is on in ``env``; a missing key means off, which is Floci's default."""
        return env.get(self.tls_enabled_env, "").lower() == "true"

    def service_env(self, token: str, setting: str) -> str:
        """Env var of one service setting, e.g. ``service_env("SQS", "ENABLED")``."""
        return f"{self.env_prefix}SERVICES_{token}_{setting}"

    def service_enabled(self, env: Mapping[str, str], token: str) -> bool:
        """Whether a service is enabled in ``env``; a missing ``_ENABLED`` key means enabled."""
        enabled = env.get(self.service_env(token, "ENABLED"))
        return enabled is None or enabled.lower() == "true"

    def docker_socket_required(self, env: Mapping[str, str]) -> bool:
        """Whether any enabled, non-mocked socket service in ``env`` spawns sibling containers.

        A missing ``_ENABLED`` key means enabled, which is Floci's default.
        """
        for svc in self.socket_services:
            if not self.service_enabled(env, svc.token):
                continue
            if svc.mockable:
                mocked = env.get(self.service_env(svc.token, svc.mock_setting))
                if svc.mocked_by_default if mocked is None else mocked.lower() == "true":
                    continue
            if svc.spawns is not None and not svc.spawns(self._setting_reader(env, svc.token)):
                continue
            return True
        return False

    def _setting_reader(self, env: Mapping[str, str], token: str) -> Setting:
        def read(setting: str) -> str | None:
            return env.get(self.service_env(token, setting))

        return read
