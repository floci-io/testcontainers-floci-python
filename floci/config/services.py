"""Service configuration dataclasses for FlociContainer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from floci.container import FlociContainer


def _env(container: "FlociContainer", key: str, value: object) -> None:
    container.with_env(key, str(value).lower() if isinstance(value, bool) else str(value))


@dataclass
class AcmConfig:
    enabled: bool = True
    validation_wait_seconds: int = 0

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ACM_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ACM_VALIDATION_WAIT_SECONDS", self.validation_wait_seconds)


@dataclass
class ApiGatewayConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_APIGATEWAY_ENABLED", self.enabled)


@dataclass
class ApiGatewayV2Config:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_APIGATEWAYV2_ENABLED", self.enabled)


@dataclass
class AppConfigConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_APPCONFIG_ENABLED", self.enabled)


@dataclass
class AppConfigDataConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_APPCONFIGDATA_ENABLED", self.enabled)


@dataclass
class AthenaConfig:
    enabled: bool = True
    mock: bool = False
    default_image: str = "floci/floci-duck:latest"

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ATHENA_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ATHENA_MOCK", self.mock)
        _env(c, "FLOCI_SERVICES_ATHENA_DEFAULT_IMAGE", self.default_image)


@dataclass
class BedrockRuntimeConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_BEDROCK_RUNTIME_ENABLED", self.enabled)


@dataclass
class CloudFormationConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_CLOUDFORMATION_ENABLED", self.enabled)


@dataclass
class CloudWatchLogsConfig:
    enabled: bool = True
    max_events_per_query: int = 10000

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_CLOUDWATCH_LOGS_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_CLOUDWATCH_LOGS_MAX_EVENTS_PER_QUERY", self.max_events_per_query)


@dataclass
class CloudWatchMetricsConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_CLOUDWATCH_METRICS_ENABLED", self.enabled)


@dataclass
class CodeBuildConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_CODEBUILD_ENABLED", self.enabled)


@dataclass
class CodeDeployConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_CODEDEPLOY_ENABLED", self.enabled)


@dataclass
class CognitoConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_COGNITO_ENABLED", self.enabled)


@dataclass
class DynamoDbConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_DYNAMODB_ENABLED", self.enabled)


@dataclass
class Ec2Config:
    enabled: bool = True
    mock: bool = False
    imds_port: int = 9169

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_EC2_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_EC2_MOCK", self.mock)
        _env(c, "FLOCI_SERVICES_EC2_IMDS_PORT", self.imds_port)


@dataclass
class EcrConfig:
    enabled: bool = True
    registry_image: str = "registry:2"
    registry_base_port: int = 5100
    registry_port_count: int = 100

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ECR_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ECR_REGISTRY_IMAGE", self.registry_image)
        _env(c, "FLOCI_SERVICES_ECR_REGISTRY_BASE_PORT", self.registry_base_port)
        for port in range(self.registry_base_port, self.registry_base_port + self.registry_port_count):
            c.with_exposed_ports(port)


@dataclass
class EcsConfig:
    enabled: bool = True
    mock: bool = False

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ECS_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ECS_MOCK", self.mock)


@dataclass
class EksConfig:
    enabled: bool = True
    mock: bool = False
    provider: str = "k3s"
    default_image: str = "rancher/k3s:latest"
    api_server_base_port: int = 6500
    api_server_port_count: int = 100

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_EKS_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_EKS_MOCK", self.mock)
        _env(c, "FLOCI_SERVICES_EKS_PROVIDER", self.provider)
        _env(c, "FLOCI_SERVICES_EKS_DEFAULT_IMAGE", self.default_image)
        _env(c, "FLOCI_SERVICES_EKS_API_SERVER_BASE_PORT", self.api_server_base_port)
        for port in range(self.api_server_base_port, self.api_server_base_port + self.api_server_port_count):
            c.with_exposed_ports(port)


@dataclass
class ElastiCacheConfig:
    enabled: bool = True
    default_image: str = "valkey/valkey:8"
    proxy_base_port: int = 6379
    proxy_port_count: int = 21

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ELASTICACHE_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ELASTICACHE_DEFAULT_IMAGE", self.default_image)
        _env(c, "FLOCI_SERVICES_ELASTICACHE_PROXY_BASE_PORT", self.proxy_base_port)
        for port in range(self.proxy_base_port, self.proxy_base_port + self.proxy_port_count):
            c.with_exposed_ports(port)


@dataclass
class ElbV2Config:
    enabled: bool = True
    mock: bool = False

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_ELBV2_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_ELBV2_MOCK", self.mock)


@dataclass
class EventBridgeConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_EVENTBRIDGE_ENABLED", self.enabled)


@dataclass
class FirehoseConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_FIREHOSE_ENABLED", self.enabled)


@dataclass
class GlueConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_GLUE_ENABLED", self.enabled)


@dataclass
class IamConfig:
    enabled: bool = True
    enforcement_enabled: bool = False

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_IAM_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED", self.enforcement_enabled)


@dataclass
class KinesisConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_KINESIS_ENABLED", self.enabled)


@dataclass
class KmsConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_KMS_ENABLED", self.enabled)


@dataclass
class LambdaConfig:
    enabled: bool = True
    default_memory_mb: int = 128
    default_timeout_seconds: int = 3
    ephemeral: bool = False
    hot_reload_enabled: bool = False
    runtime_api_base_port: int = 9200
    runtime_api_port_count: int = 100
    expose_runtime_ports: bool = False
    docker_network: Optional[str] = None

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_LAMBDA_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_LAMBDA_DEFAULT_MEMORY_MB", self.default_memory_mb)
        _env(c, "FLOCI_SERVICES_LAMBDA_DEFAULT_TIMEOUT_SECONDS", self.default_timeout_seconds)
        _env(c, "FLOCI_SERVICES_LAMBDA_EPHEMERAL", self.ephemeral)
        _env(c, "FLOCI_SERVICES_LAMBDA_HOT_RELOAD_ENABLED", self.hot_reload_enabled)
        _env(c, "FLOCI_SERVICES_LAMBDA_RUNTIME_API_BASE_PORT", self.runtime_api_base_port)
        if self.docker_network:
            _env(c, "FLOCI_SERVICES_LAMBDA_DOCKER_NETWORK", self.docker_network)
        if self.expose_runtime_ports:
            for port in range(self.runtime_api_base_port, self.runtime_api_base_port + self.runtime_api_port_count):
                c.with_exposed_ports(port)


@dataclass
class MskConfig:
    enabled: bool = True
    mock: bool = False
    default_image: str = "redpandadata/redpanda:latest"

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_MSK_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_MSK_MOCK", self.mock)
        _env(c, "FLOCI_SERVICES_MSK_DEFAULT_IMAGE", self.default_image)


@dataclass
class OpenSearchConfig:
    enabled: bool = True
    mock: bool = False
    default_image: str = "opensearchproject/opensearch:2"
    proxy_base_port: int = 9400
    proxy_port_count: int = 100

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_OPENSEARCH_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_OPENSEARCH_MOCK", self.mock)
        _env(c, "FLOCI_SERVICES_OPENSEARCH_DEFAULT_IMAGE", self.default_image)
        _env(c, "FLOCI_SERVICES_OPENSEARCH_PROXY_BASE_PORT", self.proxy_base_port)
        for port in range(self.proxy_base_port, self.proxy_base_port + self.proxy_port_count):
            c.with_exposed_ports(port)


@dataclass
class PipesConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_PIPES_ENABLED", self.enabled)


@dataclass
class RdsConfig:
    enabled: bool = True
    proxy_base_port: int = 7001
    proxy_port_count: int = 99
    default_postgres_image: str = "postgres:16-alpine"
    default_mysql_image: str = "mysql:8.0"
    default_mariadb_image: str = "mariadb:11"

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_RDS_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_RDS_PROXY_BASE_PORT", self.proxy_base_port)
        _env(c, "FLOCI_SERVICES_RDS_DEFAULT_POSTGRES_IMAGE", self.default_postgres_image)
        _env(c, "FLOCI_SERVICES_RDS_DEFAULT_MYSQL_IMAGE", self.default_mysql_image)
        _env(c, "FLOCI_SERVICES_RDS_DEFAULT_MARIADB_IMAGE", self.default_mariadb_image)
        for port in range(self.proxy_base_port, self.proxy_base_port + self.proxy_port_count):
            c.with_exposed_ports(port)


@dataclass
class ResourceGroupsTaggingConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_RESOURCEGROUPSTAGGING_ENABLED", self.enabled)


@dataclass
class S3Config:
    enabled: bool = True
    default_presign_expiry_seconds: int = 3600

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_S3_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_S3_DEFAULT_PRESIGN_EXPIRY_SECONDS", self.default_presign_expiry_seconds)


@dataclass
class SchedulerConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SCHEDULER_ENABLED", self.enabled)


@dataclass
class SecretsManagerConfig:
    enabled: bool = True
    default_recovery_window_days: int = 30

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SECRETS_MANAGER_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_SECRETS_MANAGER_DEFAULT_RECOVERY_WINDOW_DAYS", self.default_recovery_window_days)


@dataclass
class SesConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SES_ENABLED", self.enabled)


@dataclass
class SesV2Config:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SES_V2_ENABLED", self.enabled)


@dataclass
class SnsConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SNS_ENABLED", self.enabled)


@dataclass
class SqsConfig:
    enabled: bool = True
    default_visibility_timeout: int = 30
    max_message_size: int = 262144

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SQS_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_SQS_DEFAULT_VISIBILITY_TIMEOUT", self.default_visibility_timeout)
        _env(c, "FLOCI_SERVICES_SQS_MAX_MESSAGE_SIZE", self.max_message_size)


@dataclass
class SsmConfig:
    enabled: bool = True
    max_parameter_history: int = 5

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_SSM_ENABLED", self.enabled)
        _env(c, "FLOCI_SERVICES_SSM_MAX_PARAMETER_HISTORY", self.max_parameter_history)


@dataclass
class StepFunctionsConfig:
    enabled: bool = True

    def apply_to(self, c: "FlociContainer") -> None:
        _env(c, "FLOCI_SERVICES_STEPFUNCTIONS_ENABLED", self.enabled)
