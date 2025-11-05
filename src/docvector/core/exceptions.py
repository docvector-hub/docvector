"""Custom exceptions for DocVector."""

from typing import Any, Dict, Optional


class DocVectorException(Exception):
    """Base exception for all DocVector errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


class ConfigurationError(DocVectorException):
    """Configuration error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class DatabaseError(DocVectorException):
    """Database operation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class ValidationError(DocVectorException):
    """Input validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class NotFoundError(DocVectorException):
    """Resource not found error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="NOT_FOUND", details=details)


class EmbeddingError(DocVectorException):
    """Embedding generation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class SearchError(DocVectorException):
    """Search operation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SEARCH_ERROR", details=details)


class IngestionError(DocVectorException):
    """Document ingestion error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INGESTION_ERROR", details=details)


class ProcessingError(DocVectorException):
    """Document processing error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="PROCESSING_ERROR", details=details)


class RateLimitError(DocVectorException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)


class AuthenticationError(DocVectorException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHENTICATION_REQUIRED", details=details)


class AuthorizationError(DocVectorException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="FORBIDDEN", details=details)
