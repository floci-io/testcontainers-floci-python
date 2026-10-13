"""FlociAzContainer: Testcontainers module for the Floci local Azure emulator."""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any

from floci.az.config.services import (
    AciConfig,
    AcrConfig,
    AksConfig,
    ApimConfig,
    AppConfigConfig,
    ArmConfig,
    BlobConfig,
    ContainerAppsConfig,
    CosmosConfig,
    EmailConfig,
    EntraConfig,
    EventGridConfig,
    EventHubConfig,
    FunctionsConfig,
    GraphConfig,
    KeyVaultConfig,
    ManagedIdentityConfig,
    MariaDbConfig,
    MonitorConfig,
    MySqlConfig,
    NetworkConfig,
    PolicyConfig,
    PostgresConfig,
    QueueConfig,
    RedisConfig,
    ServiceBusConfig,
    SignalRConfig,
    SqlConfig,
    TableConfig,
    VmConfig,
)
from floci.az.config.top_level import TlsConfig
from floci.core import CloudDescriptor, FlociBaseContainer, Setting, SocketService

DEFAULT_IMAGE = "floci/floci-az"
DEFAULT_TAG = "latest"

_COSMOS_CONTAINER_ENGINES = ("MONGODB", "POSTGRESQL", "CASSANDRA", "GREMLIN")


def _is(value: str | None, expected: str) -> bool:
    return value is not None and value.lower() == expected


def _cosmos_spawns(setting: Setting) -> bool:
    """Cosmos starts containers only for its container-backed engines, unless startup is off."""
    if _is(setting("ENGINES_STARTUP"), "disabled"):
        return False
    return any(_is(setting(f"ENGINES_{api}_ENABLED"), "true") for api in _COSMOS_CONTAINER_ENGINES)


def _sql_spawns(setting: Setting) -> bool:
    """SQL starts a SQL Server container only with the ``managed`` data-plane provider.

    Resolved as the emulator does: the provider if set, then the deprecated ``MOCKED`` switch,
    then ``managed`` once the EULA is accepted.
    """
    provider = setting("DATA_PLANE_PROVIDER")
    if provider is not None:
        return provider.lower() == "managed"
    mocked = setting("MOCKED")
    if mocked is not None:
        return mocked.lower() != "true"
    return _is(setting("ACCEPT_EULA"), "y")


def _mockable(token: str, mocked_by_default: bool = False) -> SocketService:
    return SocketService(
        token, mockable=True, mock_setting="MOCKED", mocked_by_default=mocked_by_default
    )


AZ = CloudDescriptor(
    name="az",
    image=DEFAULT_IMAGE,
    port=4577,
    env_prefix="FLOCI_AZ_",
    health_path="/_floci/health",
    reset_path="/_admin/reset",
    log_level_env="QUARKUS_LOG_CATEGORY__IO_FLOCI_AZ__LEVEL",
    # Services that spawn sibling containers, mirroring requiresDockerSocket() in the Java module.
    socket_services=(
        _mockable("ACI", mocked_by_default=True),
        _mockable("ACR"),
        _mockable("AKS"),
        _mockable("CONTAINER_APPS", mocked_by_default=True),
        SocketService("COSMOS", mockable=True, mock_setting="MOCKED", spawns=_cosmos_spawns),
        _mockable("EVENT_HUB"),
        _mockable("FUNCTIONS"),
        _mockable("MARIA_DB"),
        _mockable("MYSQL"),
        _mockable("POSTGRES"),
        _mockable("REDIS"),
        _mockable("SERVICE_BUS", mocked_by_default=True),
        SocketService("SQL", spawns=_sql_spawns),
        _mockable("VM", mocked_by_default=True),
    ),
    default_env={
        # The host and port the emulator reports for its sibling containers must be reachable
        # from the test process, not only from inside the Docker network.
        "FLOCI_AZ_DOCKER_ENDPOINT_MODE": "published",
        # The extra HTTPS port defaults to 443, which an unprivileged container cannot bind.
        "FLOCI_AZ_TLS_HTTPS_PORT": "0",
    },
)


