"""Tests for the GCP module (``floci.gcp``). The unit tests need no Docker."""

from __future__ import annotations

import base64
import json
import urllib.request
import uuid
from collections.abc import Iterator
from typing import Any

import pytest

from floci.core import FlociBaseContainer
from floci.gcp import GCP, FlociGcpContainer
from floci.gcp.config import (
    SERVICE_CONFIGS,
    BigQueryConfig,
    CloudSqlConfig,
    GcpMockableServiceConfig,
    GcpServiceConfig,
    GcsConfig,
    TlsConfig,
)
from tests.https import https_status
from tests.images import GCP_TEST_IMAGE

# Token -> has a mock switch: the emulator's ServicesConfig (floci-gcp,
# config/EmulatorConfig.java). No service is mocked by default.
SERVICES = {
    "BIGQUERY": True,
    "CLOUDFUNCTIONS": False,
    "CLOUDRUN": True,
    "CLOUDSQL": True,
    "CLOUDTASKS": False,
    "COMPUTE": False,
    "DATASTORE": False,
    "EVENTARC": False,
    "FIREBASEAUTH": False,
    "FIRESTORE": False,
    "GCS": False,
    "GKE": True,
    "IAM": False,
    "IAMCREDENTIALS": False,
    "KAFKA": True,
    "KMS": False,
    "LOGGING": False,
    "MONITORING": False,
    "PUBSUB": False,
    "RESOURCEMANAGER": False,
    "SCHEDULER": False,
    "SECRETMANAGER": False,
    "SERVICEUSAGE": False,
    "STS": False,
}


def env_of(config: object) -> dict[str, str]:
    """The env vars a config writes on a fresh container."""
    c = FlociGcpContainer()
    before = dict(c.env)
    c.with_service_config(config)  # type: ignore[arg-type]
    return {k: v for k, v in c.env.items() if before.get(k) != v}


def all_disabled() -> FlociGcpContainer:
    """A container with every service switched off."""
    c = FlociGcpContainer()
    for config in SERVICE_CONFIGS:
        c.with_service_config(config(enabled=False))
    return c


# --- descriptor and defaults ----------------------------------------------------------------


def test_descriptor() -> None:
    assert GCP.name == "gcp"
    assert GCP.image == "floci/floci-gcp"
    assert GCP.port == 4588
    assert GCP.env_prefix == "FLOCI_GCP_"
    assert GCP.health_path == "/_floci-gcp/health"
    assert GCP.reset_path == "/_floci-gcp/state/reset"
    assert GCP.log_level_env == "QUARKUS_LOG_CATEGORY__IO_FLOCI_GCP__LEVEL"
    assert GCP.network_env == "FLOCI_GCP_SERVICES_DOCKER_NETWORK"
    assert GCP.resource_namespace_env == "FLOCI_GCP_DOCKER_RESOURCE_NAMESPACE"
    assert GCP.host_settings == ()


def test_default_container() -> None:
    c = FlociGcpContainer()
    assert isinstance(c, FlociBaseContainer)
    assert c.DESCRIPTOR is GCP
    assert c.image == "floci/floci-gcp:latest"
    assert {str(port) for port in c.ports} == {"4588"}
    assert c.env == {
        "FLOCI_GCP_TLS_HTTPS_PORT": "0",
        "FLOCI_GCP_DOCKER_RESOURCE_NAMESPACE": c.get_resource_namespace(),
    }


def test_default_env_can_be_overridden() -> None:
    c = FlociGcpContainer().with_env("FLOCI_GCP_TLS_HTTPS_PORT", "8443")
    assert c.env["FLOCI_GCP_TLS_HTTPS_PORT"] == "8443"


def test_project_id() -> None:
    c = FlociGcpContainer()
    assert c.get_project_id() == "floci-local"
    assert "FLOCI_GCP_DEFAULT_PROJECT_ID" not in c.env
    assert c.with_project_id("my-project") is c
    assert c.get_project_id() == "my-project"
    assert c.env["FLOCI_GCP_DEFAULT_PROJECT_ID"] == "my-project"


def test_core_settings_use_the_gcp_env_vars() -> None:
    a, b = FlociGcpContainer(), FlociGcpContainer()
    assert a.get_resource_namespace().startswith("tc-")
    assert a.get_resource_namespace() != b.get_resource_namespace()
    assert a.with_resource_namespace("ci-42").env["FLOCI_GCP_DOCKER_RESOURCE_NAMESPACE"] == "ci-42"
    assert a.with_log_level("DEBUG").env["QUARKUS_LOG_CATEGORY__IO_FLOCI_GCP__LEVEL"] == "DEBUG"
    network = a.with_dedicated_network().get_dedicated_network_name()
    assert network is not None
    assert a.env["FLOCI_GCP_SERVICES_DOCKER_NETWORK"] == network


