"""The pinned images the integration tests run against, from ``.github/docker-images.txt``."""

from pathlib import Path


def pinned_image(prefix: str) -> str:
    """The pinned image starting with ``prefix``, from its one declaration."""
    path = Path(__file__).resolve().parent.parent / ".github" / "docker-images.txt"
    for line in path.read_text().splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    raise LookupError(f"no {prefix} image in .github/docker-images.txt")


TEST_IMAGE = pinned_image("floci/floci:")
"""The pinned floci/floci tag every integration test runs against."""
