"""Service configuration dataclasses for FlociAzContainer.

One dataclass per service of the Azure emulator, each an enabled switch plus a ``mocked``
switch where the emulator has one. ``TOKEN`` is the emulator's name for the service in
``FLOCI_AZ_SERVICES_<TOKEN>_<SETTING>``. ``..._ENABLED`` is always emitted, every other
setting only while the service is enabled. Defaults equal the emulator's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from floci.core import env_value

if TYPE_CHECKING:
    from floci.az.container import FlociAzContainer

_PREFIX = "FLOCI_AZ_SERVICES_"


@dataclass
class AzServiceConfig:
    """A service of the Azure emulator that can be switched on or off."""

    TOKEN: ClassVar[str]

    enabled: bool = True

    def settings(self) -> dict[str, object]:
        """The settings beyond ``ENABLED``, by setting name; emitted only while enabled."""
        return {}

    def apply_to(self, c: FlociAzContainer) -> None:
        c.with_env(f"{_PREFIX}{self.TOKEN}_ENABLED", env_value(self.enabled))
        if self.enabled:
            for setting, value in self.settings().items():
                c.with_env(f"{_PREFIX}{self.TOKEN}_{setting}", env_value(value))


@dataclass
class AzMockableServiceConfig(AzServiceConfig):
    """A container-backed service; while ``mocked`` it spawns no sibling containers."""

    mocked: bool = False

    def settings(self) -> dict[str, object]:
        return {"MOCKED": self.mocked}


@dataclass
class AciConfig(AzMockableServiceConfig):
    """Container Instances. Mocked by default."""

    TOKEN: ClassVar[str] = "ACI"

    mocked: bool = True


@dataclass
class AcrConfig(AzMockableServiceConfig):
    """Container Registry."""

    TOKEN: ClassVar[str] = "ACR"


@dataclass
class AksConfig(AzMockableServiceConfig):
    """Kubernetes Service."""

    TOKEN: ClassVar[str] = "AKS"


@dataclass
class ApimConfig(AzServiceConfig):
    """API Management."""

    TOKEN: ClassVar[str] = "APIM"


@dataclass
class AppConfigConfig(AzServiceConfig):
    """App Configuration."""

    TOKEN: ClassVar[str] = "APP_CONFIG"


@dataclass
class ArmConfig(AzServiceConfig):
    """Resource Manager, the management plane. Disabling it turns off every ARM-based service."""

    TOKEN: ClassVar[str] = "ARM"


@dataclass
class BlobConfig(AzServiceConfig):
    """Blob Storage."""

    TOKEN: ClassVar[str] = "BLOB"


@dataclass
class ContainerAppsConfig(AzMockableServiceConfig):
    """Container Apps. Mocked by default."""

    TOKEN: ClassVar[str] = "CONTAINER_APPS"

    mocked: bool = True


@dataclass
class CosmosConfig(AzMockableServiceConfig):
    """Cosmos DB.

    The NoSQL and Table APIs run inside the emulator. The MongoDB, PostgreSQL, Cassandra and
    Gremlin engines are sibling containers, off by default; ``engine_startup`` says when an
    enabled one starts: ``on-demand``, ``eager`` or ``disabled``.
    """

    TOKEN: ClassVar[str] = "COSMOS"

    engine_startup: str = "on-demand"
    mongodb_enabled: bool = False
    postgresql_enabled: bool = False
    cassandra_enabled: bool = False
    gremlin_enabled: bool = False

    def settings(self) -> dict[str, object]:
        return {
            "MOCKED": self.mocked,
            "ENGINES_STARTUP": self.engine_startup,
            "ENGINES_MONGODB_ENABLED": self.mongodb_enabled,
            "ENGINES_POSTGRESQL_ENABLED": self.postgresql_enabled,
            "ENGINES_CASSANDRA_ENABLED": self.cassandra_enabled,
            "ENGINES_GREMLIN_ENABLED": self.gremlin_enabled,
        }


@dataclass
class EmailConfig(AzServiceConfig):
    """Communication Services Email."""

    TOKEN: ClassVar[str] = "EMAIL"


@dataclass
class EntraConfig(AzServiceConfig):
    """Microsoft Entra ID."""

    TOKEN: ClassVar[str] = "ENTRA"


@dataclass
class EventGridConfig(AzServiceConfig):
    """Event Grid."""

    TOKEN: ClassVar[str] = "EVENT_GRID"


@dataclass
class EventHubConfig(AzMockableServiceConfig):
    """Event Hubs."""

    TOKEN: ClassVar[str] = "EVENT_HUB"


@dataclass
class FunctionsConfig(AzMockableServiceConfig):
    """Functions."""

    TOKEN: ClassVar[str] = "FUNCTIONS"


@dataclass
class GraphConfig(AzServiceConfig):
    """Microsoft Graph."""

    TOKEN: ClassVar[str] = "GRAPH"


@dataclass
class KeyVaultConfig(AzServiceConfig):
    """Key Vault."""

    TOKEN: ClassVar[str] = "KEY_VAULT"


@dataclass
class ManagedIdentityConfig(AzServiceConfig):
    """Managed Identity."""

    TOKEN: ClassVar[str] = "MANAGED_IDENTITY"


@dataclass
class MariaDbConfig(AzMockableServiceConfig):
    """Database for MariaDB."""

    TOKEN: ClassVar[str] = "MARIA_DB"


@dataclass
class MonitorConfig(AzServiceConfig):
    """Monitor."""

    TOKEN: ClassVar[str] = "MONITOR"


@dataclass
class MySqlConfig(AzMockableServiceConfig):
    """Database for MySQL."""

    TOKEN: ClassVar[str] = "MYSQL"


@dataclass
class NetworkConfig(AzServiceConfig):
    """Virtual networks, public IPs, security groups and DNS zones."""

    TOKEN: ClassVar[str] = "NETWORK"


@dataclass
class PolicyConfig(AzServiceConfig):
    """Policy definitions and assignments. In emulator releases after 0.14.0."""

    TOKEN: ClassVar[str] = "POLICY"


@dataclass
class PostgresConfig(AzMockableServiceConfig):
    """Database for PostgreSQL."""

    TOKEN: ClassVar[str] = "POSTGRES"


@dataclass
class QueueConfig(AzServiceConfig):
    """Queue Storage."""

    TOKEN: ClassVar[str] = "QUEUE"


@dataclass
class RedisConfig(AzMockableServiceConfig):
    """Cache for Redis."""

    TOKEN: ClassVar[str] = "REDIS"


@dataclass
class ServiceBusConfig(AzMockableServiceConfig):
    """Service Bus. Mocked by default."""

    TOKEN: ClassVar[str] = "SERVICE_BUS"

    mocked: bool = True


@dataclass
class SignalRConfig(AzServiceConfig):
    """SignalR Service."""

    TOKEN: ClassVar[str] = "SIGNALR"


@dataclass
class SqlConfig(AzServiceConfig):
    """SQL Database.

    ``data_plane_provider`` is ``none`` (control plane only), ``managed`` (a SQL Server sibling
    container per server) or ``external``. Left unset, the emulator uses ``managed`` once
    ``accept_eula`` is ``Y`` (the Microsoft SQL Server EULA) and ``none`` otherwise.
    """

    TOKEN: ClassVar[str] = "SQL"

    data_plane_provider: str | None = None
    accept_eula: str = "N"

    def settings(self) -> dict[str, object]:
        settings: dict[str, object] = {"ACCEPT_EULA": self.accept_eula}
        if self.data_plane_provider is not None:
            settings["DATA_PLANE_PROVIDER"] = self.data_plane_provider.lower()
        return settings


@dataclass
class TableConfig(AzServiceConfig):
    """Table Storage."""

    TOKEN: ClassVar[str] = "TABLE"


@dataclass
class VmConfig(AzMockableServiceConfig):
    """Virtual Machines. Mocked by default."""

    TOKEN: ClassVar[str] = "VM"

    mocked: bool = True
