"""DocVector - Self-hostable documentation vector search system."""

__version__ = "0.1.0"

from docvector.core import DocVectorException, get_logger, settings, setup_logging

__all__ = [
    "__version__",
    "DocVectorException",
    "get_logger",
    "settings",
    "setup_logging",
]