def test_fluent_methods_keep_the_gcp_type() -> None:
    c = FlociGcpContainer().with_log_level("INFO").with_gcs_config(GcsConfig())
    assert isinstance(c.with_docker_socket(False), FlociGcpContainer)


def test_connection_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    c = FlociGcpContainer().with_project_id("my-project")
    monkeypatch.setattr(c, "get_endpoint", lambda: "http://localhost:32768")
    assert c.get_https_endpoint() == "https://localhost:32768"
    assert c.get_emulator_host() == "localhost:32768"
    # Only the Storage REST variable is a URL; the SDKs want host:port for the rest.
    assert c.get_emulator_env() == {
        "PUBSUB_EMULATOR_HOST": "localhost:32768",
        "FIRESTORE_EMULATOR_HOST": "localhost:32768",
        "DATASTORE_EMULATOR_HOST": "localhost:32768",
        "SECRET_MANAGER_EMULATOR_HOST": "localhost:32768",
        "FIREBASE_AUTH_EMULATOR_HOST": "localhost:32768",
        "LOGGING_EMULATOR_HOST": "localhost:32768",
        "KMS_EMULATOR_HOST": "localhost:32768",
        "STORAGE_EMULATOR_HOST": "http://localhost:32768",
        "STORAGE_EMULATOR_HOST_GRPC": "localhost:32768",
        "GOOGLE_CLOUD_PROJECT": "my-project",
    }


# --- service configs ------------------------------------------------------------------------


def test_every_emulator_service_has_a_config() -> None:
    assert {config.TOKEN for config in SERVICE_CONFIGS} == set(SERVICES)
    assert len({config.TOKEN for config in SERVICE_CONFIGS}) == len(SERVICE_CONFIGS)


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_mock_switch_and_defaults_match_the_emulator(config: type[GcpServiceConfig]) -> None:
    default = config()
    assert default.enabled
    assert issubclass(config, GcpMockableServiceConfig) == SERVICES[config.TOKEN]
    assert getattr(default, "mock", False) is False


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_enabled_is_always_emitted_and_the_rest_only_when_enabled(
    config: type[GcpServiceConfig],
) -> None:
    prefix = f"FLOCI_GCP_SERVICES_{config.TOKEN}_"
    assert env_of(config(enabled=False)) == {f"{prefix}ENABLED": "false"}

    if issubclass(config, GcpMockableServiceConfig):
        assert env_of(config()) == {f"{prefix}ENABLED": "true", f"{prefix}MOCK": "false"}
        assert env_of(config(mock=True))[f"{prefix}MOCK"] == "true"
        assert env_of(config(enabled=False, mock=True)) == {f"{prefix}ENABLED": "false"}
    else:
        assert env_of(config()) == {f"{prefix}ENABLED": "true"}


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_every_config_has_a_fluent_method(config: type[GcpServiceConfig]) -> None:
    c = FlociGcpContainer()
    method = getattr(c, f"with_{config.TOKEN.lower()}_config")
    assert method(config(enabled=False)) is c
    assert c.env[f"FLOCI_GCP_SERVICES_{config.TOKEN}_ENABLED"] == "false"


def test_fluent_methods_are_exactly_the_configs() -> None:
    methods = {
        name
        for name in dir(FlociGcpContainer)
        if name.startswith("with_") and name.endswith("_config")
    }
    expected = {f"with_{config.TOKEN.lower()}_config" for config in SERVICE_CONFIGS}
    assert methods == expected | {"with_service_config", "with_tls_config"}


def test_tls_config() -> None:
    c = FlociGcpContainer()
    c.with_tls_config(TlsConfig())
    assert c.env["FLOCI_GCP_TLS_ENABLED"] == "false"
    assert "FLOCI_GCP_TLS_SELF_SIGNED" not in c.env

    c.with_tls_config(
        TlsConfig(enabled=True, cert_path="/certs/tls.crt", key_path="/certs/tls.key")
    )
    assert c.env["FLOCI_GCP_TLS_ENABLED"] == "true"
    assert c.env["FLOCI_GCP_TLS_SELF_SIGNED"] == "true"
    assert c.env["FLOCI_GCP_TLS_CERT_PATH"] == "/certs/tls.crt"
    assert c.env["FLOCI_GCP_TLS_KEY_PATH"] == "/certs/tls.key"
    assert c.env["FLOCI_GCP_TLS_HTTPS_PORT"] == "0"


