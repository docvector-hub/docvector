"""Common API schemas."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    timestamp: datetime
    dependencies: Dict[str, Dict[str, str]]


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: Dict[str, Any]
