"""FlociContainer: Testcontainers module for the Floci local AWS emulator."""

from __future__ import annotations

from typing import Any

from floci.aws.config.services import (
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
from floci.aws.config.top_level import StorageConfig, TlsConfig
from floci.core import CloudDescriptor, FlociBaseContainer, SocketService

DEFAULT_IMAGE = "floci/floci"
DEFAULT_TAG = "latest"

AWS = CloudDescriptor(
    name="aws",
    image=DEFAULT_IMAGE,
    port=4566,
    env_prefix="FLOCI_",
    health_path="/_floci/health",
    reset_path="/_floci/state/reset",
    log_level_env="QUARKUS_LOG_CATEGORY__IO_GITHUB_HECTORVENT__LEVEL",
    # Services that spawn sibling containers, mirroring requiresDockerSocket() in the Java module.
    socket_services=(
        SocketService("ATHENA", mockable=True),
        SocketService("CODEBUILD"),
        SocketService("EC2", mockable=True),
        SocketService("ECR"),
        SocketService("ECS", mockable=True),
        SocketService("EKS", mockable=True),
        SocketService("ELASTICACHE"),
        SocketService("LAMBDA"),
        SocketService("MSK", mockable=True),
        SocketService("OPENSEARCH", mockable=True),
        SocketService("RDS"),
    ),
)


class FlociContainer(FlociBaseContainer):
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

    The host Docker socket is mounted only while an enabled service needs it (Lambda, RDS,
    ElastiCache, ECS, ...); see :meth:`with_docker_socket` to force it either way.
    """

    DESCRIPTOR = AWS
    PORT = 4566
    DEFAULT_REGION = "us-east-1"
    DEFAULT_AVAILABILITY_ZONE = "us-east-1a"
    DEFAULT_ACCOUNT_ID = "000000000000"
    DEFAULT_ACCESS_KEY = "test"
    DEFAULT_SECRET_KEY = "test"
    STARTUP_TIMEOUT = 30

    def __init__(self, image: str = f"{DEFAULT_IMAGE}:{DEFAULT_TAG}", **kwargs: Any) -> None:
        super().__init__(image, **kwargs)
        self._region = self.DEFAULT_REGION
        self._availability_zone = self.DEFAULT_AVAILABILITY_ZONE
        self._account_id = self.DEFAULT_ACCOUNT_ID
        self._access_key = self.DEFAULT_ACCESS_KEY
        self._secret_key = self.DEFAULT_SECRET_KEY

        self.with_env("FLOCI_DEFAULT_REGION", self._region)
        self.with_env("FLOCI_DEFAULT_ACCOUNT_ID", self._account_id)
        self.with_env("FLOCI_DEFAULT_AVAILABILITY_ZONE", self._availability_zone)

    # ------------------------------------------------------------------
    # Connection properties
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Top-level configuration helpers
    # ------------------------------------------------------------------

    def with_tls_config(self, config: TlsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_storage_config(self, config: StorageConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    # ------------------------------------------------------------------
    # Service configuration helpers
    # ------------------------------------------------------------------

    def with_acm_config(self, config: AcmConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_api_gateway_config(self, config: ApiGatewayConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_api_gateway_v2_config(self, config: ApiGatewayV2Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_app_config_config(self, config: AppConfigConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_app_config_data_config(self, config: AppConfigDataConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_athena_config(self, config: AthenaConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_bedrock_runtime_config(self, config: BedrockRuntimeConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_cloud_formation_config(self, config: CloudFormationConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_cloud_watch_logs_config(self, config: CloudWatchLogsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_cloud_watch_metrics_config(self, config: CloudWatchMetricsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_code_build_config(self, config: CodeBuildConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_code_deploy_config(self, config: CodeDeployConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_cognito_config(self, config: CognitoConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_dynamo_db_config(self, config: DynamoDbConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ec2_config(self, config: Ec2Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ecr_config(self, config: EcrConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ecs_config(self, config: EcsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_eks_config(self, config: EksConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_elasti_cache_config(self, config: ElastiCacheConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_elb_v2_config(self, config: ElbV2Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_event_bridge_config(self, config: EventBridgeConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_firehose_config(self, config: FirehoseConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_glue_config(self, config: GlueConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_iam_config(self, config: IamConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_kinesis_config(self, config: KinesisConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_kms_config(self, config: KmsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_lambda_config(self, config: LambdaConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_msk_config(self, config: MskConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_open_search_config(self, config: OpenSearchConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_pipes_config(self, config: PipesConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_rds_config(self, config: RdsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_resource_groups_tagging_config(
        self, config: ResourceGroupsTaggingConfig
    ) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_s3_config(self, config: S3Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_scheduler_config(self, config: SchedulerConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_secrets_manager_config(self, config: SecretsManagerConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ses_config(self, config: SesConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ses_v2_config(self, config: SesV2Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_sns_config(self, config: SnsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_sqs_config(self, config: SqsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_ssm_config(self, config: SsmConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_step_functions_config(self, config: StepFunctionsConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_backup_config(self, config: BackupConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_route53_config(self, config: Route53Config) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_textract_config(self, config: TextractConfig) -> FlociContainer:
        self.with_service_config(config)
        return self

    def with_transfer_family_config(self, config: TransferFamilyConfig) -> FlociContainer:
        self.with_service_config(config)
        return self
