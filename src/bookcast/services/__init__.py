"""
Services package for the bookcast application.

This package contains all business logic services that handle the core
functionality of the application.
"""

from .base import BaseService, ServiceResult
from .chapter import ChapterService
from .file import FileService
from .pdf_processing import PDFProcessingService
from .podcast import PodcastService
from .service_manager import (
    ServiceManager,
    get_service_manager,
    initialize_service_manager,
)
from .session import SessionService

__all__ = [
    "BaseService",
    "ServiceResult",
    "PDFProcessingService",
    "ChapterService",
    "PodcastService",
    "SessionService",
    "FileService",
    "ServiceManager",
    "get_service_manager",
    "initialize_service_manager",
]