class FlociAzContainer(FlociBaseContainer):
    """Testcontainers wrapper for the Floci local Azure emulator.

    Example::

        with FlociAzContainer() as floci:
            blobs = BlobServiceClient.from_connection_string(
                floci.get_storage_connection_string()
            )

    The host Docker socket is mounted only while an enabled, non-mocked service needs it
    (Functions, AKS, Redis, PostgreSQL, ...); see :meth:`with_docker_socket` to force it
    either way.
    """

    DESCRIPTOR = AZ
    PORT = 4577
    DEFAULT_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000001"
    DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000002"
    DEFAULT_ACCOUNT_NAME = "devstoreaccount1"
    DEFAULT_ACCOUNT_KEY = (
        "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    )
    TLS_CERT_PATH = "/_floci/tls-cert"

    def __init__(self, image: str = f"{DEFAULT_IMAGE}:{DEFAULT_TAG}", **kwargs: Any) -> None:
        super().__init__(image, **kwargs)

    # ------------------------------------------------------------------
    # Connection properties
    # ------------------------------------------------------------------

    def get_https_endpoint(self) -> str:
        """HTTPS base URL, on the same port; it answers once TLS is enabled (:class:`TlsConfig`)."""
        return "https" + self.get_endpoint()[len("http") :]

    def get_tls_certificate(self) -> str:
        """The PEM certificate clients must trust for :meth:`get_https_endpoint`.

        Raises ``RuntimeError`` when the emulator has none, i.e. TLS is not enabled.
        """
        url = self.get_endpoint() + self.TLS_CERT_PATH
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                body: bytes = resp.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"TLS certificate not available (HTTP {exc.code})") from exc
        return body.decode()

    def get_subscription_id(self) -> str:
        """The subscription that always exists in the emulator."""
        return self.DEFAULT_SUBSCRIPTION_ID

    def get_tenant_id(self) -> str:
        """The Entra tenant of the emulator."""
        return self.DEFAULT_TENANT_ID

    def get_account_name(self) -> str:
        """The storage account that always exists (``devstoreaccount1``)."""
        return self.DEFAULT_ACCOUNT_NAME

    def get_account_key(self) -> str:
        """The key of that storage account."""
        return self.DEFAULT_ACCOUNT_KEY

    def get_blob_endpoint(self) -> str:
        return f"{self.get_endpoint()}/{self.get_account_name()}"

    def get_queue_endpoint(self) -> str:
        return f"{self.get_endpoint()}/{self.get_account_name()}-queue"

    def get_table_endpoint(self) -> str:
        return f"{self.get_endpoint()}/{self.get_account_name()}-table"

    def get_storage_connection_string(self) -> str:
        """Connection string for the Azure Storage SDKs (Blob, Queue and Table)."""
        return (
            "DefaultEndpointsProtocol=http"
            f";AccountName={self.get_account_name()}"
            f";AccountKey={self.get_account_key()}"
            f";BlobEndpoint={self.get_blob_endpoint()}"
            f";QueueEndpoint={self.get_queue_endpoint()}"
            f";TableEndpoint={self.get_table_endpoint()}"
            ";"
        )

    # ------------------------------------------------------------------
    # Top-level configuration helpers
    # ------------------------------------------------------------------

    def with_tls_config(self, config: TlsConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    # ------------------------------------------------------------------
    # Service configuration helpers
    # ------------------------------------------------------------------

    def with_aci_config(self, config: AciConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_acr_config(self, config: AcrConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_aks_config(self, config: AksConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_apim_config(self, config: ApimConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_app_config_config(self, config: AppConfigConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_arm_config(self, config: ArmConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_blob_config(self, config: BlobConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_container_apps_config(self, config: ContainerAppsConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_cosmos_config(self, config: CosmosConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_email_config(self, config: EmailConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_entra_config(self, config: EntraConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_event_grid_config(self, config: EventGridConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_event_hub_config(self, config: EventHubConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_functions_config(self, config: FunctionsConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_graph_config(self, config: GraphConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_key_vault_config(self, config: KeyVaultConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_managed_identity_config(self, config: ManagedIdentityConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_maria_db_config(self, config: MariaDbConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_monitor_config(self, config: MonitorConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_mysql_config(self, config: MySqlConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_network_config(self, config: NetworkConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_policy_config(self, config: PolicyConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_postgres_config(self, config: PostgresConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_queue_config(self, config: QueueConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_redis_config(self, config: RedisConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_service_bus_config(self, config: ServiceBusConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_signalr_config(self, config: SignalRConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_sql_config(self, config: SqlConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_table_config(self, config: TableConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self

    def with_vm_config(self, config: VmConfig) -> FlociAzContainer:
        self.with_service_config(config)
        return self
