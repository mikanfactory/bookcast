"""
Base service classes and interfaces for the bookcast application.
"""

import logging
from abc import ABC
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialize()

    def _initialize(self):
        """Initialize the service. Override in subclasses if needed."""
        pass

    def _log_info(self, message: str):
        """Log an info message with service name."""
        logger.info(f"[{self.__class__.__name__}] {message}")

    def _log_error(self, message: str):
        """Log an error message with service name."""
        logger.error(f"[{self.__class__.__name__}] {message}")


class ServiceResult:
    """Standard result object for service operations."""

    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    @classmethod
    def success(cls, data: Any = None):
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def failure(cls, error: str):
        """Create a failed result."""
        return cls(success=False, error=error)
