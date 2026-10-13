"""Unit tests for the shared core and the AWS module built on it. No Docker needed."""

from __future__ import annotations

import pytest

from floci.aws import AWS, FlociContainer
from floci.aws.config import (
    AthenaConfig,
    CodeBuildConfig,
    Ec2Config,
    EcrConfig,
    EcsConfig,
    EksConfig,
    ElastiCacheConfig,
    LambdaConfig,
    MskConfig,
    OpenSearchConfig,
    RdsConfig,
    S3Config,
    TlsConfig,
)
from floci.core import CloudDescriptor, FlociBaseContainer
from tests.https import https_status
from tests.images import TEST_IMAGE


def without_socket_services() -> FlociContainer:
    """A container with every service that spawns sibling containers disabled."""
    c = FlociContainer()
    for config in (
        AthenaConfig(enabled=False),
        CodeBuildConfig(enabled=False),
        Ec2Config(enabled=False),
        EcrConfig(enabled=False),
        EcsConfig(enabled=False),
        EksConfig(enabled=False),
        ElastiCacheConfig(enabled=False),
        LambdaConfig(enabled=False),
        MskConfig(enabled=False),
        OpenSearchConfig(enabled=False),
        RdsConfig(enabled=False),
    ):
        c.with_service_config(config)
    # Neptune has no typed config yet; it is switched off through its env var.
    c.with_env(AWS.service_env("NEPTUNE", "ENABLED"), "false")
    return c


# --- the old import paths keep working --------------------------------------------------------


def test_old_import_paths_alias_the_aws_module() -> None:
    import floci
    import floci.config
    import floci.config.services
    import floci.config.top_level
    import floci.container

    assert floci.FlociContainer is FlociContainer
    assert floci.container.FlociContainer is FlociContainer
    assert floci.config.S3Config is S3Config
    assert floci.config.services.S3Config is S3Config
    assert floci.config.top_level.TlsConfig is floci.config.TlsConfig


def test_aws_container_is_a_core_container() -> None:
    c = FlociContainer()
    assert isinstance(c, FlociBaseContainer)
    assert c.DESCRIPTOR is AWS
    assert c.PORT == AWS.port == 4566


# --- Docker socket detection --------------------------------------------------------------------


def test_default_container_needs_the_socket() -> None:
    # Every service is enabled by default, including the container-backed ones.
    assert FlociContainer().needs_docker_socket()


def test_no_socket_without_container_backed_services() -> None:
    assert not without_socket_services().needs_docker_socket()


@pytest.mark.parametrize("token", [svc.token for svc in AWS.socket_services])
def test_each_socket_service_requires_it(token: str) -> None:
    c = without_socket_services().with_env(f"FLOCI_SERVICES_{token}_ENABLED", "true")
    assert c.needs_docker_socket()


@pytest.mark.parametrize("token", [svc.token for svc in AWS.socket_services if svc.mockable])
def test_mocked_services_do_not_require_it(token: str) -> None:
    c = without_socket_services()
    c.with_env(f"FLOCI_SERVICES_{token}_ENABLED", "true")
    c.with_env(f"FLOCI_SERVICES_{token}_MOCK", "true")
    assert not c.needs_docker_socket()


def test_detection_reads_the_final_env() -> None:
    c = without_socket_services()
    c.with_env("FLOCI_SERVICES_LAMBDA_ENABLED", "true")  # a raw env override, not a typed config
    assert c.needs_docker_socket()


def test_override_wins_both_ways() -> None:
    assert not FlociContainer().with_docker_socket(False).needs_docker_socket()
    assert without_socket_services().with_docker_socket(True).needs_docker_socket()


# --- core settings --------------------------------------------------------------------------


def test_service_config_exposes_its_ports() -> None:
    cfg = LambdaConfig(expose_runtime_ports=True)
    c = FlociContainer().with_service_config(cfg)
    # testcontainers keys ports by str or int depending on its version.
    ports = {str(port) for port in c.ports}
    assert str(cfg.runtime_api_base_port) in ports
    assert str(cfg.runtime_api_base_port + cfg.runtime_api_port_count - 1) in ports


def test_resource_namespace_is_unique_and_overridable() -> None:
    a, b = FlociContainer(), FlociContainer()
    assert a.get_resource_namespace().startswith("tc-")
    assert a.get_resource_namespace() != b.get_resource_namespace()
    assert a.env["FLOCI_DOCKER_RESOURCE_NAMESPACE"] == a.get_resource_namespace()
    assert a.with_resource_namespace("ci-42").get_resource_namespace() == "ci-42"


def test_log_level_uses_the_cloud_env_var() -> None:
    c = FlociContainer().with_log_level("DEBUG")
    assert c.env["QUARKUS_LOG_CATEGORY__IO_GITHUB_HECTORVENT__LEVEL"] == "DEBUG"


