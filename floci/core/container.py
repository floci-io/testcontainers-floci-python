"""The container lifecycle shared by every Floci emulator module."""

from __future__ import annotations

import urllib.request
import uuid
from typing import Any, ClassVar, Protocol, TypeVar

from testcontainers.core.config import ConnectionMode
from testcontainers.core.container import DockerContainer
from testcontainers.core.docker_client import DockerClient
from testcontainers.core.network import Network
from testcontainers.core.utils import setup_logger
from testcontainers.core.wait_strategies import HttpWaitStrategy

from floci.core.descriptor import NAMESPACE_LABEL, CloudDescriptor

logger = setup_logger(__name__)

DOCKER_SOCKET = "/var/run/docker.sock"

_C = TypeVar("_C", bound="FlociBaseContainer")
"""The concrete container type, so fluent calls keep it (a FlociContainer stays one)."""


class ServiceConfig(Protocol):
    """What a per-service config offers: it writes its env vars, and may expose ports."""

    def apply_to(self, c: Any) -> None: ...


def env_value(value: object) -> str:
    """Format a setting the way Floci expects: booleans as ``true``/``false``."""
    return str(value).lower() if isinstance(value, bool) else str(value)


class FlociBaseContainer(DockerContainer):
    """A Floci emulator container, configured by its cloud's :class:`CloudDescriptor`.

    Owns what every cloud shares: readiness on the health path, Docker socket detection,
    a dedicated network, a unique resource namespace, log level, reset and the endpoint.
    """

    DESCRIPTOR: ClassVar[CloudDescriptor]
    STARTUP_TIMEOUT: ClassVar[int] = 60

    def __init__(self, image: str | None = None, **kwargs: Any) -> None:
        d = self.DESCRIPTOR
        super().__init__(image=image or f"{d.image}:latest", **kwargs)
        self._dedicated_network: str | None = None
        self._docker_socket: bool | None = None
        self.with_exposed_ports(d.port)
        for key, value in d.default_env.items():
            self.with_env(key, value)
        # Sibling containers are named after the resource; a unique namespace per container
        # keeps parallel test runs from colliding and makes leftovers attributable.
        self.with_env(d.resource_namespace_env, f"tc-{uuid.uuid4().hex[:8]}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self: _C) -> _C:
        d = self.DESCRIPTOR
        if self.needs_docker_socket():
            self.with_volume_mapping(DOCKER_SOCKET, DOCKER_SOCKET, "rw")
        self._set_host_settings()
        self.waiting_for(
            HttpWaitStrategy(d.port, d.health_path)
            .for_status_code(200)
            .with_startup_timeout(self.STARTUP_TIMEOUT)
        )
        super().start()
        return self

    def stop(self, force: bool = True, delete_volume: bool = True) -> None:
        """Stop the emulator, then remove the sibling containers it spawned.

        Floci manages the siblings (those labelled with this container's resource namespace) and
        the testcontainers reaper does not track them, so without this they outlive the run; a
        leaked one with a fixed host port, such as the AWS ECR registry, blocks the next run.
        Containers sharing a namespace set with :meth:`with_resource_namespace` lose their
        siblings too.
        """
        namespace = self.env.get(self.DESCRIPTOR.resource_namespace_env)
        super().stop(force=force, delete_volume=delete_volume)
        if namespace:
            _remove_siblings(namespace)

    def _set_host_settings(self) -> None:
        """Point every unset host setting of an enabled service at the Docker host.

        Without it Floci advertises sibling containers' bridge addresses (e.g. RDS endpoints),
        which only a Linux host can reach. Inside a container the bridge address is the
        reachable one, so nothing is set there.
        """
        d = self.DESCRIPTOR
        missing = [
            d.service_env(hs.token, hs.setting)
            for hs in d.host_settings
            if d.service_env(hs.token, hs.setting) not in self.env
            and d.service_enabled(self.env, hs.token)
        ]
        if not missing:
            return
        client = self.get_docker_client()
        if client.get_connection_mode() != ConnectionMode.docker_host:
            return
        host = client.host()
        for key in missing:
            self.with_env(key, host)

    def reset(self) -> None:
        """Wipe all emulator state (buckets, queues, tables, ...) without restarting."""
        path = self.DESCRIPTOR.reset_path
        if path is None:
            raise NotImplementedError(f"the {self.DESCRIPTOR.name} emulator has no state reset")
        request = urllib.request.Request(self.get_endpoint() + path, method="POST")
        with urllib.request.urlopen(request, timeout=30) as resp:
            if not 200 <= resp.status < 300:
                raise RuntimeError(f"state reset failed with HTTP {resp.status}")

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def get_endpoint(self) -> str:
        """Base URL of the emulator, e.g. ``http://localhost:32768``."""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.DESCRIPTOR.port)
        return f"http://{host}:{port}"

    def get_dedicated_network_name(self) -> str | None:
        return self._dedicated_network

    def get_resource_namespace(self) -> str:
        return self.env[self.DESCRIPTOR.resource_namespace_env]

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def with_service_config(self: _C, config: ServiceConfig) -> _C:
        """Apply a service config: its env vars, and its ports if it exposes any."""
        config.apply_to(self)
        apply_ports = getattr(config, "apply_exposed_ports", None)
        if apply_ports is not None:
            apply_ports(self)
        return self

    def with_docker_socket(self: _C, enabled: bool) -> _C:
        """Force the host Docker socket on or off, overriding detection.

        By default it is mounted only while an enabled, non-mocked service spawns sibling
        containers. Pass ``False`` on hosts where the socket cannot be mounted (rootless
        Podman with SELinux, some CI sandboxes), ``True`` to always mount it.
        """
        self._docker_socket = enabled
        return self

    def needs_docker_socket(self) -> bool:
        """Whether :meth:`start` mounts the host Docker socket, from the env as it is now."""
        if self._docker_socket is not None:
            return self._docker_socket
        return self.DESCRIPTOR.docker_socket_required(self.env)

    def with_dedicated_network(self: _C) -> _C:
        """Create an isolated Docker network shared with the containers the emulator spawns."""
        network_name = f"floci-{uuid.uuid4().hex[:8]}"
        self._dedicated_network = network_name
        self.with_network(Network(docker_network_kw={"name": network_name}))
        self.with_env(self.DESCRIPTOR.network_env, network_name)
        return self

    def with_resource_namespace(self: _C, namespace: str) -> _C:
        """Override the generated namespace that prefixes sibling container names."""
        self.with_env(self.DESCRIPTOR.resource_namespace_env, namespace)
        return self

    def with_log_level(self: _C, level: str) -> _C:
        """Set the emulator log level (e.g. DEBUG, INFO, WARN, ERROR)."""
        self.with_env(self.DESCRIPTOR.log_level_env, level)
        return self


def _remove_siblings(namespace: str) -> None:
    """Remove every container labelled with ``namespace``; teardown never fails over leftovers."""
    try:
        client = DockerClient().client
        try:
            for sibling in client.containers.list(
                all=True, filters={"label": f"{NAMESPACE_LABEL}={namespace}"}
            ):
                try:
                    sibling.remove(force=True, v=True)
                except Exception:  # noqa: BLE001 - already gone, or removed concurrently
                    pass
        finally:
            client.close()
    except Exception as exc:  # noqa: BLE001 - best effort during teardown
        logger.debug("could not remove Floci sibling containers: %s", exc)
