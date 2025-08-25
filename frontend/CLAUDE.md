# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bookcast is a Streamlit-based web application that converts PDF documents into podcast-style audio files. The frontend provides an interface for uploading PDFs, configuring chapters, and monitoring audio generation progress.

## Development Commands

This project uses `uv` as the package manager and Python environment tool.

### Common Commands
- **Run app**: `uv run streamlit run src/bookcast/app.py`
- **Install dependencies**: `uv sync`
- **Lint code**: `make lint` or `uv run ruff check src tests`
- **Format code**: `make format` or `uv run ruff format src tests && uv run ruff check --fix src tests`
- **Run tests**: `make test` or `uv run pytest tests`
- **Run integration tests**: `make test/integration` or `uv run pytest -m integration tests`

### Environment Setup
- Copy `.env.org` to `.env` and configure:
  - `GOOGLE_CLOUD_PROJECT`: GCP project ID
  - `GOOGLE_CLOUD_LOCATION`: GCP region
  - `BACKEND_URL`: API backend endpoint
  - `GOOGLE_CLOUD_DEVELOPMENT_STORAGE_BUCKET`: Dev GCS bucket
  - `GOOGLE_CLOUD_PRODUCTION_STORAGE_BUCKET`: Prod GCS bucket

## Architecture

### Multi-Page Streamlit Application
The app uses Streamlit's navigation system with three main pages:

1. **Project Page** (`pages/project.py`): PDF upload and project creation
2. **Chapter Selection Page** (`pages/select_chapter.py`): PDF viewer for chapter configuration
3. **Podcast Page** (`pages/podcast.py`): Processing status and audio download

### Key Components

- **View Models** (`view_models.py`): Pydantic models for data validation
  - `ProjectViewModel`: Manages project state and chapter configurations
  - `ChapterViewModel`: Handles individual chapter start/end pages
- **Services** (`services/`): Business logic layer
  - `image_file.py`: PDF to image conversion using pdf2image
  - `audio_file.py`: Audio file management and GCS integration
- **Session State** (`session_state.py`): Streamlit session state management
- **Config** (`config.py`): Environment-based configuration with dotenv

### State Flow
1. User uploads PDF → backend creates project
2. PDF converted to images for chapter selection UI
3. User configures chapter boundaries via visual interface
4. Processing pipeline: OCR → Script generation → TTS → Audio compilation
5. Final audio files stored in GCS and available for download

## Code Standards

- **Linting**: Ruff configured with E, F, W, I, C9 rules (line length: 120)
- **Testing**: pytest with unit/integration test markers
- **Type Hints**: Use proper type annotations, avoid `any`/`unknown`
- **Data Validation**: Pydantic models for all data structures
- **Error Handling**: Comprehensive exception handling for API calls and file operations

## Dependencies

- **Core**: Streamlit, Pydantic, Requests
- **PDF Processing**: pdf2image, Pillow
- **Cloud**: google-cloud-storage
- **Config**: python-dotenv, PyYAML
- **Dev Tools**: Ruff (linter/formatter), pytest, ipython

## Backend Integration

The frontend communicates with a separate backend API via HTTP requests. Key integration points:
- Project creation and status polling
- File upload and processing coordination  
- Audio file retrieval from Google Cloud Storage