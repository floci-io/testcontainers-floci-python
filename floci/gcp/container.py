"""FlociGcpContainer: Testcontainers module for the Floci local GCP emulator."""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any

from floci.core import CloudDescriptor, FlociBaseContainer, Setting, SocketService
from floci.gcp.config.services import (
    BigQueryConfig,
    CloudFunctionsConfig,
    CloudRunConfig,
    CloudSqlConfig,
    CloudTasksConfig,
    ComputeConfig,
    DatastoreConfig,
    EventarcConfig,
    FirebaseAuthConfig,
    FirestoreConfig,
    GcsConfig,
    GkeConfig,
    IamConfig,
    IamCredentialsConfig,
    KafkaConfig,
    KmsConfig,
    LoggingConfig,
    MonitoringConfig,
    PubSubConfig,
    ResourceManagerConfig,
    SchedulerConfig,
    SecretManagerConfig,
    ServiceUsageConfig,
    StsConfig,
)
from floci.gcp.config.top_level import TlsConfig

DEFAULT_IMAGE = "floci/floci-gcp"
DEFAULT_TAG = "latest"


def _bigquery_spawns(setting: Setting) -> bool:
    """BigQuery starts its DuckDB sidecar only when no running one is configured."""
    return not setting("DUCK_URL")


GCP = CloudDescriptor(
    name="gcp",
    image=DEFAULT_IMAGE,
    port=4588,
    env_prefix="FLOCI_GCP_",
    health_path="/_floci-gcp/health",
    reset_path="/_floci-gcp/state/reset",
    log_level_env="QUARKUS_LOG_CATEGORY__IO_FLOCI_GCP__LEVEL",
    # The services that start sibling containers (floci-gcp 0.10.0); each has a mock switch.
    # Cloud Functions is control plane only and starts none.
    socket_services=(
        SocketService("BIGQUERY", mockable=True, spawns=_bigquery_spawns),
        SocketService("CLOUDRUN", mockable=True),
        SocketService("CLOUDSQL", mockable=True),
        SocketService("GKE", mockable=True),
        SocketService("KAFKA", mockable=True),
    ),
    default_env={
        # The extra HTTPS port defaults to 443, which an unprivileged container cannot bind.
        "FLOCI_GCP_TLS_HTTPS_PORT": "0",
    },
)


class FlociGcpContainer(FlociBaseContainer):
    """Testcontainers wrapper for the Floci local GCP emulator.

    Example::

        with FlociGcpContainer() as floci:
            os.environ.update(floci.get_emulator_env())
            storage.Client(project=floci.get_project_id())

    The host Docker socket is mounted only while an enabled, non-mocked service needs it
    (GKE, Cloud SQL, Cloud Run, Managed Kafka, BigQuery); see :meth:`with_docker_socket` to
    force it either way.
    """

    DESCRIPTOR = GCP
    PORT = 4588
    DEFAULT_PROJECT_ID = "floci-local"
    TLS_CERT_PATH = "/_floci-gcp/tls-cert"

    def __init__(self, image: str = f"{DEFAULT_IMAGE}:{DEFAULT_TAG}", **kwargs: Any) -> None:
        super().__init__(image, **kwargs)
        self._project_id = self.DEFAULT_PROJECT_ID

    # ------------------------------------------------------------------
    # Connection properties
    # ------------------------------------------------------------------

    def get_https_endpoint(self) -> str:
        """HTTPS base URL, on the same port; it answers once TLS is enabled (:class:`TlsConfig`)."""
        return "https" + self.get_endpoint()[len("http") :]

    def get_tls_certificate(self) -> str:
        """The PEM certificate clients must trust for :meth:`get_https_endpoint`.

        Raises ``RuntimeError`` when the emulator has none, i.e. TLS is not enabled.
        """
        url = self.get_endpoint() + self.TLS_CERT_PATH
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                body: bytes = resp.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"TLS certificate not available (HTTP {exc.code})") from exc
        return body.decode()

    def get_project_id(self) -> str:
        """The default project (``floci-local``); the emulator accepts any project ID."""
        return self._project_id

    def get_emulator_host(self) -> str:
        """``host:port`` of the emulator, the form the ``*_EMULATOR_HOST`` variables take."""
        return self.get_endpoint()[len("http://") :]

    def get_emulator_env(self) -> dict[str, str]:
        """The environment variables that point Google's SDKs and tools at the emulator.

        All plain HTTP on the one emulator port. ``STORAGE_EMULATOR_HOST`` is a URL, the rest
        are ``host:port``. The Pub/Sub, Firestore, Datastore, Secret Manager, Firebase Auth
        and Storage variables are read by Google's client libraries. ``LOGGING_EMULATOR_HOST``
        and ``KMS_EMULATOR_HOST`` are a floci-gcp convention that no client library reads:
        build those clients on ``get_emulator_host()`` yourself.
        """
        host = self.get_emulator_host()
        return {
            "PUBSUB_EMULATOR_HOST": host,
            "FIRESTORE_EMULATOR_HOST": host,
            "DATASTORE_EMULATOR_HOST": host,
            "SECRET_MANAGER_EMULATOR_HOST": host,
            "FIREBASE_AUTH_EMULATOR_HOST": host,
            "LOGGING_EMULATOR_HOST": host,
            "KMS_EMULATOR_HOST": host,
            "STORAGE_EMULATOR_HOST": self.get_endpoint(),
            "STORAGE_EMULATOR_HOST_GRPC": host,
            "GOOGLE_CLOUD_PROJECT": self.get_project_id(),
        }

    # ------------------------------------------------------------------
    # Top-level configuration helpers
    # ------------------------------------------------------------------

    def with_project_id(self, project_id: str) -> FlociGcpContainer:
        """Change the default project, used when a request names none."""
        self._project_id = project_id
        self.with_env("FLOCI_GCP_DEFAULT_PROJECT_ID", project_id)
        return self

    def with_tls_config(self, config: TlsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    # ------------------------------------------------------------------
    # Service configuration helpers
    # ------------------------------------------------------------------

    def with_bigquery_config(self, config: BigQueryConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_cloudfunctions_config(self, config: CloudFunctionsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_cloudrun_config(self, config: CloudRunConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_cloudsql_config(self, config: CloudSqlConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_cloudtasks_config(self, config: CloudTasksConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_compute_config(self, config: ComputeConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_datastore_config(self, config: DatastoreConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_eventarc_config(self, config: EventarcConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_firebaseauth_config(self, config: FirebaseAuthConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_firestore_config(self, config: FirestoreConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_gcs_config(self, config: GcsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_gke_config(self, config: GkeConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_iam_config(self, config: IamConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_iamcredentials_config(self, config: IamCredentialsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_kafka_config(self, config: KafkaConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_kms_config(self, config: KmsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_logging_config(self, config: LoggingConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_monitoring_config(self, config: MonitoringConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_pubsub_config(self, config: PubSubConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_resourcemanager_config(self, config: ResourceManagerConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_scheduler_config(self, config: SchedulerConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_secretmanager_config(self, config: SecretManagerConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_serviceusage_config(self, config: ServiceUsageConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self

    def with_sts_config(self, config: StsConfig) -> FlociGcpContainer:
        self.with_service_config(config)
        return self
