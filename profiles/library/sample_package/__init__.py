"""A sample library: replace this sentence with what the package is for."""

from importlib.metadata import PackageNotFoundError, version

from .smoothing import moving_average

__all__ = ["__version__", "moving_average"]

try:
    __version__ = version("sample-project")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0+unknown"