def test_a_disabled_config_removes_the_settings_of_the_enabled_one() -> None:
    c = all_disabled().with_cloudsql_config(CloudSqlConfig())
    assert c.needs_docker_socket()

    c.with_cloudsql_config(CloudSqlConfig(enabled=False))

    assert "FLOCI_GCP_SERVICES_CLOUDSQL_MOCK" not in c.env
    assert c.env["FLOCI_GCP_SERVICES_CLOUDSQL_ENABLED"] == "false"
    assert not c.needs_docker_socket()


def test_a_caller_override_survives_the_replacement() -> None:
    c = FlociGcpContainer().with_cloudsql_config(CloudSqlConfig())
    c.with_env("FLOCI_GCP_SERVICES_CLOUDSQL_MOCK", "true")
    c.with_cloudsql_config(CloudSqlConfig(enabled=False))
    assert c.env["FLOCI_GCP_SERVICES_CLOUDSQL_MOCK"] == "true"


def test_applying_the_same_config_again_changes_nothing() -> None:
    c = FlociGcpContainer().with_cloudsql_config(CloudSqlConfig(mock=True))
    once = dict(c.env)
    c.with_cloudsql_config(CloudSqlConfig(mock=True))
    assert c.env == once


def test_replacing_the_tls_config_keeps_the_default_https_port() -> None:
    c = FlociGcpContainer()
    defaults = dict(c.env)
    c.with_tls_config(TlsConfig(enabled=True, https_port=8443, cert_path="/certs/tls.crt"))
    assert c.env["FLOCI_GCP_TLS_HTTPS_PORT"] == "8443"

    c.with_tls_config(TlsConfig(enabled=False))

    # Back to the container's default, not gone: without it the emulator binds 443.
    assert c.env == {**defaults, "FLOCI_GCP_TLS_ENABLED": "false"}

    c.with_tls_config(TlsConfig(enabled=True)).with_tls_config(TlsConfig(enabled=False))
    assert c.env["FLOCI_GCP_TLS_HTTPS_PORT"] == "0"


def test_https_wait_only_while_tls_is_enabled() -> None:
    assert GCP.tls_enabled_env == "FLOCI_GCP_TLS_ENABLED"
    c = FlociGcpContainer()
    assert not c.needs_https_wait()
    assert c.with_tls_config(TlsConfig(enabled=True)).needs_https_wait()
    assert not c.with_tls_config(TlsConfig()).needs_https_wait()
    assert c.with_env("FLOCI_GCP_TLS_ENABLED", "true").needs_https_wait()


def test_configs_can_be_applied_repeatedly() -> None:
    c = FlociGcpContainer()
    c.with_cloudsql_config(CloudSqlConfig(mock=True))
    c.with_cloudsql_config(CloudSqlConfig(mock=True))
    c.with_cloudsql_config(CloudSqlConfig())
    assert c.env["FLOCI_GCP_SERVICES_CLOUDSQL_MOCK"] == "false"


# --- Docker socket detection ----------------------------------------------------------------


def test_socket_table_matches_the_service_configs() -> None:
    table = {svc.token: svc for svc in GCP.socket_services}
    assert len(table) == len(GCP.socket_services)
    # Exactly the services with a mock switch start sibling containers.
    assert set(table) == {token for token, mockable in SERVICES.items() if mockable}
    for svc in table.values():
        assert svc.mockable
        assert svc.mock_setting == "MOCK"
        assert not svc.mocked_by_default
    assert {token for token, svc in table.items() if svc.spawns is not None} == {"BIGQUERY"}


def test_default_container_needs_the_socket() -> None:
    assert FlociGcpContainer().needs_docker_socket()


def test_no_socket_with_every_service_disabled() -> None:
    assert not all_disabled().needs_docker_socket()


def test_no_socket_for_the_services_without_containers() -> None:
    c = all_disabled()
    for config in SERVICE_CONFIGS:
        if not issubclass(config, GcpMockableServiceConfig):
            c.with_service_config(config())
    assert not c.needs_docker_socket()


@pytest.mark.parametrize(
    "config", [c for c in SERVICE_CONFIGS if issubclass(c, GcpMockableServiceConfig)]
)
def test_mockable_service_needs_the_socket_only_while_not_mocked(
    config: type[GcpMockableServiceConfig],
) -> None:
    assert all_disabled().with_service_config(config()).needs_docker_socket()
    assert not all_disabled().with_service_config(config(mock=True)).needs_docker_socket()
    # Enabled through a raw env var, with the mock switch left at the emulator's default.
    raw = all_disabled().with_env(GCP.service_env(config.TOKEN, "ENABLED"), "true")
    assert raw.needs_docker_socket()
    assert not raw.with_env(GCP.service_env(config.TOKEN, "MOCK"), "true").needs_docker_socket()


