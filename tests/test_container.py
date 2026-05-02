"""Integration tests for FlociContainer.

Run with Docker available:
    pytest -m integration

Skip Docker tests (CI without Docker):
    pytest -m "not integration"
"""

import pytest

from floci import FlociContainer
from floci.config import (
    DynamoDbConfig,
    S3Config,
    SnsConfig,
    SqsConfig,
)


def test_default_values() -> None:
    container = FlociContainer()
    assert container.PORT == 4566
    assert container.get_region() == "us-east-1"
    assert container.get_access_key() == "test"
    assert container.get_secret_key() == "test"
    assert container.get_account_id() == "000000000000"


def test_fluent_region() -> None:
    container = FlociContainer().with_region("eu-west-1")
    assert container.get_region() == "eu-west-1"


def test_fluent_account_id() -> None:
    container = FlociContainer().with_account_id("111122223333")
    assert container.get_account_id() == "111122223333"


def test_dedicated_network_set() -> None:
    container = FlociContainer().with_dedicated_network()
    assert container.get_dedicated_network_name() is not None


def test_service_configs_apply_without_error() -> None:
    (
        FlociContainer()
        .with_s3_config(S3Config(enabled=True, default_presign_expiry_seconds=7200))
        .with_sqs_config(SqsConfig(enabled=True, default_visibility_timeout=60))
        .with_sns_config(SnsConfig(enabled=True))
        .with_dynamo_db_config(DynamoDbConfig(enabled=True))
    )


@pytest.mark.integration
def test_container_starts_and_is_healthy() -> None:
    with FlociContainer() as floci:
        import urllib.request

        url = f"{floci.get_endpoint()}/_floci/health"
        with urllib.request.urlopen(url, timeout=5) as resp:
            assert resp.status == 200


@pytest.mark.integration
def test_s3_create_bucket() -> None:
    import boto3

    with FlociContainer() as floci:
        s3 = boto3.client(
            "s3",
            endpoint_url=floci.get_endpoint(),
            region_name=floci.get_region(),
            aws_access_key_id=floci.get_access_key(),
            aws_secret_access_key=floci.get_secret_key(),
        )
        s3.create_bucket(Bucket="my-test-bucket")
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
        assert "my-test-bucket" in buckets


@pytest.mark.integration
def test_sqs_send_receive_message() -> None:
    import boto3

    with FlociContainer() as floci:
        sqs = boto3.client(
            "sqs",
            endpoint_url=floci.get_endpoint(),
            region_name=floci.get_region(),
            aws_access_key_id=floci.get_access_key(),
            aws_secret_access_key=floci.get_secret_key(),
        )
        queue = sqs.create_queue(QueueName="test-queue")
        url = queue["QueueUrl"]
        sqs.send_message(QueueUrl=url, MessageBody="hello floci")
        messages = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
        assert messages["Messages"][0]["Body"] == "hello floci"


@pytest.mark.integration
def test_dynamodb_create_table() -> None:
    import boto3

    with FlociContainer() as floci:
        ddb = boto3.resource(
            "dynamodb",
            endpoint_url=floci.get_endpoint(),
            region_name=floci.get_region(),
            aws_access_key_id=floci.get_access_key(),
            aws_secret_access_key=floci.get_secret_key(),
        )
        table = ddb.create_table(
            TableName="users",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        assert table.table_status == "ACTIVE"