def test_fluent_core_methods_keep_the_aws_type() -> None:
    # The core's with_* methods return the concrete container, so AWS methods chain after them.
    c = FlociContainer().with_dedicated_network().with_log_level("INFO").with_region("eu-west-1")
    assert isinstance(c, FlociContainer)
    assert c.get_region() == "eu-west-1"


# --- HTTPS readiness ------------------------------------------------------------------------


def test_https_wait_only_while_tls_is_enabled() -> None:
    assert AWS.tls_enabled_env == "FLOCI_TLS_ENABLED"
    c = FlociContainer()
    assert not c.needs_https_wait()
    assert c.with_tls_config(TlsConfig(enabled=True)).needs_https_wait()
    assert not c.with_tls_config(TlsConfig(enabled=False)).needs_https_wait()
    # From the final environment, however TLS was switched on.
    assert c.with_env("FLOCI_TLS_ENABLED", "TRUE").needs_https_wait()
    assert not c.with_env("FLOCI_TLS_ENABLED", "false").needs_https_wait()


def test_tls_env_follows_the_descriptor_prefix() -> None:
    other = CloudDescriptor(
        name="x",
        image="floci/x",
        port=1,
        env_prefix="FLOCI_X_",
        health_path="/health",
        reset_path=None,
        log_level_env="LOG",
    )
    assert other.tls_enabled_env == "FLOCI_X_TLS_ENABLED"
    assert not other.tls_enabled({})
    assert other.tls_enabled({"FLOCI_X_TLS_ENABLED": "true"})
    assert not other.tls_enabled({"FLOCI_TLS_ENABLED": "true"})


class _Response:
    status = 200

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_https_wait_polls_the_health_path_until_it_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ssl
    import urllib.error

    calls: list[tuple[str, ssl.SSLContext]] = []

    def urlopen(url: str, timeout: float, context: ssl.SSLContext) -> _Response:
        calls.append((url, context))
        if len(calls) < 3:  # the window in which the port accepts but TLS is not up yet
            raise urllib.error.URLError(ssl.SSLEOFError("EOF occurred in violation of protocol"))
        return _Response()

    c = FlociContainer()
    monkeypatch.setattr(c, "get_endpoint", lambda: "http://localhost:32768")
    monkeypatch.setattr("floci.core.container.urllib.request.urlopen", urlopen)
    monkeypatch.setattr("floci.core.container.time.sleep", lambda seconds: None)

    c._wait_for_https()

    assert [url for url, _ in calls] == ["https://localhost:32768/_floci/health"] * 3
    # The probe only asks whether TLS answers; it trusts no particular certificate.
    assert calls[0][1].verify_mode == ssl.CERT_NONE


def test_https_wait_gives_up_after_the_startup_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen(url: str, timeout: float, context: object) -> _Response:
        raise ConnectionResetError("reset")

    class Impatient(FlociContainer):
        STARTUP_TIMEOUT = 0

    c = Impatient()
    monkeypatch.setattr(c, "get_endpoint", lambda: "http://localhost:32768")
    monkeypatch.setattr("floci.core.container.urllib.request.urlopen", urlopen)

    with pytest.raises(TimeoutError, match="HTTPS endpoint not ready within 0 seconds"):
        c._wait_for_https()


@pytest.mark.integration
def test_https_answers_as_soon_as_a_tls_container_has_started() -> None:
    # The port answers plain HTTP before it completes TLS handshakes; start() must cover both.
    with FlociContainer(TEST_IMAGE).with_tls_config(TlsConfig(enabled=True)) as floci:
        url = "https" + floci.get_endpoint()[len("http") :] + "/_floci/health"
        assert https_status(url) == 200


@pytest.mark.integration
def test_reset_wipes_state_and_keeps_serving() -> None:
    import boto3

    with FlociContainer(TEST_IMAGE) as floci:
        sqs = boto3.client(
            "sqs",
            endpoint_url=floci.get_endpoint(),
            region_name=floci.get_region(),
            aws_access_key_id=floci.get_access_key(),
            aws_secret_access_key=floci.get_secret_key(),
        )
        sqs.create_queue(QueueName="before-reset")

        floci.reset()

        assert sqs.list_queues().get("QueueUrls", []) == []
        sqs.create_queue(QueueName="after-reset")


def test_descriptor_keeps_its_positional_fields() -> None:
    # New descriptor fields go last, so callers passing the earlier ones positionally keep working.
    d = CloudDescriptor("x", "img", 1, "X_", "/h", None, "LOG", (), {"K": "v"})
    assert d.default_env == {"K": "v"}
    assert d.host_settings == ()
