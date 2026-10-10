"""Sibling cleanup and the RDS endpoint host, ported from the .NET and Go modules."""

from __future__ import annotations

import socket
import time
from typing import Any
from urllib.parse import urlparse

import pytest

from floci import FlociContainer
from floci.aws.config import RdsConfig
from floci.core import NAMESPACE_LABEL
from tests.images import TEST_IMAGE


class _Env:
    def __init__(self) -> None:
        self.env: dict[str, str] = {}

    def with_env(self, key: str, value: str) -> _Env:
        self.env[key] = value
        return self


def test_rds_endpoint_host_is_emitted_only_when_set() -> None:
    target: Any = _Env()
    RdsConfig().apply_to(target)
    assert "FLOCI_SERVICES_RDS_ENDPOINT_HOST" not in target.env

    RdsConfig(endpoint_host="rds.example.com").apply_to(target)
    assert target.env["FLOCI_SERVICES_RDS_ENDPOINT_HOST"] == "rds.example.com"


def test_host_settings_skip_disabled_or_explicit_services() -> None:
    c = FlociContainer().with_service_config(RdsConfig(enabled=False))
    c._set_host_settings()
    assert "FLOCI_SERVICES_RDS_ENDPOINT_HOST" not in c.env

    c = FlociContainer().with_service_config(RdsConfig(endpoint_host="rds.example.com"))
    c._set_host_settings()
    assert c.env["FLOCI_SERVICES_RDS_ENDPOINT_HOST"] == "rds.example.com"


def _siblings(namespace: str) -> int:
    import docker

    client = docker.from_env()
    try:
        return len(
            client.containers.list(all=True, filters={"label": f"{NAMESPACE_LABEL}={namespace}"})
        )
    finally:
        client.close()


def _client(floci: FlociContainer, service: str) -> Any:
    import boto3

    return boto3.client(
        service,
        endpoint_url=floci.get_endpoint(),
        region_name=floci.get_region(),
        aws_access_key_id=floci.get_access_key(),
        aws_secret_access_key=floci.get_secret_key(),
    )


@pytest.mark.integration
def test_stop_removes_sibling_containers() -> None:
    floci = FlociContainer(TEST_IMAGE).start()
    namespace = floci.get_resource_namespace()
    try:
        # CreateRepository makes Floci start its ECR registry as a sibling container.
        _client(floci, "ecr").create_repository(repositoryName="cleanup-test")
        assert _siblings(namespace) > 0
    finally:
        floci.stop()
    assert _siblings(namespace) == 0


@pytest.mark.integration
def test_rds_endpoint_is_reachable_from_the_host() -> None:
    # The proxy ports are published only when RDS is configured.
    rds_config = RdsConfig(proxy_base_port=7010, proxy_port_count=3)
    with FlociContainer(TEST_IMAGE).with_service_config(rds_config) as floci:
        rds = _client(floci, "rds")
        rds.create_db_instance(
            DBInstanceIdentifier="endpoint-test",
            DBInstanceClass="db.t3.micro",
            Engine="postgres",
            MasterUsername="admin",
            MasterUserPassword="password123",
            AllocatedStorage=20,
        )
        deadline = time.monotonic() + 120
        endpoint: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            instance = rds.describe_db_instances(DBInstanceIdentifier="endpoint-test")[
                "DBInstances"
            ][0]
            if instance.get("DBInstanceStatus") == "available" and instance.get("Endpoint"):
                endpoint = instance["Endpoint"]
                break
            time.sleep(2)
        assert endpoint is not None
        assert endpoint["Address"] == urlparse(floci.get_endpoint()).hostname
        with socket.create_connection((endpoint["Address"], endpoint["Port"]), timeout=5):
            pass
