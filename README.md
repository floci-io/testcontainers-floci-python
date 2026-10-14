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
emulator's environment variables. `FlociAzContainer` does the same for the Floci Azure emulator, with a storage
connection string and endpoints for the Azure SDKs, and `FlociGcpContainer` for the Floci GCP emulator, with the
`*_EMULATOR_HOST` variables Google's SDKs read, and `FlociOciContainer` for the Floci OCI emulator, with a ready
SDK config and signing key. No cloud account, no auth token.

See the [Floci documentation](https://floci.io/floci/services/) for the full list of emulated AWS services, and
[floci-az](https://github.com/floci-io/floci-az), [floci-gcp](https://github.com/floci-io/floci-gcp) and
[floci-oci](https://github.com/floci-io/floci-oci) for the Azure, GCP and OCI ones.

### The Floci emulators

testcontainers-floci-python is the Python member of the [Floci](https://github.com/floci-io) Testcontainers family.
Floci is named after [floccus](https://en.wikipedia.org/wiki/Cirrocumulus_floccus), the cloud formation that looks
like popcorn.

| Emulator                                           | Cloud | Port | Supported                                                                  |
|----------------------------------------------------|-------|:----:|:--------------------------------------------------------------------------:|
| [floci](https://github.com/floci-io/floci)         | AWS   | 4566 | ✅ [`testcontainers-floci`](https://pypi.org/project/testcontainers-floci/) |
| [floci-az](https://github.com/floci-io/floci-az)   | Azure | 4577 | ✅ [`testcontainers-floci`](https://pypi.org/project/testcontainers-floci/) |
| [floci-gcp](https://github.com/floci-io/floci-gcp) | GCP   | 4588 | ✅ [`testcontainers-floci`](https://pypi.org/project/testcontainers-floci/) |
| [floci-oci](https://github.com/floci-io/floci-oci) | OCI   | 4599 | ✅ [`testcontainers-floci`](https://pypi.org/project/testcontainers-floci/) |

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

### Azure

`FlociAzContainer`, in `floci.az`, starts the Floci Azure emulator (`floci/floci-az`). Point the Azure SDKs at it
with the storage connection string, or with the endpoint of one service:

```python
from azure.storage.blob import BlobServiceClient
from floci.az import FlociAzContainer


def test_blob():
    with FlociAzContainer() as floci:
        service = BlobServiceClient.from_connection_string(floci.get_storage_connection_string())
        container = service.create_container("uploads")
        container.upload_blob("hello.txt", b"hello")
        assert container.download_blob("hello.txt").readall() == b"hello"
```

The Azure SDK packages (`azure-storage-blob`, `azure-storage-queue`, …) are yours to install; this module does not
depend on them.

### GCP

`FlociGcpContainer`, in `floci.gcp`, starts the Floci GCP emulator (`floci/floci-gcp`). `get_emulator_env()` returns
the environment variables Google's client libraries read to find an emulator; set them before creating a client:

```python
import pytest

from floci.gcp import FlociGcpContainer
from google.cloud import storage


def test_bucket(monkeypatch: pytest.MonkeyPatch):
    with FlociGcpContainer() as floci:
        # monkeypatch restores the variables after the test, so no later test inherits a
        # stopped emulator's address.
        for key, value in floci.get_emulator_env().items():
            monkeypatch.setenv(key, value)
        client = storage.Client()
        bucket = client.create_bucket("uploads")
        bucket.blob("hello.txt").upload_from_string(b"hello")
        assert bucket.blob("hello.txt").download_as_bytes() == b"hello"
```

A service without an emulator variable (BigQuery, Cloud Tasks, Cloud KMS, Cloud Logging, …) takes the endpoint
when you build its client: `get_endpoint()` for REST, `get_emulator_host()` (`host:port`) for a plaintext gRPC
channel. The Google client libraries are yours to install; this module does not depend on them.

### OCI

`FlociOciContainer`, in `floci.oci`, starts the Floci OCI emulator (`floci/floci-oci`). OCI SDKs sign every request
with an API key; the emulator reads the tenancy and user from the signature and never verifies it, so the
container hands out a throwaway RSA key. `get_config()` is a ready config for the OCI Python SDK:

```python
import oci
from floci.oci import FlociOciContainer


def test_bucket():
    with FlociOciContainer() as floci:
        client = oci.object_storage.ObjectStorageClient(
            floci.get_config(), service_endpoint=floci.get_endpoint()
        )
        client.create_bucket(
            floci.get_namespace(),
            oci.object_storage.models.CreateBucketDetails(
                name="uploads", compartment_id=floci.get_tenancy_id()
            ),
        )
        client.put_object(floci.get_namespace(), "uploads", "hello.txt", b"hello")
```

Generating the key needs the [`cryptography`](https://pypi.org/project/cryptography/) package, which is not a
dependency of this module. The `oci` SDK installs it; without the SDK, install `testcontainers-floci[oci]`, or
pass a key of your own with `with_private_key_pem(...)`.

For the OCI CLI, or an SDK that reads `~/.oci/config`, write the key and a profile to files:

```python
key_file = tmp_path / "floci_key.pem"
key_file.write_text(floci.get_private_key_pem())
config_file = tmp_path / "config"
config_file.write_text(floci.get_config_file_contents(str(key_file), profile="FLOCI"))
# oci --config-file <config_file> --profile FLOCI os ns get --endpoint <floci.get_endpoint()>
```

## Service configuration

Each AWS service emulated by Floci can be configured individually using a typed config dataclass passed to the
matching `with_*_config(...)` method on `FlociContainer`. Every service config supports at least an `enabled` flag;
some services expose additional settings. See the [Floci documentation](https://floci.io/floci/services/) for the
full list of supported services.

Passing a config again replaces the earlier one for that service, on every container in this module: a setting the
earlier config wrote and the new one does not is removed from the environment (back to the container's default
where it has one), so `with_x_config(XConfig())` really is the default setup. A variable you changed yourself with
`with_env(...)` afterwards is left alone.

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

The container sets `FLOCI_SERVICES_RDS_ENDPOINT_HOST` to the Docker host, so `describe_db_instances` returns an
endpoint (host and published proxy port) that a client on the host can connect to, on Linux, macOS and Windows
alike. Set `RdsConfig(endpoint_host=...)` to advertise another hostname.

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

With TLS enabled the emulator port answers both HTTP and HTTPS. `start()` then waits for the health path over
HTTPS as well as over HTTP (without checking the certificate), because the port accepts plain HTTP shortly before
it completes TLS handshakes. That holds for every container in this module, and however TLS was switched on
(`TlsConfig` or the `..._TLS_ENABLED` variable).

### Azure services

Azure service configs live in `floci.az.config`, one per service of the emulator, each passed to the matching
`with_*_config(...)` method on `FlociAzContainer`. Every one has an `enabled` flag; the container-backed services
also have `mocked`, which keeps the emulator from starting a sibling container for them.

```python
from floci.az import FlociAzContainer
from floci.az.config import CosmosConfig, FunctionsConfig, ServiceBusConfig, SqlConfig

container = (
    FlociAzContainer()
    .with_service_bus_config(ServiceBusConfig(mocked=False))  # a real broker in a sibling container
    .with_functions_config(FunctionsConfig(enabled=False))
    .with_cosmos_config(CosmosConfig(mongodb_enabled=True))
    .with_sql_config(SqlConfig(data_plane_provider="managed", accept_eula="Y"))
)
```

| Config class | Azure service | `mocked` (default) |
|---|---|---|
| `AciConfig` | Container Instances | yes (`True`) |
| `AcrConfig` | Container Registry | yes (`False`) |
| `AksConfig` | Kubernetes Service | yes (`False`) |
| `ApimConfig` | API Management | |
| `AppConfigConfig` | App Configuration | |
| `ArmConfig` | Resource Manager | |
| `BlobConfig` | Blob Storage | |
| `ContainerAppsConfig` | Container Apps | yes (`True`) |
| `CosmosConfig` | Cosmos DB | yes (`False`) |
| `EmailConfig` | Communication Services Email | |
| `EntraConfig` | Microsoft Entra ID | |
| `EventGridConfig` | Event Grid | |
| `EventHubConfig` | Event Hubs | yes (`False`) |
| `FunctionsConfig` | Functions | yes (`False`) |
| `GraphConfig` | Microsoft Graph | |
| `KeyVaultConfig` | Key Vault | |
| `ManagedIdentityConfig` | Managed Identity | |
| `MariaDbConfig` | Database for MariaDB | yes (`False`) |
| `MonitorConfig` | Monitor | |
| `MySqlConfig` | Database for MySQL | yes (`False`) |
| `NetworkConfig` | Virtual networks and DNS | |
| `PolicyConfig` | Policy (emulator releases after 0.14.0) | |
| `PostgresConfig` | Database for PostgreSQL | yes (`False`) |
| `QueueConfig` | Queue Storage | |
| `RedisConfig` | Cache for Redis | yes (`False`) |
| `ServiceBusConfig` | Service Bus | yes (`True`) |
| `SignalRConfig` | SignalR Service | |
| `SqlConfig` | SQL Database | |
| `TableConfig` | Table Storage | |
| `VmConfig` | Virtual Machines | yes (`True`) |

`CosmosConfig` also takes `engine_startup` (`on-demand`, `eager` or `disabled`) and a switch per container-backed
engine (`mongodb_enabled`, `postgresql_enabled`, `cassandra_enabled`, `gremlin_enabled`). `SqlConfig` takes
`data_plane_provider` (`none`, `managed` or `external`) and `accept_eula`. Any other emulator setting can be set
with `with_env("FLOCI_AZ_SERVICES_<SERVICE>_<SETTING>", ...)`. TLS uses `TlsConfig` (`with_tls_config(...)`), also
in `floci.az.config`.

### GCP services

GCP service configs live in `floci.gcp.config`, one per service of the emulator, each passed to the matching
`with_*_config(...)` method on `FlociGcpContainer`. Every one has an `enabled` flag; the container-backed services
also have `mock` (default `False`), which keeps the emulator from starting a sibling container for them.

```python
from floci.gcp import FlociGcpContainer
from floci.gcp.config import BigQueryConfig, CloudSqlConfig, GkeConfig

container = (
    FlociGcpContainer()
    .with_gke_config(GkeConfig(enabled=False))
    .with_cloudsql_config(CloudSqlConfig(mock=True))  # control plane only, no database container
    .with_bigquery_config(BigQueryConfig(mock=True))  # built-in SQL subset instead of DuckDB
)
```

| Config class | GCP service | `mock` |
|---|---|---|
| `BigQueryConfig` | BigQuery | yes |
| `CloudFunctionsConfig` | Cloud Functions | |
| `CloudRunConfig` | Cloud Run | yes |
| `CloudSqlConfig` | Cloud SQL | yes |
| `CloudTasksConfig` | Cloud Tasks | |
| `ComputeConfig` | Compute Engine | |
| `DatastoreConfig` | Datastore | |
| `EventarcConfig` | Eventarc | |
| `FirebaseAuthConfig` | Firebase Authentication | |
| `FirestoreConfig` | Firestore | |
| `GcsConfig` | Cloud Storage | |
| `GkeConfig` | Kubernetes Engine | yes |
| `IamConfig` | IAM | |
| `IamCredentialsConfig` | IAM Service Account Credentials | |
| `KafkaConfig` | Managed Service for Apache Kafka | yes |
| `KmsConfig` | Cloud KMS | |
| `LoggingConfig` | Cloud Logging | |
| `MonitoringConfig` | Cloud Monitoring | |
| `PubSubConfig` | Pub/Sub | |
| `ResourceManagerConfig` | Resource Manager | |
| `SchedulerConfig` | Cloud Scheduler | |
| `SecretManagerConfig` | Secret Manager | |
| `ServiceUsageConfig` | Service Usage | |
| `StsConfig` | Security Token Service | |

The method is named after the emulator's service token: `with_cloudsql_config`, `with_secretmanager_config`,
`with_pubsub_config`. Any other emulator setting can be set with
`with_env("FLOCI_GCP_SERVICES_<SERVICE>_<SETTING>", ...)`. TLS uses `TlsConfig` (`with_tls_config(...)`), also in
`floci.gcp.config`.

### OCI services

OCI service configs live in `floci.oci.config` and work the same way on `FlociOciContainer`: an `enabled` flag
each, and `mock` (default `False`) on the container-backed ones.

```python
from floci.oci import FlociOciContainer
from floci.oci.config import FunctionsConfig, OkeConfig

container = (
    FlociOciContainer()
    .with_functions_config(FunctionsConfig(mock=True))  # no Fn server container
    .with_oke_config(OkeConfig(enabled=False))
)
```

| Config class | OCI service | `mock` |
|---|---|---|
| `FunctionsConfig` | Functions | yes |
| `IdentityConfig` | Identity and Access Management | |
| `KmsConfig` | Key Management | |
| `ObjectStorageConfig` | Object Storage | |
| `OkeConfig` | Container Engine for Kubernetes | yes |
| `QueueConfig` | Queue | |
| `StreamingConfig` | Streaming | |
| `VaultConfig` | Vault | |

Any other emulator setting can be set with `with_env("FLOCI_OCI_SERVICES_<SERVICE>_<SETTING>", ...)`. TLS uses
`TlsConfig` (`with_tls_config(...)`), also in `floci.oci.config`.

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
| `with_docker_socket(bool)`       | Forces the host Docker socket on or off, overriding detection (see below)                     |
| `with_resource_namespace(str)`   | Overrides the generated prefix of sibling container names                                     |
| `with_tls_config(TlsConfig)`     | Configures TLS/HTTPS                                                                          |
| `with_storage_config(StorageConfig)` | Configures persistent storage and volume behaviour                                    |

#### Docker socket

Docker-backed services (Lambda, RDS, ElastiCache, ECS, EC2, EKS, ECR, MSK, OpenSearch, Athena, CodeBuild,
Neptune) start sibling containers and need the host Docker socket (`/var/run/docker.sock`). It is mounted only while at least one
of them is enabled and not in `mock` mode, decided from the final environment when the container starts. All
services are enabled by default, so a default container gets the socket. Use `with_docker_socket(False)` on hosts
where the socket cannot be mounted (rootless Podman with SELinux, some CI sandboxes), or `with_docker_socket(True)`
to always mount it.

Each container also gets a unique `FLOCI_DOCKER_RESOURCE_NAMESPACE` (`tc-…`), so sibling containers of parallel
test runs never collide by name.

Floci manages the sibling containers it spawns; the testcontainers reaper does not track them. `stop()` (and so
leaving a `with` block) removes every one of them after stopping Floci, found by the `floci_namespace` label that
holds the namespace (`get_resource_namespace()`). Containers that share a namespace lose their siblings together.

On Azure the same rule holds for `FlociAzContainer`: ACR, AKS, Event Hubs, Functions, MariaDB, MySQL, PostgreSQL
and Redis need the socket while enabled and not `mocked`. Service Bus, Container Instances, Virtual Machines and
Container Apps are mocked by default and need it only with `mocked=False`. Cosmos DB needs it only for an enabled
container-backed engine (and never with `engine_startup="disabled"`), SQL Database only with the `managed`
data-plane provider. The namespace variable there is `FLOCI_AZ_DOCKER_RESOURCE_NAMESPACE`.

On GCP (`FlociGcpContainer`), GKE, Cloud SQL, Cloud Run, Managed Kafka and BigQuery need the socket while enabled
and not `mock`; BigQuery does not when `FLOCI_GCP_SERVICES_BIGQUERY_DUCK_URL` names a running DuckDB sidecar. The
namespace variable is `FLOCI_GCP_DOCKER_RESOURCE_NAMESPACE`.

On OCI (`FlociOciContainer`), Functions and OKE need the socket while enabled and not `mock`. The namespace
variable is `FLOCI_OCI_DOCKER_RESOURCE_NAMESPACE`.

#### Resetting state

`reset()` wipes all emulator state (buckets, queues, tables, …) without restarting the container, which is
handy when one container is shared across tests.

#### Module layout

The AWS module lives in `floci.aws` (`from floci.aws import FlociContainer`, `from floci.aws.config import
S3Config`). The shorter `floci` and `floci.config` imports used throughout this README keep working as aliases.
The Azure module lives in `floci.az` (`from floci.az import FlociAzContainer`, `from floci.az.config import
BlobConfig`), the GCP module in `floci.gcp` (`from floci.gcp import FlociGcpContainer`, `from floci.gcp.config
import GcsConfig`), the OCI module in `floci.oci` (`from floci.oci import FlociOciContainer`, `from
floci.oci.config import ObjectStorageConfig`). All are built on `floci.core`.

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

`FlociAzContainer` shares the core methods above (`with_log_level`, `with_dedicated_network`, `with_docker_socket`,
`with_resource_namespace`, `reset`, `get_endpoint`, `get_dedicated_network_name`) and has its own connection details:

| Method | Returns |
|---|---|
| `get_endpoint()` | `http://host:port` of the emulator |
| `get_https_endpoint()` | `https://host:port`, the same port; answers once TLS is enabled with `TlsConfig(enabled=True)` |
| `get_tls_certificate()` | PEM certificate to trust for the HTTPS endpoint |
| `get_subscription_id()` | Subscription ID (`00000000-0000-0000-0000-000000000001`) |
| `get_tenant_id()` | Entra tenant ID (`00000000-0000-0000-0000-000000000002`) |
| `get_account_name()` | Storage account name (`devstoreaccount1`) |
| `get_account_key()` | Storage account key |
| `get_blob_endpoint()` | Blob endpoint, `http://host:port/devstoreaccount1` |
| `get_queue_endpoint()` | Queue endpoint, `http://host:port/devstoreaccount1-queue` |
| `get_table_endpoint()` | Table endpoint, `http://host:port/devstoreaccount1-table` |
| `get_storage_connection_string()` | Connection string for the Azure Storage SDKs (Blob, Queue, Table) |

`FlociGcpContainer` shares the same core methods and has these:

| Method | Returns |
|---|---|
| `get_endpoint()` | `http://host:port` of the emulator |
| `get_emulator_host()` | `host:port`, the form the `*_EMULATOR_HOST` variables take |
| `get_emulator_env()` | The variables that point Google's SDKs at the emulator (see below) |
| `get_project_id()` | Default project (`floci-local`; `with_project_id(...)` changes it, and any project ID is accepted) |
| `get_https_endpoint()` | `https://host:port`, the same port; answers once TLS is enabled with `TlsConfig(enabled=True)` |
| `get_tls_certificate()` | PEM certificate to trust for the HTTPS endpoint |

`get_emulator_env()` holds `PUBSUB_EMULATOR_HOST`, `FIRESTORE_EMULATOR_HOST`, `DATASTORE_EMULATOR_HOST`,
`SECRET_MANAGER_EMULATOR_HOST`, `FIREBASE_AUTH_EMULATOR_HOST`, `LOGGING_EMULATOR_HOST`, `KMS_EMULATOR_HOST` and
`STORAGE_EMULATOR_HOST_GRPC` as `host:port`, `STORAGE_EMULATOR_HOST` as `http://host:port`, and
`GOOGLE_CLOUD_PROJECT`. The Logging and KMS variables are a floci-gcp convention; Google's client libraries do not
read them.

`FlociOciContainer` shares the same core methods and has these:

| Method | Returns |
|---|---|
| `get_endpoint()` | `http://host:port` of the emulator, the `service_endpoint` of every client |
| `get_region()` | Region (`us-ashburn-1`; `with_region(...)` changes it) |
| `get_tenancy_id()` | Tenancy OCID, also the root compartment (`with_tenancy_id(...)` changes it) |
| `get_namespace()` | Object Storage namespace (`floci-local`; `with_namespace(...)` changes it) |
| `get_user_id()` | User OCID to sign as |
| `get_fingerprint()` | API key fingerprint to sign with (a placeholder; the emulator checks none) |
| `get_private_key_pem()` | The container's throwaway RSA signing key, PKCS#8 PEM, generated on first use |
| `get_config()` | Config dict for the OCI Python SDK, with the key inline as `key_content` |
| `get_config_file_contents(key_file, profile="DEFAULT")` | One profile of an OCI config file, naming the key at `key_file` |
| `get_https_endpoint()` | `https://host:port`, the same port; answers once TLS is enabled with `TlsConfig(enabled=True)` |

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

Every emulator publishes `latest`, `x.y.z` and `nightly` tags; `FlociAzContainer` defaults to
`floci/floci-az:latest`, `FlociGcpContainer` to `floci/floci-gcp:latest`, `FlociOciContainer` to
`floci/floci-oci:latest`, and each takes an image the same way.

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
