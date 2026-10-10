"""Testcontainers modules for the Floci local cloud emulators.

The AWS module lives in :mod:`floci.aws`; ``floci.FlociContainer`` stays available as an alias.
"""

from floci.aws import FlociContainer

__all__ = ["FlociContainer"]