def test_bigquery_needs_no_socket_with_an_external_duck() -> None:
    c = all_disabled().with_bigquery_config(BigQueryConfig())
    assert c.needs_docker_socket()
    c.with_env("FLOCI_GCP_SERVICES_BIGQUERY_DUCK_URL", "http://duck:3000")
    assert not c.needs_docker_socket()


def test_override_wins_both_ways() -> None:
    assert not FlociGcpContainer().with_docker_socket(False).needs_docker_socket()
    assert all_disabled().with_docker_socket(True).needs_docker_socket()


# --- integration ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def floci() -> Iterator[FlociGcpContainer]:
    with FlociGcpContainer(GCP_TEST_IMAGE) as container:
        yield container


def call(method: str, url: str, body: dict[str, Any] | None = None) -> Any:
    """One JSON request to the emulator's REST surface."""
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


@pytest.mark.integration
def test_container_starts_and_is_healthy(floci: FlociGcpContainer) -> None:
    assert floci.get_endpoint().startswith("http://")
    with urllib.request.urlopen(floci.get_endpoint() + "/_floci-gcp/health", timeout=5) as resp:
        assert resp.status == 200


@pytest.mark.integration
def test_storage_round_trip_with_the_emulator_env(
    floci: FlociGcpContainer, monkeypatch: pytest.MonkeyPatch
) -> None:
    from google.cloud import storage

    for key, value in floci.get_emulator_env().items():
        monkeypatch.setenv(key, value)

    # STORAGE_EMULATOR_HOST alone points the client at the emulator, without credentials.
    client = storage.Client()
    assert client.project == floci.get_project_id()
    bucket = client.create_bucket(f"bucket-{uuid.uuid4().hex[:8]}")
    bucket.blob("hello.txt").upload_from_string(b"hello from floci")

    assert [blob.name for blob in client.list_blobs(bucket.name)] == ["hello.txt"]
    assert bucket.blob("hello.txt").download_as_bytes() == b"hello from floci"


@pytest.mark.integration
def test_pubsub_round_trip(floci: FlociGcpContainer) -> None:
    host = floci.get_emulator_env()["PUBSUB_EMULATOR_HOST"]
    project = f"http://{host}/v1/projects/{floci.get_project_id()}"
    suffix = uuid.uuid4().hex[:8]
    topic, subscription = f"{project}/topics/t-{suffix}", f"{project}/subscriptions/s-{suffix}"

    call("PUT", topic, {})
    call("PUT", subscription, {"topic": f"projects/{floci.get_project_id()}/topics/t-{suffix}"})
    payload = base64.b64encode(b"hello from floci").decode()
    assert len(call("POST", f"{topic}:publish", {"messages": [{"data": payload}]})["messageIds"])

    received = call("POST", f"{subscription}:pull", {"maxMessages": 1})["receivedMessages"]
    assert [base64.b64decode(m["message"]["data"]) for m in received] == [b"hello from floci"]
    call("POST", f"{subscription}:acknowledge", {"ackIds": [m["ackId"] for m in received]})


@pytest.mark.integration
def test_reset_wipes_state_and_keeps_serving(floci: FlociGcpContainer) -> None:
    buckets = f"{floci.get_endpoint()}/storage/v1/b?project={floci.get_project_id()}"

    def names() -> list[str]:
        return [bucket["name"] for bucket in call("GET", buckets).get("items", [])]

    call("POST", buckets, {"name": "before-reset"})
    assert "before-reset" in names()

    floci.reset()

    assert names() == []
    call("POST", buckets, {"name": "after-reset"})
    assert names() == ["after-reset"]


@pytest.mark.integration
def test_https_answers_as_soon_as_a_tls_container_has_started() -> None:
    # The port answers plain HTTP before it completes TLS handshakes; start() must cover both.
    with FlociGcpContainer(GCP_TEST_IMAGE).with_tls_config(TlsConfig(enabled=True)) as floci:
        health = floci.get_https_endpoint() + "/_floci-gcp/health"
        assert https_status(health) == 200
        assert https_status(health, floci.get_tls_certificate()) == 200


@pytest.mark.integration
def test_namespace_is_unique_per_start() -> None:
    def namespace_in_container(container: FlociGcpContainer) -> str:
        env = container.get_wrapped_container().attrs["Config"]["Env"]
        prefix = "FLOCI_GCP_DOCKER_RESOURCE_NAMESPACE="
        return next(entry[len(prefix) :] for entry in env if entry.startswith(prefix))

    with FlociGcpContainer(GCP_TEST_IMAGE) as a, FlociGcpContainer(GCP_TEST_IMAGE) as b:
        assert namespace_in_container(a) == a.get_resource_namespace()
        assert namespace_in_container(b) == b.get_resource_namespace()
        assert a.get_resource_namespace() != b.get_resource_namespace()
