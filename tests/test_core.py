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
)
from floci.core import FlociBaseContainer


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
    assert str(cfg.runtime_api_base_port) in c.ports
    assert str(cfg.runtime_api_base_port + cfg.runtime_api_port_count - 1) in c.ports


def test_resource_namespace_is_unique_and_overridable() -> None:
    a, b = FlociContainer(), FlociContainer()
    assert a.get_resource_namespace().startswith("tc-")
    assert a.get_resource_namespace() != b.get_resource_namespace()
    assert a.env["FLOCI_DOCKER_RESOURCE_NAMESPACE"] == a.get_resource_namespace()
    assert a.with_resource_namespace("ci-42").get_resource_namespace() == "ci-42"


def test_log_level_uses_the_cloud_env_var() -> None:
    c = FlociContainer().with_log_level("DEBUG")
    assert c.env["QUARKUS_LOG_CATEGORY__IO_GITHUB_HECTORVENT__LEVEL"] == "DEBUG"
