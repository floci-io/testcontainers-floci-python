"""FlociContainer — Testcontainers module for the Floci local AWS emulator."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

from floci.config.services import (
    AcmConfig,
    ApiGatewayConfig,
    ApiGatewayV2Config,
    AppConfigConfig,
    AppConfigDataConfig,
    AthenaConfig,
    BackupConfig,
    BedrockRuntimeConfig,
    CloudFormationConfig,
    CloudWatchLogsConfig,
    CloudWatchMetricsConfig,
    CodeBuildConfig,
    CodeDeployConfig,
    CognitoConfig,
    DynamoDbConfig,
    Ec2Config,
    EcrConfig,
    EcsConfig,
    EksConfig,
    ElastiCacheConfig,
    ElbV2Config,
    EventBridgeConfig,
    FirehoseConfig,
    GlueConfig,
    IamConfig,
    KinesisConfig,
    KmsConfig,
    LambdaConfig,
    MskConfig,
    OpenSearchConfig,
    PipesConfig,
    RdsConfig,
    ResourceGroupsTaggingConfig,
    Route53Config,
    S3Config,
    SchedulerConfig,
    SecretsManagerConfig,
    SesConfig,
    SesV2Config,
    SnsConfig,
    SqsConfig,
    SsmConfig,
    StepFunctionsConfig,
    TextractConfig,
    TransferFamilyConfig,
)
from floci.config.top_level import StorageConfig, TlsConfig

DEFAULT_IMAGE = "floci/floci"
DEFAULT_TAG = "latest"


class FlociContainer(DockerContainer):
    """Testcontainers wrapper for the Floci local AWS emulator.

    Example::

        with FlociContainer() as floci:
            s3 = boto3.client(
                "s3",
                endpoint_url=floci.get_endpoint(),
                region_name=floci.get_region(),
                aws_access_key_id=floci.get_access_key(),
                aws_secret_access_key=floci.get_secret_key(),
            )
    """

    PORT = 4566
    DEFAULT_REGION = "us-east-1"
    DEFAULT_AVAILABILITY_ZONE = "us-east-1a"
    DEFAULT_ACCOUNT_ID = "000000000000"
    DEFAULT_ACCESS_KEY = "test"
    DEFAULT_SECRET_KEY = "test"
    STARTUP_TIMEOUT = 30

    def __init__(self, image: str = f"{DEFAULT_IMAGE}:{DEFAULT_TAG}", **kwargs: Any) -> None:
        super().__init__(image=image, **kwargs)
        self._region = self.DEFAULT_REGION
        self._availability_zone = self.DEFAULT_AVAILABILITY_ZONE
        self._account_id = self.DEFAULT_ACCOUNT_ID
        self._access_key = self.DEFAULT_ACCESS_KEY
        self._secret_key = self.DEFAULT_SECRET_KEY
        self._dedicated_network: str | None = None

        self.with_exposed_ports(self.PORT)
        self.with_volume_mapping("/var/run/docker.sock", "/var/run/docker.sock", "rw")
        self.with_env("FLOCI_DEFAULT_REGION", self._region)
        self.with_env("FLOCI_DEFAULT_ACCOUNT_ID", self._account_id)
        self.with_env("FLOCI_DEFAULT_AVAILABILITY_ZONE", self._availability_zone)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> FlociContainer:
        super().start()
        self._wait_for_health()
        return self

    def _wait_for_health(self) -> None:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.PORT)
        url = f"http://{host}:{port}/_floci/health"
        deadline = time.monotonic() + self.STARTUP_TIMEOUT
        last_error: Exception | None = None

        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except Exception as exc:
                last_error = exc
            time.sleep(0.5)

        raise TimeoutError(
            f"Floci container did not become healthy within {self.STARTUP_TIMEOUT}s. "
            f"Last error: {last_error}"
        )

    # ------------------------------------------------------------------
    # Connection properties
    # ------------------------------------------------------------------

    def get_endpoint(self) -> str:
        """Return the base URL for all AWS API calls, e.g. http://localhost:32768."""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.PORT)
        return f"http://{host}:{port}"

    def get_region(self) -> str:
        return self._region

    def get_access_key(self) -> str:
        return self._access_key

    def get_secret_key(self) -> str:
        return self._secret_key

    def get_account_id(self) -> str:
        return self._account_id

    def get_availability_zone(self) -> str:
        return self._availability_zone

    def get_dedicated_network_name(self) -> str | None:
        return self._dedicated_network

    # ------------------------------------------------------------------
    # General configuration
    # ------------------------------------------------------------------

    def with_region(self, region: str) -> FlociContainer:
        self._region = region
        self.with_env("FLOCI_DEFAULT_REGION", region)
        return self

    def with_account_id(self, account_id: str) -> FlociContainer:
        self._account_id = account_id
        self.with_env("FLOCI_DEFAULT_ACCOUNT_ID", account_id)
        return self

    def with_availability_zone(self, zone: str) -> FlociContainer:
        self._availability_zone = zone
        self.with_env("FLOCI_DEFAULT_AVAILABILITY_ZONE", zone)
        return self

    def with_access_key(self, access_key: str) -> FlociContainer:
        self._access_key = access_key
        return self

    def with_secret_key(self, secret_key: str) -> FlociContainer:
        self._secret_key = secret_key
        return self

    def with_dedicated_network(self) -> FlociContainer:
        """Create an isolated Docker network for container-based services (RDS, ElastiCache…)."""
        network_name = f"floci-{uuid.uuid4().hex[:8]}"
        network = Network(docker_network_kw={"name": network_name})
        self._dedicated_network = network_name
        self.with_network(network)
        self.with_env("FLOCI_SERVICES_DOCKER_NETWORK", network_name)
        return self

    def with_log_level(self, level: str) -> FlociContainer:
        """Set the Floci log level (e.g. DEBUG, INFO, WARN, ERROR)."""
        self.with_env("QUARKUS_LOG_CATEGORY__IO_GITHUB_HECTORVENT__LEVEL", level)
        return self

    # ------------------------------------------------------------------
    # Top-level configuration helpers
    # ------------------------------------------------------------------

    def with_tls_config(self, config: TlsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_storage_config(self, config: StorageConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    # ------------------------------------------------------------------
    # Service configuration helpers
    # ------------------------------------------------------------------

    def with_acm_config(self, config: AcmConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_api_gateway_config(self, config: ApiGatewayConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_api_gateway_v2_config(self, config: ApiGatewayV2Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_app_config_config(self, config: AppConfigConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_app_config_data_config(self, config: AppConfigDataConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_athena_config(self, config: AthenaConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_bedrock_runtime_config(self, config: BedrockRuntimeConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_cloud_formation_config(self, config: CloudFormationConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_cloud_watch_logs_config(self, config: CloudWatchLogsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_cloud_watch_metrics_config(self, config: CloudWatchMetricsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_code_build_config(self, config: CodeBuildConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_code_deploy_config(self, config: CodeDeployConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_cognito_config(self, config: CognitoConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_dynamo_db_config(self, config: DynamoDbConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_ec2_config(self, config: Ec2Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_ecr_config(self, config: EcrConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_ecs_config(self, config: EcsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_eks_config(self, config: EksConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_elasti_cache_config(self, config: ElastiCacheConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_elb_v2_config(self, config: ElbV2Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_event_bridge_config(self, config: EventBridgeConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_firehose_config(self, config: FirehoseConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_glue_config(self, config: GlueConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_iam_config(self, config: IamConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_kinesis_config(self, config: KinesisConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_kms_config(self, config: KmsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_lambda_config(self, config: LambdaConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_msk_config(self, config: MskConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_open_search_config(self, config: OpenSearchConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_pipes_config(self, config: PipesConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_rds_config(self, config: RdsConfig) -> FlociContainer:
        config.apply_to(self)
        config.apply_exposed_ports(self)
        return self

    def with_resource_groups_tagging_config(
        self, config: ResourceGroupsTaggingConfig
    ) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_s3_config(self, config: S3Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_scheduler_config(self, config: SchedulerConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_secrets_manager_config(self, config: SecretsManagerConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_ses_config(self, config: SesConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_ses_v2_config(self, config: SesV2Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_sns_config(self, config: SnsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_sqs_config(self, config: SqsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_ssm_config(self, config: SsmConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_step_functions_config(self, config: StepFunctionsConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_backup_config(self, config: BackupConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_route53_config(self, config: Route53Config) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_textract_config(self, config: TextractConfig) -> FlociContainer:
        config.apply_to(self)
        return self

    def with_transfer_family_config(self, config: TransferFamilyConfig) -> FlociContainer:
        config.apply_to(self)
        return self
