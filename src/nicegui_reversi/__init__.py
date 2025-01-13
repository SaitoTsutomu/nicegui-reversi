from importlib.metadata import metadata

from .main import main

_package_metadata = metadata(str(__package__))
__version__ = _package_metadata["Version"]
__author__ = _package_metadata.get("Author-email", "")

__all__ = ["__author__", "__version__", "main"]
