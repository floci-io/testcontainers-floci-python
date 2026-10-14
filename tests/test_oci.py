"""Tests for the OCI module (``floci.oci``). The unit tests need no Docker."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from floci.core import FlociBaseContainer
from floci.oci import OCI, FlociOciContainer
from floci.oci.config import (
    SERVICE_CONFIGS,
    FunctionsConfig,
    ObjectStorageConfig,
    OciMockableServiceConfig,
    OciServiceConfig,
    TlsConfig,
)
from tests.https import https_status
from tests.images import OCI_TEST_IMAGE

TENANCY = "ocid1.tenancy.oc1..flocilocaltenancy0000000000000000000000000000000000000000"
USER = "ocid1.user.oc1..flocilocaluser0000000000000000000000000000000000000000000000"
FINGERPRINT = "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"

# Token -> has a mock switch: the emulator's ServicesConfig (floci-oci,
# config/EmulatorConfig.java). No service is mocked by default.
SERVICES = {
    "FUNCTIONS": True,
    "IDENTITY": False,
    "KMS": False,
    "OBJECTSTORAGE": False,
    "OKE": True,
    "QUEUE": False,
    "STREAMING": False,
    "VAULT": False,
}


def env_of(config: object) -> dict[str, str]:
    """The env vars a config writes on a fresh container."""
    c = FlociOciContainer()
    before = dict(c.env)
    c.with_service_config(config)  # type: ignore[arg-type]
    return {k: v for k, v in c.env.items() if before.get(k) != v}


def all_disabled() -> FlociOciContainer:
    """A container with every service switched off."""
    c = FlociOciContainer()
    for config in SERVICE_CONFIGS:
        c.with_service_config(config(enabled=False))
    return c


# --- descriptor and defaults ----------------------------------------------------------------


def test_descriptor() -> None:
    assert OCI.name == "oci"
    assert OCI.image == "floci/floci-oci"
    assert OCI.port == 4599
    assert OCI.env_prefix == "FLOCI_OCI_"
    assert OCI.health_path == "/_floci-oci/health"
    assert OCI.reset_path == "/_floci-oci/state/reset"
    assert OCI.log_level_env == "QUARKUS_LOG_CATEGORY__IO_FLOCI_OCI__LEVEL"
    assert OCI.network_env == "FLOCI_OCI_SERVICES_DOCKER_NETWORK"
    assert OCI.resource_namespace_env == "FLOCI_OCI_DOCKER_RESOURCE_NAMESPACE"
    assert OCI.host_settings == ()


def test_default_container() -> None:
    c = FlociOciContainer()
    assert isinstance(c, FlociBaseContainer)
    assert c.DESCRIPTOR is OCI
    assert c.image == "floci/floci-oci:latest"
    assert {str(port) for port in c.ports} == {"4599"}
    assert c.env == {
        "FLOCI_OCI_TLS_HTTPS_PORT": "0",
        "FLOCI_OCI_DOCKER_RESOURCE_NAMESPACE": c.get_resource_namespace(),
    }


def test_default_env_can_be_overridden() -> None:
    c = FlociOciContainer().with_env("FLOCI_OCI_TLS_HTTPS_PORT", "8443")
    assert c.env["FLOCI_OCI_TLS_HTTPS_PORT"] == "8443"


def test_identity() -> None:
    c = FlociOciContainer()
    assert c.get_region() == "us-ashburn-1"
    assert c.DEFAULT_REALM == "oc1"
    assert c.get_tenancy_id() == TENANCY
    assert c.get_namespace() == "floci-local"
    assert c.get_user_id() == USER
    assert c.get_fingerprint() == FINGERPRINT


def test_identity_overrides() -> None:
    c = FlociOciContainer()
    assert c.with_region("eu-frankfurt-1").with_namespace("my-ns") is c
    c.with_tenancy_id("ocid1.tenancy.oc1..other")
    assert c.get_region() == "eu-frankfurt-1"
    assert c.get_namespace() == "my-ns"
    assert c.get_tenancy_id() == "ocid1.tenancy.oc1..other"
    assert c.env["FLOCI_OCI_DEFAULT_REGION"] == "eu-frankfurt-1"
    assert c.env["FLOCI_OCI_DEFAULT_NAMESPACE"] == "my-ns"
    assert c.env["FLOCI_OCI_DEFAULT_TENANCY_ID"] == "ocid1.tenancy.oc1..other"
    assert c.get_config()["tenancy"] == "ocid1.tenancy.oc1..other"
    assert c.get_config()["region"] == "eu-frankfurt-1"


def test_core_settings_use_the_oci_env_vars() -> None:
    a, b = FlociOciContainer(), FlociOciContainer()
    assert a.get_resource_namespace().startswith("tc-")
    assert a.get_resource_namespace() != b.get_resource_namespace()
    assert a.with_resource_namespace("ci-42").env["FLOCI_OCI_DOCKER_RESOURCE_NAMESPACE"] == "ci-42"
    assert a.with_log_level("DEBUG").env["QUARKUS_LOG_CATEGORY__IO_FLOCI_OCI__LEVEL"] == "DEBUG"
    network = a.with_dedicated_network().get_dedicated_network_name()
    assert network is not None
    assert a.env["FLOCI_OCI_SERVICES_DOCKER_NETWORK"] == network


def test_fluent_methods_keep_the_oci_type() -> None:
    c = FlociOciContainer().with_log_level("INFO").with_objectstorage_config(ObjectStorageConfig())
    assert isinstance(c.with_docker_socket(False), FlociOciContainer)


def test_https_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    c = FlociOciContainer()
    monkeypatch.setattr(c, "get_endpoint", lambda: "http://localhost:32768")
    assert c.get_https_endpoint() == "https://localhost:32768"


# --- credentials ----------------------------------------------------------------------------


def test_private_key_is_an_rsa_key_generated_once_per_container() -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    a, b = FlociOciContainer(), FlociOciContainer()
    pem = a.get_private_key_pem()
    assert pem.startswith("-----BEGIN PRIVATE KEY-----\n")
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    assert isinstance(key, rsa.RSAPrivateKey)
    assert key.key_size == 2048
    assert a.get_private_key_pem() == pem
    assert b.get_private_key_pem() != pem


def test_private_key_can_be_supplied() -> None:
    c = FlociOciContainer()
    assert c.with_private_key_pem("-----BEGIN PRIVATE KEY-----\nmine\n") is c
    assert c.get_private_key_pem() == "-----BEGIN PRIVATE KEY-----\nmine\n"


def test_key_generation_without_cryptography_says_what_to_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A None entry makes the import fail, as if the package were not installed.
    for name in [m for m in sys.modules if m == "cryptography" or m.startswith("cryptography.")]:
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setitem(sys.modules, "cryptography", None)

    c = FlociOciContainer()  # the container itself does not need the package
    with pytest.raises(ImportError, match=r"testcontainers-floci\[oci\]"):
        c.get_private_key_pem()
    assert c.with_private_key_pem("mine").get_private_key_pem() == "mine"


def test_sdk_config() -> None:
    c = FlociOciContainer()
    assert c.get_config() == {
        "user": USER,
        "fingerprint": FINGERPRINT,
        "tenancy": TENANCY,
        "region": "us-ashburn-1",
        "key_content": c.get_private_key_pem(),
    }


def test_sdk_config_passes_the_python_sdk_validation() -> None:
    import oci

    oci.config.validate_config(FlociOciContainer().get_config())


def test_config_file_contents() -> None:
    c = FlociOciContainer()
    assert c.get_config_file_contents("/keys/floci.pem") == (
        "[DEFAULT]\n"
        f"user={USER}\n"
        f"fingerprint={FINGERPRINT}\n"
        f"tenancy={TENANCY}\n"
        "region=us-ashburn-1\n"
        "key_file=/keys/floci.pem\n"
    )
    assert c.get_config_file_contents("k.pem", profile="FLOCI").startswith("[FLOCI]\n")


def test_config_file_is_read_by_the_python_sdk(tmp_path: Path) -> None:
    import oci

    c = FlociOciContainer()
    key_file = tmp_path / "floci_key.pem"
    key_file.write_text(c.get_private_key_pem())
    config_file = tmp_path / "config"
    config_file.write_text(c.get_config_file_contents(str(key_file), profile="FLOCI"))

    config = oci.config.from_file(str(config_file), "FLOCI")
    assert config["tenancy"] == TENANCY
    assert config["user"] == USER
    assert config["key_file"] == str(key_file)
    # Building a client loads the key and the signer.
    oci.object_storage.ObjectStorageClient(config, service_endpoint="http://localhost:4599")


# --- service configs ------------------------------------------------------------------------


def test_every_emulator_service_has_a_config() -> None:
    assert {config.TOKEN for config in SERVICE_CONFIGS} == set(SERVICES)
    assert len({config.TOKEN for config in SERVICE_CONFIGS}) == len(SERVICE_CONFIGS)


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_mock_switch_and_defaults_match_the_emulator(config: type[OciServiceConfig]) -> None:
    default = config()
    assert default.enabled
    assert issubclass(config, OciMockableServiceConfig) == SERVICES[config.TOKEN]
    assert getattr(default, "mock", False) is False


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_enabled_is_always_emitted_and_the_rest_only_when_enabled(
    config: type[OciServiceConfig],
) -> None:
    prefix = f"FLOCI_OCI_SERVICES_{config.TOKEN}_"
    assert env_of(config(enabled=False)) == {f"{prefix}ENABLED": "false"}

    if issubclass(config, OciMockableServiceConfig):
        assert env_of(config()) == {f"{prefix}ENABLED": "true", f"{prefix}MOCK": "false"}
        assert env_of(config(mock=True))[f"{prefix}MOCK"] == "true"
        assert env_of(config(enabled=False, mock=True)) == {f"{prefix}ENABLED": "false"}
    else:
        assert env_of(config()) == {f"{prefix}ENABLED": "true"}


@pytest.mark.parametrize("config", SERVICE_CONFIGS, ids=lambda config: config.TOKEN)
def test_every_config_has_a_fluent_method(config: type[OciServiceConfig]) -> None:
    c = FlociOciContainer()
    method = getattr(c, f"with_{config.TOKEN.lower()}_config")
    assert method(config(enabled=False)) is c
    assert c.env[f"FLOCI_OCI_SERVICES_{config.TOKEN}_ENABLED"] == "false"


def test_fluent_methods_are_exactly_the_configs() -> None:
    methods = {
        name
        for name in dir(FlociOciContainer)
        if name.startswith("with_") and name.endswith("_config")
    }
    expected = {f"with_{config.TOKEN.lower()}_config" for config in SERVICE_CONFIGS}
    assert methods == expected | {"with_service_config", "with_tls_config"}


def test_tls_config() -> None:
    c = FlociOciContainer()
    c.with_tls_config(TlsConfig())
    assert c.env["FLOCI_OCI_TLS_ENABLED"] == "false"
    assert "FLOCI_OCI_TLS_SELF_SIGNED" not in c.env

    c.with_tls_config(
        TlsConfig(enabled=True, cert_path="/certs/tls.crt", key_path="/certs/tls.key")
    )
    assert c.env["FLOCI_OCI_TLS_ENABLED"] == "true"
    assert c.env["FLOCI_OCI_TLS_SELF_SIGNED"] == "true"
    assert c.env["FLOCI_OCI_TLS_CERT_PATH"] == "/certs/tls.crt"
    assert c.env["FLOCI_OCI_TLS_KEY_PATH"] == "/certs/tls.key"
    assert c.env["FLOCI_OCI_TLS_HTTPS_PORT"] == "0"


def test_a_disabled_config_removes_the_settings_of_the_enabled_one() -> None:
    c = all_disabled().with_functions_config(FunctionsConfig())
    assert c.needs_docker_socket()

    c.with_functions_config(FunctionsConfig(enabled=False))

    assert "FLOCI_OCI_SERVICES_FUNCTIONS_MOCK" not in c.env
    assert c.env["FLOCI_OCI_SERVICES_FUNCTIONS_ENABLED"] == "false"
    assert not c.needs_docker_socket()


def test_a_caller_override_survives_the_replacement() -> None:
    c = FlociOciContainer().with_functions_config(FunctionsConfig())
    c.with_env("FLOCI_OCI_SERVICES_FUNCTIONS_MOCK", "true")
    c.with_functions_config(FunctionsConfig(enabled=False))
    assert c.env["FLOCI_OCI_SERVICES_FUNCTIONS_MOCK"] == "true"


def test_applying_the_same_config_again_changes_nothing() -> None:
    c = FlociOciContainer().with_functions_config(FunctionsConfig(mock=True))
    once = dict(c.env)
    c.with_functions_config(FunctionsConfig(mock=True))
    assert c.env == once


def test_replacing_the_tls_config_keeps_the_default_https_port() -> None:
    c = FlociOciContainer()
    defaults = dict(c.env)
    c.with_tls_config(TlsConfig(enabled=True, https_port=8443, cert_path="/certs/tls.crt"))
    assert c.env["FLOCI_OCI_TLS_HTTPS_PORT"] == "8443"

    c.with_tls_config(TlsConfig(enabled=False))

    # Back to the container's default, not gone: without it the emulator binds 443.
    assert c.env == {**defaults, "FLOCI_OCI_TLS_ENABLED": "false"}

    c.with_tls_config(TlsConfig(enabled=True)).with_tls_config(TlsConfig(enabled=False))
    assert c.env["FLOCI_OCI_TLS_HTTPS_PORT"] == "0"


def test_https_wait_only_while_tls_is_enabled() -> None:
    assert OCI.tls_enabled_env == "FLOCI_OCI_TLS_ENABLED"
    c = FlociOciContainer()
    assert not c.needs_https_wait()
    assert c.with_tls_config(TlsConfig(enabled=True)).needs_https_wait()
    assert not c.with_tls_config(TlsConfig()).needs_https_wait()
    assert c.with_env("FLOCI_OCI_TLS_ENABLED", "true").needs_https_wait()


def test_configs_can_be_applied_repeatedly() -> None:
    c = FlociOciContainer()
    c.with_functions_config(FunctionsConfig(mock=True))
    c.with_functions_config(FunctionsConfig(mock=True))
    c.with_functions_config(FunctionsConfig())
    assert c.env["FLOCI_OCI_SERVICES_FUNCTIONS_MOCK"] == "false"


# --- Docker socket detection ----------------------------------------------------------------


def test_socket_table_matches_the_service_configs() -> None:
    table = {svc.token: svc for svc in OCI.socket_services}
    assert len(table) == len(OCI.socket_services)
    # Exactly the services with a mock switch start sibling containers.
    assert set(table) == {token for token, mockable in SERVICES.items() if mockable}
    for svc in table.values():
        assert svc.mockable
        assert svc.mock_setting == "MOCK"
        assert not svc.mocked_by_default
        assert svc.spawns is None


def test_default_container_needs_the_socket() -> None:
    assert FlociOciContainer().needs_docker_socket()


def test_no_socket_with_every_service_disabled() -> None:
    assert not all_disabled().needs_docker_socket()


def test_no_socket_for_the_services_without_containers() -> None:
    c = all_disabled()
    for config in SERVICE_CONFIGS:
        if not issubclass(config, OciMockableServiceConfig):
            c.with_service_config(config())
    assert not c.needs_docker_socket()


@pytest.mark.parametrize(
    "config", [c for c in SERVICE_CONFIGS if issubclass(c, OciMockableServiceConfig)]
)
def test_mockable_service_needs_the_socket_only_while_not_mocked(
    config: type[OciMockableServiceConfig],
) -> None:
    assert all_disabled().with_service_config(config()).needs_docker_socket()
    assert not all_disabled().with_service_config(config(mock=True)).needs_docker_socket()
    # Enabled through a raw env var, with the mock switch left at the emulator's default.
    raw = all_disabled().with_env(OCI.service_env(config.TOKEN, "ENABLED"), "true")
    assert raw.needs_docker_socket()
    assert not raw.with_env(OCI.service_env(config.TOKEN, "MOCK"), "true").needs_docker_socket()


def test_override_wins_both_ways() -> None:
    assert not FlociOciContainer().with_docker_socket(False).needs_docker_socket()
    assert all_disabled().with_docker_socket(True).needs_docker_socket()


# --- integration ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def floci() -> Iterator[FlociOciContainer]:
    with FlociOciContainer(OCI_TEST_IMAGE) as container:
        yield container


def object_storage(floci: FlociOciContainer, config: dict[str, Any] | None = None) -> Any:
    import oci

    return oci.object_storage.ObjectStorageClient(
        config or floci.get_config(), service_endpoint=floci.get_endpoint()
    )


def create_bucket(client: Any, floci: FlociOciContainer, name: str) -> None:
    import oci

    client.create_bucket(
        floci.get_namespace(),
        oci.object_storage.models.CreateBucketDetails(
            name=name, compartment_id=floci.get_tenancy_id()
        ),
    )


def bucket_names(client: Any, floci: FlociOciContainer) -> list[str]:
    buckets = client.list_buckets(floci.get_namespace(), floci.get_tenancy_id()).data
    return [bucket.name for bucket in buckets]


@pytest.mark.integration
def test_container_starts_and_is_healthy(floci: FlociOciContainer) -> None:
    assert floci.get_endpoint().startswith("http://")
    with urllib.request.urlopen(floci.get_endpoint() + "/_floci-oci/health", timeout=5) as resp:
        assert resp.status == 200


@pytest.mark.integration
def test_object_storage_round_trip(floci: FlociOciContainer) -> None:
    client = object_storage(floci)
    assert client.get_namespace().data == floci.get_namespace()

    bucket = f"bucket-{uuid.uuid4().hex[:8]}"
    create_bucket(client, floci, bucket)
    client.put_object(floci.get_namespace(), bucket, "hello.txt", b"hello from floci")

    listed = client.list_objects(floci.get_namespace(), bucket).data.objects
    assert [obj.name for obj in listed] == ["hello.txt"]
    body = client.get_object(floci.get_namespace(), bucket, "hello.txt").data.content
    assert body == b"hello from floci"


@pytest.mark.integration
def test_config_file_profile_works_with_the_sdk(floci: FlociOciContainer, tmp_path: Path) -> None:
    import oci

    key_file = tmp_path / "floci_key.pem"
    key_file.write_text(floci.get_private_key_pem())
    config_file = tmp_path / "config"
    config_file.write_text(floci.get_config_file_contents(str(key_file), profile="FLOCI"))

    client = object_storage(floci, oci.config.from_file(str(config_file), "FLOCI"))
    bucket = f"from-file-{uuid.uuid4().hex[:8]}"
    create_bucket(client, floci, bucket)
    assert bucket in bucket_names(client, floci)


@pytest.mark.integration
def test_reset_wipes_state_and_keeps_serving(floci: FlociOciContainer) -> None:
    client = object_storage(floci)
    create_bucket(client, floci, "before-reset")
    assert "before-reset" in bucket_names(client, floci)

    floci.reset()

    assert bucket_names(client, floci) == []
    create_bucket(client, floci, "after-reset")
    assert bucket_names(client, floci) == ["after-reset"]


@pytest.mark.integration
def test_the_emulator_reads_the_tenancy_from_the_signature(floci: FlociOciContainer) -> None:
    # The tenancy in the signature's keyId is the storage partition, so a client signing as
    # another tenancy must not see this one's buckets: proof that the emulator parsed what
    # the helpers made the SDK sign.
    bucket = f"tenant-{uuid.uuid4().hex[:8]}"
    mine = object_storage(floci)
    create_bucket(mine, floci, bucket)
    assert bucket in bucket_names(mine, floci)

    other_tenancy = "ocid1.tenancy.oc1..othertenancy" + uuid.uuid4().hex
    other = object_storage(floci, {**floci.get_config(), "tenancy": other_tenancy})
    listed = other.list_buckets(floci.get_namespace(), other_tenancy).data
    assert bucket not in [b.name for b in listed]

    # An unsigned request falls back to the default tenancy, the one the helpers sign as.
    url = (
        f"{floci.get_endpoint()}/n/{floci.get_namespace()}/b?compartmentId={floci.get_tenancy_id()}"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        assert bucket in [b["name"] for b in json.loads(resp.read())]


@pytest.mark.integration
@pytest.mark.xfail(
    strict=True,
    raises=TimeoutError,
    reason="floci-oci 0.4.2: with auth.require-signature the paths meant to be exempt "
    "(/health, /_floci-oci/*, /p/*) answer 401 too, so the container never reports ready",
)
def test_credentials_pass_when_the_emulator_requires_a_signature() -> None:
    class QuickToGiveUp(FlociOciContainer):
        STARTUP_TIMEOUT = 15  # the emulator is up in well under a second

    container = QuickToGiveUp(OCI_TEST_IMAGE).with_env("FLOCI_OCI_AUTH_REQUIRE_SIGNATURE", "true")
    with container as floci:
        with pytest.raises(urllib.error.HTTPError) as unsigned:
            urllib.request.urlopen(floci.get_endpoint() + "/n", timeout=10)
        assert unsigned.value.code == 401

        assert object_storage(floci).get_namespace().data == floci.get_namespace()


@pytest.mark.integration
def test_https_answers_as_soon_as_a_tls_container_has_started() -> None:
    # The port answers plain HTTP before it completes TLS handshakes; start() must cover both.
    with FlociOciContainer(OCI_TEST_IMAGE).with_tls_config(TlsConfig(enabled=True)) as floci:
        health = floci.get_https_endpoint() + "/_floci-oci/health"
        assert https_status(health) == 200


@pytest.mark.integration
def test_namespace_is_unique_per_start() -> None:
    def namespace_in_container(container: FlociOciContainer) -> str:
        env = container.get_wrapped_container().attrs["Config"]["Env"]
        prefix = "FLOCI_OCI_DOCKER_RESOURCE_NAMESPACE="
        return next(entry[len(prefix) :] for entry in env if entry.startswith(prefix))

    with FlociOciContainer(OCI_TEST_IMAGE) as a, FlociOciContainer(OCI_TEST_IMAGE) as b:
        assert namespace_in_container(a) == a.get_resource_namespace()
        assert namespace_in_container(b) == b.get_resource_namespace()
        assert a.get_resource_namespace() != b.get_resource_namespace()
