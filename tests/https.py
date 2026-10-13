"""One HTTPS request without retries, for the TLS readiness tests."""

from __future__ import annotations

import ssl
import urllib.request


def https_status(url: str, certificate: str | None = None) -> int:
    """GET ``url`` once and return the status.

    ``certificate`` is the PEM to trust (the emulator's self-signed one, which names no
    host); without it the server certificate is not checked at all.
    """
    context = ssl.create_default_context(cadata=certificate)
    context.check_hostname = False
    if certificate is None:
        context.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, timeout=10, context=context) as resp:
        status: int = resp.status
    return status
