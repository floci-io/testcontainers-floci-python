"""Tests for the Azure module (``floci.az``). The unit tests need no Docker."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

from floci.az import AZ, FlociAzContainer
from floci.az.config import (
    SERVICE_CONFIGS,
    AciConfig,
    AzMockableServiceConfig,
    AzServiceConfig,
    BlobConfig,
    ContainerAppsConfig,
    CosmosConfig,
    PostgresConfig,
    ServiceBusConfig,
    SqlConfig,
    TlsConfig,
    VmConfig,
)
from floci.core import FlociBaseContainer
from tests.https import https_status
from tests.images import AZ_TEST_IMAGE

MOCKED_BY_DEFAULT = {"ACI", "CONTAINER_APPS", "SERVICE_BUS", "VM"}

# Token, has a mock switch, mocked by default: the emulator's ServicesConfig
# (floci-az, config/EmulatorConfig.java). SQL's deprecated mock switch is not modelled.
SERVICES = {
    "ACI": (True, True),
    "ACR": (True, False),
    "AKS": (True, False),
    "APIM": (False, False),
    "APP_CONFIG": (False, False),
    "ARM": (False, False),
    "BLOB": (False, False),
    "CONTAINER_APPS": (True, True),
    "COSMOS": (True, False),
    "EMAIL": (False, False),
    "ENTRA": (False, False),
    "EVENT_GRID": (False, False),
    "EVENT_HUB": (True, False),
    "FUNCTIONS": (True, False),
    "GRAPH": (False, False),
    "KEY_VAULT": (False, False),
    "MANAGED_IDENTITY": (False, False),
    "MARIA_DB": (True, False),
    "MONITOR": (False, False),
    "MYSQL": (True, False),
    "NETWORK": (False, False),
    "POLICY": (False, False),
    "POSTGRES": (True, False),
    "QUEUE": (False, False),
    "REDIS": (True, False),
    "SERVICE_BUS": (True, True),
    "SIGNALR": (False, False),
    "SQL": (False, False),
    "TABLE": (False, False),
    "VM": (True, True),
}


def env_of(config: object) -> dict[str, str]:
    """The env vars a config writes on a fresh container."""
    c = FlociAzContainer()
    before = dict(c.env)
    c.with_service_config(config)  # type: ignore[arg-type]
    return {k: v for k, v in c.env.items() if before.get(k) != v}


def all_disabled() -> FlociAzContainer:
    """A container with every service switched off."""
    c = FlociAzContainer()
    for config in SERVICE_CONFIGS:
        c.with_service_config(config(enabled=False))
    return c


# --- descriptor and defaults ----------------------------------------------------------------


def test_descriptor() -> None:
    assert AZ.name == "az"
    assert AZ.image == "floci/floci-az"
    assert AZ.port == 4577
    assert AZ.env_prefix == "FLOCI_AZ_"
    assert AZ.health_path == "/_floci/health"
    assert AZ.reset_path == "/_admin/reset"
    assert AZ.log_level_env == "QUARKUS_LOG_CATEGORY__IO_FLOCI_AZ__LEVEL"
    assert AZ.network_env == "FLOCI_AZ_SERVICES_DOCKER_NETWORK"
    assert AZ.resource_namespace_env == "FLOCI_AZ_DOCKER_RESOURCE_NAMESPACE"
    assert AZ.host_settings == ()


def test_default_container() -> None:
    c = FlociAzContainer()
    assert isinstance(c, FlociBaseContainer)
    assert c.DESCRIPTOR is AZ
    assert c.image == "floci/floci-az:latest"
    assert {str(port) for port in c.ports} == {"4577"}
    assert c.env == {
        "FLOCI_AZ_DOCKER_ENDPOINT_MODE": "published",
        "FLOCI_AZ_TLS_HTTPS_PORT": "0",
        "FLOCI_AZ_DOCKER_RESOURCE_NAMESPACE": c.get_resource_namespace(),
    }


def test_default_env_can_be_overridden() -> None:
    c = FlociAzContainer().with_env("FLOCI_AZ_DOCKER_ENDPOINT_MODE", "auto")
    assert c.env["FLOCI_AZ_DOCKER_ENDPOINT_MODE"] == "auto"


def test_identity() -> None:
    c = FlociAzContainer()
    assert c.get_subscription_id() == "00000000-0000-0000-0000-000000000001"
    assert c.get_tenant_id() == "00000000-0000-0000-0000-000000000002"
    assert c.get_account_name() == "devstoreaccount1"
    assert c.get_account_key().startswith("Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6")


def test_core_settings_use_the_azure_env_vars() -> None:
    a, b = FlociAzContainer(), FlociAzContainer()
    assert a.get_resource_namespace().startswith("tc-")
    assert a.get_resource_namespace() != b.get_resource_namespace()
    assert a.with_resource_namespace("ci-42").env["FLOCI_AZ_DOCKER_RESOURCE_NAMESPACE"] == "ci-42"
    assert a.with_log_level("DEBUG").env["QUARKUS_LOG_CATEGORY__IO_FLOCI_AZ__LEVEL"] == "DEBUG"
    network = a.with_dedicated_network().get_dedicated_network_name()
    assert network is not None
    assert a.env["FLOCI_AZ_SERVICES_DOCKER_NETWORK"] == network


def test_fluent_methods_keep_the_azure_type() -> None:
    c = FlociAzContainer().with_log_level("INFO").with_blob_config(BlobConfig())
    assert isinstance(c.with_docker_socket(False), FlociAzContainer)


def test_connection_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    c = FlociAzContainer()
    monkeypatch.setattr(c, "get_endpoint", lambda: "http://localhost:32768")
    assert c.get_https_endpoint() == "https://localhost:32768"
    assert c.get_blob_endpoint() == "http://localhost:32768/devstoreaccount1"
    assert c.get_queue_endpoint() == "http://localhost:32768/devstoreaccount1-queue"
    assert c.get_table_endpoint() == "http://localhost:32768/devstoreaccount1-table"
    assert c.get_storage_connection_string() == (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1"
        f";AccountKey={c.get_account_key()}"
        ";BlobEndpoint=http://localhost:32768/devstoreaccount1"
        ";QueueEndpoint=http://localhost:32768/devstoreaccount1-queue"
        ";TableEndpoint=http://localhost:32768/devstoreaccount1-table;"
    )


# --- service configs ------------------------------------------------------------------------


def test_every_emulator_service_has_a_config() -> None:
    assert {config.TOKEN for config in SERVICE_CONFIGS} == set(SERVICES)
    assert len({config.TOKEN for config in SERVICE_CONFIGS}) == len(SERVICE_CONFIGS)


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_mock_switch_and_defaults_match_the_emulator(config: type[AzServiceConfig]) -> None:
    mockable, mocked = SERVICES[config.TOKEN]
    default = config()
    assert default.enabled
    assert issubclass(config, AzMockableServiceConfig) == mockable
    assert getattr(default, "mocked", False) == mocked


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_enabled_is_always_emitted_and_the_rest_only_when_enabled(
    config: type[AzServiceConfig],
) -> None:
    enabled_key = f"FLOCI_AZ_SERVICES_{config.TOKEN}_ENABLED"
    assert env_of(config(enabled=False)) == {enabled_key: "false"}

    env = env_of(config())
    assert env[enabled_key] == "true"
    assert all(key.startswith(f"FLOCI_AZ_SERVICES_{config.TOKEN}_") for key in env)
    if issubclass(config, AzMockableServiceConfig):
        mocked = SERVICES[config.TOKEN][1]
        assert env[f"FLOCI_AZ_SERVICES_{config.TOKEN}_MOCKED"] == str(mocked).lower()
        flipped = env_of(config(mocked=not mocked))
        assert flipped[f"FLOCI_AZ_SERVICES_{config.TOKEN}_MOCKED"] == str(not mocked).lower()


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_every_config_has_a_fluent_method(config: type[AzServiceConfig]) -> None:
    methods = [
        name
        for name in dir(FlociAzContainer)
        if name.startswith("with_") and name.endswith("_config")
    ]
    c = FlociAzContainer()
    matching = [m for m in methods if m == f"with_{config.TOKEN.lower()}_config"]
    assert len(matching) == 1
    assert getattr(c, matching[0])(config(enabled=False)) is c
    assert c.env[f"FLOCI_AZ_SERVICES_{config.TOKEN}_ENABLED"] == "false"


def test_simple_service_emits_only_enabled() -> None:
    assert env_of(BlobConfig()) == {"FLOCI_AZ_SERVICES_BLOB_ENABLED": "true"}


def test_cosmos_settings() -> None:
    assert env_of(CosmosConfig()) == {
        "FLOCI_AZ_SERVICES_COSMOS_ENABLED": "true",
        "FLOCI_AZ_SERVICES_COSMOS_MOCKED": "false",
        "FLOCI_AZ_SERVICES_COSMOS_ENGINES_STARTUP": "on-demand",
        "FLOCI_AZ_SERVICES_COSMOS_ENGINES_MONGODB_ENABLED": "false",
        "FLOCI_AZ_SERVICES_COSMOS_ENGINES_POSTGRESQL_ENABLED": "false",
        "FLOCI_AZ_SERVICES_COSMOS_ENGINES_CASSANDRA_ENABLED": "false",
        "FLOCI_AZ_SERVICES_COSMOS_ENGINES_GREMLIN_ENABLED": "false",
    }
    env = env_of(CosmosConfig(engine_startup="eager", gremlin_enabled=True))
    assert env["FLOCI_AZ_SERVICES_COSMOS_ENGINES_STARTUP"] == "eager"
    assert env["FLOCI_AZ_SERVICES_COSMOS_ENGINES_GREMLIN_ENABLED"] == "true"


def test_sql_settings() -> None:
    assert env_of(SqlConfig()) == {
        "FLOCI_AZ_SERVICES_SQL_ENABLED": "true",
        "FLOCI_AZ_SERVICES_SQL_ACCEPT_EULA": "N",
    }
    env = env_of(SqlConfig(data_plane_provider="MANAGED", accept_eula="Y"))
    assert env["FLOCI_AZ_SERVICES_SQL_DATA_PLANE_PROVIDER"] == "managed"
    assert env["FLOCI_AZ_SERVICES_SQL_ACCEPT_EULA"] == "Y"


def test_tls_config() -> None:
    c = FlociAzContainer()
    c.with_tls_config(TlsConfig())
    assert c.env["FLOCI_AZ_TLS_ENABLED"] == "false"
    assert "FLOCI_AZ_TLS_SELF_SIGNED" not in c.env

    c.with_tls_config(
        TlsConfig(enabled=True, cert_path="/certs/tls.crt", key_path="/certs/tls.key")
    )
    assert c.env["FLOCI_AZ_TLS_ENABLED"] == "true"
    assert c.env["FLOCI_AZ_TLS_SELF_SIGNED"] == "true"
    assert c.env["FLOCI_AZ_TLS_CERT_PATH"] == "/certs/tls.crt"
    assert c.env["FLOCI_AZ_TLS_KEY_PATH"] == "/certs/tls.key"
    assert c.env["FLOCI_AZ_TLS_HTTPS_PORT"] == "0"


def test_https_wait_only_while_tls_is_enabled() -> None:
    assert AZ.tls_enabled_env == "FLOCI_AZ_TLS_ENABLED"
    c = FlociAzContainer()
    assert not c.needs_https_wait()
    assert c.with_tls_config(TlsConfig(enabled=True)).needs_https_wait()
    assert not c.with_tls_config(TlsConfig()).needs_https_wait()
    assert c.with_env("FLOCI_AZ_TLS_ENABLED", "true").needs_https_wait()


def test_configs_can_be_applied_repeatedly() -> None:
    c = FlociAzContainer()
    c.with_postgres_config(PostgresConfig(mocked=True))
    c.with_postgres_config(PostgresConfig(mocked=True))
    c.with_postgres_config(PostgresConfig())
    assert c.env["FLOCI_AZ_SERVICES_POSTGRES_MOCKED"] == "false"


# --- Docker socket detection ----------------------------------------------------------------


def test_socket_table_matches_the_service_configs() -> None:
    by_token = {config.TOKEN: config for config in SERVICE_CONFIGS}
    table = {svc.token: svc for svc in AZ.socket_services}
    assert len(table) == len(AZ.socket_services)
    assert set(table) <= set(by_token)
    # Every service with a mock switch spawns containers, and SQL does by its provider.
    mockable = {t for t, c in by_token.items() if issubclass(c, AzMockableServiceConfig)}
    assert set(table) == mockable | {"SQL"}
    for token, svc in table.items():
        assert svc.mockable == (token in mockable)
        if svc.mockable:
            assert svc.mock_setting == "MOCKED"
            default = by_token[token]()
            assert isinstance(default, AzMockableServiceConfig)
            assert svc.mocked_by_default == default.mocked
    assert {t for t, svc in table.items() if svc.mocked_by_default} == MOCKED_BY_DEFAULT
    assert {t for t, svc in table.items() if svc.spawns is not None} == {"COSMOS", "SQL"}


def test_services_that_need_the_socket_by_default() -> None:
    # One service enabled at a time, with the emulator's defaults for everything else.
    needing = {
        svc.token
        for svc in AZ.socket_services
        if all_disabled()
        .with_env(AZ.service_env(svc.token, "ENABLED"), "true")
        .needs_docker_socket()
    }
    assert needing == {
        "ACR",
        "AKS",
        "EVENT_HUB",
        "FUNCTIONS",
        "MARIA_DB",
        "MYSQL",
        "POSTGRES",
        "REDIS",
    }


def test_default_container_needs_the_socket() -> None:
    assert FlociAzContainer().needs_docker_socket()


def test_no_socket_with_every_service_disabled() -> None:
    assert not all_disabled().needs_docker_socket()


@pytest.mark.parametrize(
    "config", [c for c in SERVICE_CONFIGS if issubclass(c, AzMockableServiceConfig)]
)
def test_mockable_service_needs_the_socket_only_while_not_mocked(
    config: type[AzMockableServiceConfig],
) -> None:
    if config is CosmosConfig:
        live: AzServiceConfig = CosmosConfig(mocked=False, mongodb_enabled=True)
        mocked: AzServiceConfig = CosmosConfig(mocked=True, mongodb_enabled=True)
    else:
        live, mocked = config(mocked=False), config(mocked=True)
    assert all_disabled().with_service_config(live).needs_docker_socket()
    assert not all_disabled().with_service_config(mocked).needs_docker_socket()


@pytest.mark.parametrize("config", [AciConfig, ContainerAppsConfig, ServiceBusConfig, VmConfig])
def test_default_mocked_services_need_no_socket_until_unmocked(
    config: type[AzMockableServiceConfig],
) -> None:
    assert not all_disabled().with_service_config(config()).needs_docker_socket()
    # Enabled through a raw env var, with the mock switch left at the emulator's default.
    raw = all_disabled().with_env(AZ.service_env(config.TOKEN, "ENABLED"), "true")
    assert not raw.needs_docker_socket()
    assert raw.with_env(AZ.service_env(config.TOKEN, "MOCKED"), "false").needs_docker_socket()


def test_cosmos_needs_the_socket_only_for_a_container_engine() -> None:
    def needs(config: CosmosConfig) -> bool:
        return all_disabled().with_service_config(config).needs_docker_socket()

    assert not needs(CosmosConfig())  # NoSQL and Table run inside the emulator
    for engine in ("mongodb", "postgresql", "cassandra", "gremlin"):
        on = {f"{engine}_enabled": True}
        assert needs(CosmosConfig(**on))  # type: ignore[arg-type]
        assert needs(CosmosConfig(engine_startup="eager", **on))  # type: ignore[arg-type]
        assert not needs(CosmosConfig(engine_startup="disabled", **on))  # type: ignore[arg-type]
        assert not needs(CosmosConfig(mocked=True, **on))  # type: ignore[arg-type]
        assert not needs(CosmosConfig(enabled=False, **on))  # type: ignore[arg-type]


def test_sql_needs_the_socket_only_with_the_managed_provider() -> None:
    def needs(config: SqlConfig) -> bool:
        return all_disabled().with_service_config(config).needs_docker_socket()

    assert not needs(SqlConfig())
    assert needs(SqlConfig(data_plane_provider="managed"))
    assert not needs(SqlConfig(data_plane_provider="none"))
    assert not needs(SqlConfig(data_plane_provider="external"))
    # Without a provider the emulator picks managed once the EULA is accepted.
    assert needs(SqlConfig(accept_eula="Y"))
    assert not needs(SqlConfig(data_plane_provider="none", accept_eula="Y"))
    assert not needs(SqlConfig(enabled=False, data_plane_provider="managed"))


def test_sql_detection_follows_the_deprecated_mock_switch() -> None:
    c = all_disabled().with_env("FLOCI_AZ_SERVICES_SQL_ENABLED", "true")
    assert not c.needs_docker_socket()
    assert c.with_env("FLOCI_AZ_SERVICES_SQL_MOCKED", "false").needs_docker_socket()
    assert not c.with_env("FLOCI_AZ_SERVICES_SQL_MOCKED", "true").needs_docker_socket()
    # An explicit provider wins over the old switch.
    c.with_env("FLOCI_AZ_SERVICES_SQL_MOCKED", "false")
    assert not c.with_env("FLOCI_AZ_SERVICES_SQL_DATA_PLANE_PROVIDER", "none").needs_docker_socket()


def test_override_wins_both_ways() -> None:
    assert not FlociAzContainer().with_docker_socket(False).needs_docker_socket()
    assert all_disabled().with_docker_socket(True).needs_docker_socket()


# --- integration ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def floci() -> Iterator[FlociAzContainer]:
    with FlociAzContainer(AZ_TEST_IMAGE) as container:
        yield container


@pytest.mark.integration
def test_container_starts_and_is_healthy(floci: FlociAzContainer) -> None:
    import urllib.request

    assert floci.get_endpoint().startswith("http://")
    with urllib.request.urlopen(floci.get_endpoint() + "/_floci/health", timeout=5) as resp:
        assert resp.status == 200


@pytest.mark.integration
def test_blob_round_trip(floci: FlociAzContainer) -> None:
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(floci.get_storage_connection_string())
    container = service.create_container(f"blobs-{uuid.uuid4().hex[:8]}")
    container.upload_blob("hello.txt", b"hello from floci")

    assert [blob.name for blob in container.list_blobs()] == ["hello.txt"]
    assert container.download_blob("hello.txt").readall() == b"hello from floci"


@pytest.mark.integration
def test_queue_round_trip(floci: FlociAzContainer) -> None:
    from azure.storage.queue import QueueServiceClient

    service = QueueServiceClient.from_connection_string(floci.get_storage_connection_string())
    queue = service.create_queue(f"queue-{uuid.uuid4().hex[:8]}")
    queue.send_message("hello from floci")

    assert [message.content for message in queue.receive_messages()] == ["hello from floci"]


@pytest.mark.integration
def test_reset_wipes_state_and_keeps_serving(floci: FlociAzContainer) -> None:
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(floci.get_storage_connection_string())
    service.create_container("before-reset")
    assert "before-reset" in [container.name for container in service.list_containers()]

    floci.reset()

    assert [container.name for container in service.list_containers()] == []
    service.create_container("after-reset")


@pytest.mark.integration
def test_https_answers_as_soon_as_a_tls_container_has_started() -> None:
    # The port answers plain HTTP before it completes TLS handshakes; start() must cover both.
    with FlociAzContainer(AZ_TEST_IMAGE).with_tls_config(TlsConfig(enabled=True)) as floci:
        health = floci.get_https_endpoint() + "/_floci/health"
        assert https_status(health) == 200
        assert https_status(health, floci.get_tls_certificate()) == 200


@pytest.mark.integration
def test_namespace_is_unique_per_start() -> None:
    def namespace_in_container(container: FlociAzContainer) -> str:
        env = container.get_wrapped_container().attrs["Config"]["Env"]
        prefix = "FLOCI_AZ_DOCKER_RESOURCE_NAMESPACE="
        return next(entry[len(prefix) :] for entry in env if entry.startswith(prefix))

    with FlociAzContainer(AZ_TEST_IMAGE) as a, FlociAzContainer(AZ_TEST_IMAGE) as b:
        assert namespace_in_container(a) == a.get_resource_namespace()
        assert namespace_in_container(b) == b.get_resource_namespace()
        assert a.get_resource_namespace() != b.get_resource_namespace()
