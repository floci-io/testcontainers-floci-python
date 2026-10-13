"""Service configuration dataclasses for FlociGcpContainer.

One dataclass per service of the GCP emulator, each an enabled switch plus a ``mock``
switch where the emulator has one. ``TOKEN`` is the emulator's name for the service in
``FLOCI_GCP_SERVICES_<TOKEN>_<SETTING>``. ``..._ENABLED`` is always emitted, every other
setting only while the service is enabled. Defaults equal the emulator's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from floci.core import env_value

if TYPE_CHECKING:
    from floci.gcp.container import FlociGcpContainer

_PREFIX = "FLOCI_GCP_SERVICES_"


@dataclass
class GcpServiceConfig:
    """A service of the GCP emulator that can be switched on or off."""

    TOKEN: ClassVar[str]

    enabled: bool = True

    def settings(self) -> dict[str, object]:
        """The settings beyond ``ENABLED``, by setting name; emitted only while enabled."""
        return {}

    def apply_to(self, c: FlociGcpContainer) -> None:
        c.with_env(f"{_PREFIX}{self.TOKEN}_ENABLED", env_value(self.enabled))
        if self.enabled:
            for setting, value in self.settings().items():
                c.with_env(f"{_PREFIX}{self.TOKEN}_{setting}", env_value(value))


@dataclass
class GcpMockableServiceConfig(GcpServiceConfig):
    """A container-backed service; while ``mock`` it spawns no sibling containers."""

    mock: bool = False

    def settings(self) -> dict[str, object]:
        return {"MOCK": self.mock}


@dataclass
class BigQueryConfig(GcpMockableServiceConfig):
    """BigQuery. Queries run on a DuckDB sibling container unless mocked."""

    TOKEN: ClassVar[str] = "BIGQUERY"


@dataclass
class CloudFunctionsConfig(GcpServiceConfig):
    """Cloud Functions (control plane only; nothing is run)."""

    TOKEN: ClassVar[str] = "CLOUDFUNCTIONS"


@dataclass
class CloudRunConfig(GcpMockableServiceConfig):
    """Cloud Run. Services, jobs and worker pools run as sibling containers."""

    TOKEN: ClassVar[str] = "CLOUDRUN"


@dataclass
class CloudSqlConfig(GcpMockableServiceConfig):
    """Cloud SQL. Each instance is a PostgreSQL or MySQL sibling container."""

    TOKEN: ClassVar[str] = "CLOUDSQL"


@dataclass
class CloudTasksConfig(GcpServiceConfig):
    """Cloud Tasks."""

    TOKEN: ClassVar[str] = "CLOUDTASKS"


@dataclass
class ComputeConfig(GcpServiceConfig):
    """Compute Engine."""

    TOKEN: ClassVar[str] = "COMPUTE"


@dataclass
class DatastoreConfig(GcpServiceConfig):
    """Datastore."""

    TOKEN: ClassVar[str] = "DATASTORE"


@dataclass
class EventarcConfig(GcpServiceConfig):
    """Eventarc."""

    TOKEN: ClassVar[str] = "EVENTARC"


@dataclass
class FirebaseAuthConfig(GcpServiceConfig):
    """Firebase Authentication (Identity Platform)."""

    TOKEN: ClassVar[str] = "FIREBASEAUTH"


@dataclass
class FirestoreConfig(GcpServiceConfig):
    """Firestore."""

    TOKEN: ClassVar[str] = "FIRESTORE"


@dataclass
class GcsConfig(GcpServiceConfig):
    """Cloud Storage."""

    TOKEN: ClassVar[str] = "GCS"


@dataclass
class GkeConfig(GcpMockableServiceConfig):
    """Kubernetes Engine. Each cluster is a k3s sibling container."""

    TOKEN: ClassVar[str] = "GKE"


@dataclass
class IamConfig(GcpServiceConfig):
    """Identity and Access Management."""

    TOKEN: ClassVar[str] = "IAM"


@dataclass
class IamCredentialsConfig(GcpServiceConfig):
    """IAM Service Account Credentials."""

    TOKEN: ClassVar[str] = "IAMCREDENTIALS"


@dataclass
class KafkaConfig(GcpMockableServiceConfig):
    """Managed Service for Apache Kafka, on a Redpanda sibling container."""

    TOKEN: ClassVar[str] = "KAFKA"


@dataclass
class KmsConfig(GcpServiceConfig):
    """Cloud Key Management Service."""

    TOKEN: ClassVar[str] = "KMS"


@dataclass
class LoggingConfig(GcpServiceConfig):
    """Cloud Logging."""

    TOKEN: ClassVar[str] = "LOGGING"


@dataclass
class MonitoringConfig(GcpServiceConfig):
    """Cloud Monitoring."""

    TOKEN: ClassVar[str] = "MONITORING"


@dataclass
class PubSubConfig(GcpServiceConfig):
    """Pub/Sub."""

    TOKEN: ClassVar[str] = "PUBSUB"


@dataclass
class ResourceManagerConfig(GcpServiceConfig):
    """Resource Manager."""

    TOKEN: ClassVar[str] = "RESOURCEMANAGER"


@dataclass
class SchedulerConfig(GcpServiceConfig):
    """Cloud Scheduler."""

    TOKEN: ClassVar[str] = "SCHEDULER"


@dataclass
class SecretManagerConfig(GcpServiceConfig):
    """Secret Manager."""

    TOKEN: ClassVar[str] = "SECRETMANAGER"


@dataclass
class ServiceUsageConfig(GcpServiceConfig):
    """Service Usage."""

    TOKEN: ClassVar[str] = "SERVICEUSAGE"


@dataclass
class StsConfig(GcpServiceConfig):
    """Security Token Service."""

    TOKEN: ClassVar[str] = "STS"
