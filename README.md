# testcontainers-floci

[![PyPI version](https://img.shields.io/pypi/v/testcontainers-floci.svg)](https://pypi.org/project/testcontainers-floci/)
[![Python versions](https://img.shields.io/pypi/pyversions/testcontainers-floci.svg)](https://pypi.org/project/testcontainers-floci/)
[![CI](https://github.com/floci-io/testcontainers-floci-python/actions/workflows/ci.yml/badge.svg)](https://github.com/floci-io/testcontainers-floci-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python [Testcontainers](https://testcontainers.com) module for [Floci](https://github.com/floci-io/floci) — the open-source, drop-in replacement for LocalStack Community Edition.

Floci emulates **41 AWS services** in a single container with:
- **~24 ms** startup time (native image)
- **~13 MiB** idle memory
- **~90 MB** Docker image
- No auth tokens, no feature gates, MIT license

## Installation

```bash
pip install testcontainers-floci
```

## Quick start

```python
import boto3
from floci import FlociContainer

def test_s3():
    with FlociContainer() as floci:
        s3 = boto3.client(
            "s3",
            endpoint_url=floci.get_endpoint(),
            region_name=floci.get_region(),
            aws_access_key_id=floci.get_access_key(),
            aws_secret_access_key=floci.get_secret_key(),
        )
        s3.create_bucket(Bucket="my-bucket")
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
        assert "my-bucket" in buckets
```

## Using pytest fixtures

```python
import pytest
import boto3
from floci import FlociContainer

@pytest.fixture(scope="session")
def floci():
    with FlociContainer() as container:
        yield container

@pytest.fixture
def s3_client(floci):
    return boto3.client(
        "s3",
        endpoint_url=floci.get_endpoint(),
        region_name=floci.get_region(),
        aws_access_key_id=floci.get_access_key(),
        aws_secret_access_key=floci.get_secret_key(),
        config=boto3.session.Config(s3={"addressing_style": "path"}),
    )

def test_upload(s3_client):
    s3_client.create_bucket(Bucket="uploads")
    s3_client.put_object(Bucket="uploads", Key="hello.txt", Body=b"hello")
    obj = s3_client.get_object(Bucket="uploads", Key="hello.txt")
    assert obj["Body"].read() == b"hello"
```

## Service configuration

Each of Floci's 41 services can be configured individually using typed config dataclasses.

### S3

```python
from floci import FlociContainer
from floci.config import S3Config

container = FlociContainer().with_s3_config(
    S3Config(enabled=True, default_presign_expiry_seconds=7200)
)
```

### SQS

```python
from floci.config import SqsConfig

container = FlociContainer().with_sqs_config(
    SqsConfig(enabled=True, default_visibility_timeout=60, max_message_size=262144)
)
```

### DynamoDB

```python
from floci.config import DynamoDbConfig

container = FlociContainer().with_dynamo_db_config(DynamoDbConfig(enabled=True))
```

### Lambda

```python
from floci.config import LambdaConfig

container = FlociContainer().with_lambda_config(
    LambdaConfig(
        enabled=True,
        default_memory_mb=256,
        default_timeout_seconds=30,
        hot_reload_enabled=True,
    )
)
```

### RDS (PostgreSQL / MySQL / MariaDB)

```python
from floci.config import RdsConfig

container = FlociContainer().with_rds_config(
    RdsConfig(
        enabled=True,
        default_postgres_image="postgres:16-alpine",
        proxy_base_port=7001,
    )
)
```

### ElastiCache (Redis / Valkey)

```python
from floci.config import ElastiCacheConfig

container = FlociContainer().with_elasti_cache_config(
    ElastiCacheConfig(enabled=True, default_image="valkey/valkey:8")
)
```

### OpenSearch

```python
from floci.config import OpenSearchConfig

container = FlociContainer().with_open_search_config(
    OpenSearchConfig(enabled=True, mock=False)
)
```

### MSK (Kafka via Redpanda)

```python
from floci.config import MskConfig

container = FlociContainer().with_msk_config(
    MskConfig(enabled=True, mock=False, default_image="redpandadata/redpanda:latest")
)
```

### All available config classes

| Config class | AWS service |
|---|---|
| `AcmConfig` | AWS Certificate Manager |
| `ApiGatewayConfig` | API Gateway (v1) |
| `ApiGatewayV2Config` | API Gateway (v2) |
| `AppConfigConfig` | AppConfig |
| `AppConfigDataConfig` | AppConfig Data |
| `AthenaConfig` | Athena |
| `BedrockRuntimeConfig` | Bedrock Runtime |
| `CloudFormationConfig` | CloudFormation |
| `CloudWatchLogsConfig` | CloudWatch Logs |
| `CloudWatchMetricsConfig` | CloudWatch Metrics |
| `CodeBuildConfig` | CodeBuild |
| `CodeDeployConfig` | CodeDeploy |
| `CognitoConfig` | Cognito |
| `DynamoDbConfig` | DynamoDB |
| `Ec2Config` | EC2 |
| `EcrConfig` | ECR |
| `EcsConfig` | ECS |
| `EksConfig` | EKS |
| `ElastiCacheConfig` | ElastiCache |
| `ElbV2Config` | ELB v2 |
| `EventBridgeConfig` | EventBridge |
| `FirehoseConfig` | Kinesis Firehose |
| `GlueConfig` | Glue |
| `IamConfig` | IAM |
| `KinesisConfig` | Kinesis |
| `KmsConfig` | KMS |
| `LambdaConfig` | Lambda |
| `MskConfig` | MSK (Kafka) |
| `OpenSearchConfig` | OpenSearch |
| `PipesConfig` | EventBridge Pipes |
| `RdsConfig` | RDS |
| `ResourceGroupsTaggingConfig` | Resource Groups Tagging |
| `S3Config` | S3 |
| `SchedulerConfig` | EventBridge Scheduler |
| `SecretsManagerConfig` | Secrets Manager |
| `SesConfig` | SES |
| `SesV2Config` | SES v2 |
| `SnsConfig` | SNS |
| `SqsConfig` | SQS |
| `SsmConfig` | SSM Parameter Store |
| `StepFunctionsConfig` | Step Functions |

## Container options

```python
container = (
    FlociContainer(image="floci/floci:latest")  # pin a specific tag
    .with_region("eu-west-1")
    .with_account_id("111122223333")
    .with_availability_zone("eu-west-1a")
    .with_dedicated_network()   # isolated Docker network for stateful services
)
```

### Connection details

| Method | Returns |
|---|---|
| `get_endpoint()` | `http://host:port` — pass as `endpoint_url` to boto3 |
| `get_region()` | AWS region string |
| `get_access_key()` | Access key (`"test"` by default) |
| `get_secret_key()` | Secret key (`"test"` by default) |
| `get_account_id()` | AWS account ID |

## Docker image variants

| Tag | Description |
|---|---|
| `floci/floci:latest` | Native image — sub-second startup (recommended) |
| `floci/floci:x.y.z` | Pinned release (native) |

## Requirements

- Python 3.9+
- Docker (running locally or in CI)
- `testcontainers >= 4.0.0`

## Related projects

- [Floci](https://github.com/floci-io/floci) — the emulator itself
- [testcontainers-floci](https://github.com/floci-io/testcontainer-floci) — Java / Spring Boot module
- [Testcontainers for Python](https://testcontainers-python.readthedocs.io)

## License

MIT
