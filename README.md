<p align="center">
  <img src="https://raw.githubusercontent.com/floci-io/.github/main/floci.svg#gh-light-mode-only" alt="Floci" width="500" />
  <img src="https://github.com/user-attachments/assets/edfff8b3-926c-471e-9549-77fb90a21b49#gh-dark-mode-only" alt="Floci" width="500" />
</p>

<p align="center">
  <strong>Any Cloud. Locally.</strong><br />
  Light, fluffy, and always free: Testcontainers for Python<br />
  No account. No auth token. No feature gates.
</p>

<p align="center">
  <a href="https://pypi.org/project/testcontainers-floci/"><img src="https://img.shields.io/pypi/v/testcontainers-floci?label=pypi&color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/testcontainers-floci/"><img src="https://img.shields.io/pypi/pyversions/testcontainers-floci" alt="Python versions"></a>
  <a href="https://github.com/floci-io/testcontainers-floci-python/actions/workflows/ci.yml"><img src="https://github.com/floci-io/testcontainers-floci-python/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <a href="https://github.com/floci-io/testcontainers-floci-python/stargazers"><img src="https://img.shields.io/github/stars/floci-io/testcontainers-floci-python?style=flat" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#service-configuration">Configuration</a> ·
  <a href="#the-floci-emulators">Emulators</a> ·
  <a href="https://floci.io/floci/testcontainers/python/">Docs</a>
</p>

---

## What is this?

