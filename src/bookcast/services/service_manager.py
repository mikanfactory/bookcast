"""
Service manager for centralized service access and dependency injection.
"""

from typing import Any, Dict, Optional

from bookcast.services.base import BaseService
from bookcast.services.chapter import ChapterService
from bookcast.services.file import FileService
from bookcast.services.pdf_processing import PDFProcessingService
from bookcast.services.podcast import PodcastService
from bookcast.services.session import SessionService


class ServiceManager:
    """
    Centralized service manager for the bookcast application.

    This class provides a single point of access to all services and handles
    service lifecycle management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._services: Dict[str, BaseService] = {}
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all services with their configurations."""
        # PDF Processing Service
        self._services["pdf_processing"] = PDFProcessingService(
            config=self.config.get("pdf_processing", {})
        )

        # Chapter Service
        self._services["chapter"] = ChapterService(
            config=self.config.get("chapter", {})
        )

        # Podcast Service
        self._services["podcast"] = PodcastService(
            config=self.config.get("podcast", {})
        )

        # Session Service
        self._services["session"] = SessionService(
            config=self.config.get("session", {})
        )

        # File Service
        self._services["file"] = FileService(config=self.config.get("file", {}))

    @property
    def pdf_processing(self) -> PDFProcessingService:
        """Get the PDF processing service."""
        return self._services["pdf_processing"]

    @property
    def chapter(self) -> ChapterService:
        """Get the chapter service."""
        return self._services["chapter"]

    @property
    def podcast(self) -> PodcastService:
        """Get the podcast service."""
        return self._services["podcast"]

    @property
    def session(self) -> SessionService:
        """Get the session service."""
        return self._services["session"]

    @property
    def file(self) -> FileService:
        """Get the file service."""
        return self._services["file"]

    def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Get a service by name.

        Args:
            service_name: Name of the service

        Returns:
            Service instance or None if not found
        """
        return self._services.get(service_name)

    def reload_service(self, service_name: str):
        """
        Reload a specific service.

        Args:
            service_name: Name of the service to reload
        """
        if service_name in self._services:
            # Re-initialize the service
            if service_name == "pdf_processing":
                self._services[service_name] = PDFProcessingService(
                    config=self.config.get("pdf_processing", {})
                )
            elif service_name == "chapter":
                self._services[service_name] = ChapterService(
                    config=self.config.get("chapter", {})
                )
            elif service_name == "podcast":
                self._services[service_name] = PodcastService(
                    config=self.config.get("podcast", {})
                )
            elif service_name == "session":
                self._services[service_name] = SessionService(
                    config=self.config.get("session", {})
                )
            elif service_name == "file":
                self._services[service_name] = FileService(
                    config=self.config.get("file", {})
                )

    def get_all_services(self) -> Dict[str, BaseService]:
        """Get all registered services."""
        return self._services.copy()


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """
    Get the global service manager instance.

    Returns:
        ServiceManager instance
    """
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


def initialize_service_manager(
    config: Optional[Dict[str, Any]] = None,
) -> ServiceManager:
    """
    Initialize the global service manager with configuration.

    Args:
        config: Configuration dictionary

    Returns:
        ServiceManager instance
    """
    global _service_manager
    _service_manager = ServiceManager(config)
    return _service_manager
