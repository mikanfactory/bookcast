"""
File management service for handling file operations.
"""

import shutil
from pathlib import Path

from bookcast.path_resolver import (
    build_book_directory,
    build_downloads_path,
    build_image_directory,
    build_script_directory,
    build_text_directory,
    resolve_image_path,
    resolve_text_path,
)
from bookcast.services.base import BaseService, ServiceResult


class FileService(BaseService):
    """Service for handling file operations."""

    def save_uploaded_file(self, file_content: bytes, filename: str) -> ServiceResult:
        """
        Save uploaded file to downloads directory.

        Args:
            file_content: File content as bytes
            filename: Name of the file

        Returns:
            ServiceResult with file path
        """
        try:
            self._log_info(f"Saving uploaded file: {filename}")

            downloads_path = build_downloads_path(filename)
            downloads_path.parent.mkdir(parents=True, exist_ok=True)

            with open(downloads_path, "wb") as f:
                f.write(file_content)

            result = {
                "filename": filename,
                "file_path": str(downloads_path),
                "size": len(file_content),
            }

            self._log_info(f"Successfully saved file: {filename}")
            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to save uploaded file: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_file_info(self, filename: str) -> ServiceResult:
        """
        Get information about a file.

        Args:
            filename: Name of the file

        Returns:
            ServiceResult with file information
        """
        try:
            file_path = build_downloads_path(filename)

            if not file_path.exists():
                return ServiceResult.failure(f"File not found: {filename}")

            info = {
                "filename": filename,
                "file_path": str(file_path),
                "size": file_path.stat().st_size,
                "exists": True,
                "modified": file_path.stat().st_mtime,
            }

            return ServiceResult.success(info)

        except Exception as e:
            error_msg = f"Failed to get file info: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def create_project_structure(self, filename: str) -> ServiceResult:
        """
        Create the directory structure for a project.

        Args:
            filename: Name of the PDF file

        Returns:
            ServiceResult with created directories
        """
        try:
            self._log_info(f"Creating project structure for: {filename}")

            # Create all necessary directories
            directories = [
                build_book_directory(filename),
                build_image_directory(filename),
                build_text_directory(filename),
                build_script_directory(filename),
            ]

            created_dirs = []
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(directory))

            result = {
                "filename": filename,
                "created_directories": created_dirs,
                "total_directories": len(created_dirs),
            }

            self._log_info(f"Successfully created project structure for: {filename}")
            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to create project structure: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_project_status(self, filename: str) -> ServiceResult:
        """
        Get the status of a project (what files exist).

        Args:
            filename: Name of the PDF file

        Returns:
            ServiceResult with project status
        """
        try:
            self._log_info(f"Getting project status for: {filename}")

            pdf_path = build_downloads_path(filename)
            image_dir = build_image_directory(filename)
            text_dir = build_text_directory(filename)
            script_dir = build_script_directory(filename)

            status = {
                "filename": filename,
                "pdf_exists": pdf_path.exists(),
                "image_directory_exists": image_dir.exists(),
                "text_directory_exists": text_dir.exists(),
                "script_directory_exists": script_dir.exists(),
                "image_count": len(list(image_dir.glob("*.png")))
                if image_dir.exists()
                else 0,
                "text_count": len(list(text_dir.glob("*.txt")))
                if text_dir.exists()
                else 0,
                "script_count": len(list(script_dir.glob("*.txt")))
                if script_dir.exists()
                else 0,
            }

            return ServiceResult.success(status)

        except Exception as e:
            error_msg = f"Failed to get project status: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def cleanup_project(self, filename: str) -> ServiceResult:
        """
        Clean up all files related to a project.

        Args:
            filename: Name of the PDF file

        Returns:
            ServiceResult with cleanup status
        """
        try:
            self._log_info(f"Cleaning up project: {filename}")

            book_dir = build_book_directory(filename)
            pdf_path = build_downloads_path(filename)

            cleaned_items = []

            # Remove book directory (contains images, texts, scripts)
            if book_dir.exists():
                shutil.rmtree(book_dir)
                cleaned_items.append(f"Directory: {book_dir}")

            # Remove PDF file
            if pdf_path.exists():
                pdf_path.unlink()
                cleaned_items.append(f"File: {pdf_path}")

            result = {
                "filename": filename,
                "cleaned_items": cleaned_items,
                "total_items": len(cleaned_items),
            }

            self._log_info(f"Successfully cleaned up project: {filename}")
            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to cleanup project: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def list_available_projects(self) -> ServiceResult:
        """
        List all available projects in the downloads directory.

        Returns:
            ServiceResult with list of projects
        """
        try:
            self._log_info("Listing available projects")

            downloads_dir = Path("downloads")
            if not downloads_dir.exists():
                return ServiceResult.success([])

            projects = []
            for pdf_file in downloads_dir.glob("*.pdf"):
                filename = pdf_file.name
                status_result = self.get_project_status(filename)

                if status_result.success:
                    project_info = {"filename": filename, "status": status_result.data}
                    projects.append(project_info)

            result = {"projects": projects, "total_projects": len(projects)}

            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to list available projects: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_text_content(self, filename: str, page_number: int) -> ServiceResult:
        """
        Get text content for a specific page.

        Args:
            filename: PDF filename
            page_number: Page number

        Returns:
            ServiceResult with text content
        """
        try:
            text_path = resolve_text_path(filename, page_number)

            if not text_path.exists():
                return ServiceResult.failure(
                    f"Text file not found for page {page_number}"
                )

            with open(text_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = {
                "filename": filename,
                "page_number": page_number,
                "content": content,
                "file_path": str(text_path),
            }

            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to get text content: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_image_path(self, filename: str, page_number: int) -> ServiceResult:
        """
        Get image path for a specific page.

        Args:
            filename: PDF filename
            page_number: Page number

        Returns:
            ServiceResult with image path
        """
        try:
            image_path = resolve_image_path(filename, page_number)

            if not image_path.exists():
                return ServiceResult.failure(
                    f"Image file not found for page {page_number}"
                )

            result = {
                "filename": filename,
                "page_number": page_number,
                "image_path": str(image_path),
                "exists": True,
            }

            return ServiceResult.success(result)

        except Exception as e:
            error_msg = f"Failed to get image path: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)