A Python [Testcontainers](https://testcontainers.com/) module for [Floci](https://github.com/floci-io), the free,
open-source local cloud emulators. `FlociContainer` starts a Floci (AWS) emulator container for your integration tests
and gives you an endpoint and credentials to point boto3 at, plus typed, per-service config dataclasses over the
emulator's environment variables. No cloud account, no auth token.

See the [Floci documentation](https://floci.io/floci/services/) for the full list of emulated AWS services.

### The Floci emulators

testcontainers-floci-python is the Python member of the [Floci](https://github.com/floci-io) Testcontainers family.
Floci is named after [floccus](https://en.wikipedia.org/wiki/Cirrocumulus_floccus), the cloud formation that looks
like popcorn.

| Emulator                                           | Cloud | Port | Supported                                                                  |
|----------------------------------------------------|-------|:----:|:--------------------------------------------------------------------------:|
| [floci](https://github.com/floci-io/floci)         | AWS   | 4566 | ✅ [`testcontainers-floci`](https://pypi.org/project/testcontainers-floci/) |
| [floci-az](https://github.com/floci-io/floci-az)   | Azure | 4577 | Planned                                                                    |
| [floci-gcp](https://github.com/floci-io/floci-gcp) | GCP   | 4588 | Planned                                                                    |
| [floci-oci](https://github.com/floci-io/floci-oci) | OCI   | 4599 | Planned                                                                    |

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

### Using pytest fixtures

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

Each AWS service emulated by Floci can be configured individually using a typed config dataclass passed to the
matching `with_*_config(...)` method on `FlociContainer`. Every service config supports at least an `enabled` flag;
some services expose additional settings. See the [Floci documentation](https://floci.io/floci/services/) for the
full list of supported services.

### Examples

#### S3

```python
from floci import FlociContainer
from floci.config import S3Config

container = FlociContainer().with_s3_config(
    S3Config(enabled=True, default_presign_expiry_seconds=7200)
)
```

#### SQS

```python
from floci.config import SqsConfig

container = FlociContainer().with_sqs_config(
    SqsConfig(enabled=True, default_visibility_timeout=60, max_message_size=262144)
)
```

#### DynamoDB

```python
from floci.config import DynamoDbConfig

container = FlociContainer().with_dynamo_db_config(DynamoDbConfig(enabled=True))
```

#### Lambda

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

#### RDS (PostgreSQL / MySQL / MariaDB)

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

#### ElastiCache (Redis / Valkey)

```python
from floci.config import ElastiCacheConfig

container = FlociContainer().with_elasti_cache_config(
    ElastiCacheConfig(enabled=True, default_image="valkey/valkey:8")
)
```

#### OpenSearch

```python
from floci.config import OpenSearchConfig

container = FlociContainer().with_open_search_config(OpenSearchConfig(enabled=True, mock=False))
```

#### MSK (Kafka via Redpanda)

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
| `BackupConfig` | AWS Backup |
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
| `Route53Config` | Route 53 |
| `S3Config` | S3 |
| `SchedulerConfig` | EventBridge Scheduler |
| `SecretsManagerConfig` | Secrets Manager |
| `SesConfig` | SES |
| `SesV2Config` | SES v2 |
| `SnsConfig` | SNS |
| `SqsConfig` | SQS |
| `SsmConfig` | SSM Parameter Store |
| `StepFunctionsConfig` | Step Functions |
| `TextractConfig` | Textract |
| `TransferFamilyConfig` | Transfer Family |

Cross-cutting settings use `TlsConfig` (`with_tls_config(...)`) and `StorageConfig` (`with_storage_config(...)`),
both importable from `floci.config`.

## Container options

```python
container = (
    FlociContainer(image="floci/floci:latest")  # pin a specific tag
    .with_region("eu-west-1")
    .with_account_id("111122223333")
    .with_availability_zone("eu-west-1a")
    .with_dedicated_network()  # isolated Docker network for stateful services
)
```

| Method                           | Description                                                                                   |
|----------------------------------|-----------------------------------------------------------------------------------------------|
| `FlociContainer(image=...)`      | Creates a container; the default image is `floci/floci:latest`                                |
| `with_region(str)`               | Sets the AWS region (default: `us-east-1`)                                                    |
| `with_account_id(str)`           | Sets the default AWS account ID (default: `000000000000`)                                     |
| `with_availability_zone(str)`    | Sets the default availability zone (default: `us-east-1a`)                                    |
| `with_access_key(str)`           | Sets the access key returned by `get_access_key()` (default: `test`)                          |
| `with_secret_key(str)`           | Sets the secret key returned by `get_secret_key()` (default: `test`)                          |
| `with_log_level(str)`            | Sets the Floci log level (e.g. `DEBUG`, `INFO`, `WARN`, `ERROR`)                              |
| `with_dedicated_network()`       | Creates a dedicated Docker network shared by Floci and its sibling containers (RDS, Lambda, …) |
| `with_tls_config(TlsConfig)`     | Configures TLS/HTTPS                                                                          |
| `with_storage_config(StorageConfig)` | Configures persistent storage and volume behaviour                                    |

The host Docker socket (`/var/run/docker.sock`) is mounted into the container so that Docker-backed services
(RDS, Lambda, ElastiCache, …) can start their sibling containers.

### Connection details

| Method | Returns |
|---|---|
| `get_endpoint()` | `http://host:port` — pass as `endpoint_url` to boto3 |
| `get_region()` | AWS region string (`"us-east-1"` by default) |
| `get_access_key()` | Access key (`"test"` by default) |
| `get_secret_key()` | Secret key (`"test"` by default) |
| `get_account_id()` | AWS account ID (`"000000000000"` by default) |
| `get_availability_zone()` | Default availability zone (`"us-east-1a"` by default) |
| `get_dedicated_network_name()` | Name of the dedicated Docker network, or `None` |

## Docker image tags

By default `FlociContainer` runs the floating `floci/floci:latest` tag, so you always test against the current
emulator. Pass an image to the constructor to pin a release or follow `main`:

```python
FlociContainer(image="floci/floci:x.y.z")  # a specific release
FlociContainer(image="floci/floci:nightly")  # built from main every night
```

| Tag                   | Description                       |
|-----------------------|-----------------------------------|
| `floci/floci:latest`  | Latest release (library default)  |
| `floci/floci:x.y.z`   | Pinned release                    |
| `floci/floci:nightly` | Built from `main` every night     |

Every emulator publishes `latest`, `x.y.z` and `nightly` tags.

## Requirements

- Python 3.9+
- Docker (running locally or in CI)
- `testcontainers >= 4.0.0`

## Building and testing

```bash
uv sync --extra dev
uv run ruff check . && uv run ruff format --check . && uv run mypy floci  # lint, format and type check, as CI runs them
uv run pytest -m "not integration"  # unit tests, no Docker needed
uv run pytest -m integration        # integration tests, starts real Floci containers
```

With pip instead of uv, run `pip install -e ".[dev]"` inside an activated virtualenv and drop the
`uv run` prefix.

Integration tests need Docker running. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor workflow.

## Other languages

| Language | Repository |
|---|---|
| Java | [testcontainers-floci](https://github.com/floci-io/testcontainers-floci) |
| Node.js / TypeScript | [testcontainers-floci-node](https://github.com/floci-io/testcontainers-floci-node) |
| Python | **testcontainers-floci-python** (this repo) |
| Go | [testcontainers-floci-go](https://github.com/floci-io/testcontainers-floci-go) |
| .NET | [testcontainers-floci-dotnet](https://github.com/floci-io/testcontainers-floci-dotnet) |

## Community

- 💬 [Slack](https://join.slack.com/t/floci/shared_invite/zt-3tjn02s3q-A00kEjJ1cZxsg_imTfy6Cw): quick questions and community chat
- 🗣️ [GitHub Discussions](https://github.com/orgs/floci-io/discussions): ideas, design tradeoffs, and proposals
- [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [MAINTAINERS.md](MAINTAINERS.md)

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

Floci™ is a trademark of Hector Ventura. Code is MIT-licensed; see
[TRADEMARK.md](https://github.com/floci-io/.github/blob/main/TRADEMARK.md) for name and logo use.

</div>
