"""qibocal-report: Modern web app and server for Qibocal calibration reports."""

from importlib import metadata

# One version, the package's: pyproject.toml, which a release tag must match.
try:
    __version__ = metadata.version("qibocal-report")
except metadata.PackageNotFoundError:  # a source tree on the path, never installed
    __version__ = "0+unknown"
