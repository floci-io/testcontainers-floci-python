"""FlociOciContainer: Testcontainers module for the Floci local OCI emulator."""

from __future__ import annotations

from typing import Any

from floci.core import CloudDescriptor, FlociBaseContainer, SocketService
from floci.oci.config.services import (
    FunctionsConfig,
    IdentityConfig,
    KmsConfig,
    ObjectStorageConfig,
    OkeConfig,
    QueueConfig,
    StreamingConfig,
    VaultConfig,
)
from floci.oci.config.top_level import TlsConfig

DEFAULT_IMAGE = "floci/floci-oci"
DEFAULT_TAG = "latest"

OCI = CloudDescriptor(
    name="oci",
    image=DEFAULT_IMAGE,
    port=4599,
    env_prefix="FLOCI_OCI_",
    health_path="/_floci-oci/health",
    reset_path="/_floci-oci/state/reset",
    log_level_env="QUARKUS_LOG_CATEGORY__IO_FLOCI_OCI__LEVEL",
    # The services that start sibling containers (floci-oci 0.4.2); each has a mock switch.
    socket_services=(
        SocketService("FUNCTIONS", mockable=True),
        SocketService("OKE", mockable=True),
    ),
    default_env={
        # The extra HTTPS port defaults to 443, which an unprivileged container cannot bind.
        "FLOCI_OCI_TLS_HTTPS_PORT": "0",
    },
)


def _generate_private_key_pem() -> str:
    """A new 2048-bit RSA key as unencrypted PKCS#8 PEM."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError as exc:
        raise ImportError(
            "FlociOciContainer needs the 'cryptography' package to generate the API signing "
            "key: install testcontainers-floci[oci] (the OCI SDK brings it too), or pass your "
            "own key with with_private_key_pem(...)"
        ) from exc
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


class FlociOciContainer(FlociBaseContainer):
    """Testcontainers wrapper for the Floci local OCI emulator.

    Example::

        with FlociOciContainer() as floci:
            client = oci.object_storage.ObjectStorageClient(
                floci.get_config(), service_endpoint=floci.get_endpoint()
            )

    OCI SDKs sign every request with an API key. The emulator reads the tenancy and user from
    the signature and never verifies it, so the container hands out a throwaway RSA key,
    generated on first use (:meth:`get_private_key_pem`).

    The host Docker socket is mounted only while an enabled, non-mocked service needs it
    (Functions, OKE); see :meth:`with_docker_socket` to force it either way.
    """

    DESCRIPTOR = OCI
    PORT = 4599
    DEFAULT_REGION = "us-ashburn-1"
    DEFAULT_REALM = "oc1"
    DEFAULT_TENANCY_ID = "ocid1.tenancy.oc1..flocilocaltenancy" + "0" * 40
    DEFAULT_NAMESPACE = "floci-local"
    DEFAULT_USER_ID = "ocid1.user.oc1..flocilocaluser" + "0" * 46
    DEFAULT_FINGERPRINT = "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"

    def __init__(self, image: str = f"{DEFAULT_IMAGE}:{DEFAULT_TAG}", **kwargs: Any) -> None:
        super().__init__(image, **kwargs)
        self._region = self.DEFAULT_REGION
        self._tenancy_id = self.DEFAULT_TENANCY_ID
        self._namespace = self.DEFAULT_NAMESPACE
        self._private_key_pem: str | None = None

    # ------------------------------------------------------------------
    # Connection properties
    # ------------------------------------------------------------------

    def get_https_endpoint(self) -> str:
        """HTTPS base URL, on the same port; it answers once TLS is enabled (:class:`TlsConfig`)."""
        return "https" + self.get_endpoint()[len("http") :]

    def get_region(self) -> str:
        """The emulator's region (``us-ashburn-1``)."""
        return self._region

    def get_tenancy_id(self) -> str:
        """The tenancy OCID, which is also the root compartment."""
        return self._tenancy_id

    def get_namespace(self) -> str:
        """The Object Storage namespace of the tenancy (``floci-local``)."""
        return self._namespace

    def get_user_id(self) -> str:
        """A user OCID to sign requests as; the emulator accepts any."""
        return self.DEFAULT_USER_ID

    def get_fingerprint(self) -> str:
        """The API key fingerprint to sign with; a placeholder, the emulator checks none."""
        return self.DEFAULT_FINGERPRINT

    def get_private_key_pem(self) -> str:
        """The container's throwaway RSA signing key, as unencrypted PKCS#8 PEM.

        Generated on the first call and kept for the life of this object; it works before the
        container starts. Raises ``ImportError`` when ``cryptography`` is not installed and no
        key was given with :meth:`with_private_key_pem`.
        """
        if self._private_key_pem is None:
            self._private_key_pem = _generate_private_key_pem()
        return self._private_key_pem

    def get_config(self) -> dict[str, str]:
        """The config dict of the OCI Python SDK, with the key inline (``key_content``).

        Pass it to a client together with ``service_endpoint=get_endpoint()``.
        """
        return {
            "user": self.get_user_id(),
            "fingerprint": self.get_fingerprint(),
            "tenancy": self.get_tenancy_id(),
            "region": self.get_region(),
            "key_content": self.get_private_key_pem(),
        }

    def get_config_file_contents(self, key_file: str, profile: str = "DEFAULT") -> str:
        """An OCI config file (``~/.oci/config``) with one profile, for the CLI and the SDKs.

        ``key_file`` is where you saved :meth:`get_private_key_pem`; a config file can only
        name the key by path. The endpoint is not part of the file: give each client or CLI
        call :meth:`get_endpoint`.
        """
        return (
            f"[{profile}]\n"
            f"user={self.get_user_id()}\n"
            f"fingerprint={self.get_fingerprint()}\n"
            f"tenancy={self.get_tenancy_id()}\n"
            f"region={self.get_region()}\n"
            f"key_file={key_file}\n"
        )

    # ------------------------------------------------------------------
    # Top-level configuration helpers
    # ------------------------------------------------------------------

    def with_region(self, region: str) -> FlociOciContainer:
        self._region = region
        self.with_env("FLOCI_OCI_DEFAULT_REGION", region)
        return self

    def with_tenancy_id(self, tenancy_id: str) -> FlociOciContainer:
        """Change the tenancy used for unsigned requests, and the one the helpers sign as."""
        self._tenancy_id = tenancy_id
        self.with_env("FLOCI_OCI_DEFAULT_TENANCY_ID", tenancy_id)
        return self

    def with_namespace(self, namespace: str) -> FlociOciContainer:
        """Change the Object Storage namespace."""
        self._namespace = namespace
        self.with_env("FLOCI_OCI_DEFAULT_NAMESPACE", namespace)
        return self

    def with_private_key_pem(self, pem: str) -> FlociOciContainer:
        """Sign with your own RSA key instead of a generated one (no ``cryptography`` needed)."""
        self._private_key_pem = pem
        return self

    def with_tls_config(self, config: TlsConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    # ------------------------------------------------------------------
    # Service configuration helpers
    # ------------------------------------------------------------------

    def with_functions_config(self, config: FunctionsConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_identity_config(self, config: IdentityConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_kms_config(self, config: KmsConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_objectstorage_config(self, config: ObjectStorageConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_oke_config(self, config: OkeConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_queue_config(self, config: QueueConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_streaming_config(self, config: StreamingConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self

    def with_vault_config(self, config: VaultConfig) -> FlociOciContainer:
        self.with_service_config(config)
        return self
