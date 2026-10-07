"""Set the package version in pyproject.toml and uv.lock (run by semantic-release's prepare step).

uv.lock records the project's own version, and CI installs with `uv sync --locked`, so both
files must change together or the first CI run after a release fails.
"""

import re
import sys
from pathlib import Path


def main(version: str) -> None:
    pyproject, lock = Path("pyproject.toml"), Path("uv.lock")
    pyproject_text, n = re.subn(
        r'(?m)^version = "[^"]*"', f'version = "{version}"', pyproject.read_text(), count=1
    )
    if n != 1:
        sys.exit("pyproject.toml: no top-level version line found")
    pattern = r'(\nname = "testcontainers-floci"\nversion = ")[^"]*(")'
    lock_text, n = re.subn(pattern, rf"\g<1>{version}\g<2>", lock.read_text(), count=1)
    if n != 1:
        sys.exit("uv.lock: testcontainers-floci package entry not found")
    # Both files validated: write them together so a failure never leaves mixed versions.
    pyproject.write_text(pyproject_text)
    lock.write_text(lock_text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: set_version.py <version>")
    main(sys.argv[1])
