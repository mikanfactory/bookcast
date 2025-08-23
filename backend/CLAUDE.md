# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the FastAPI application**: `uv run fastapi dev src/bookcast/main.py`
- **Install dependencies**: `uv sync`
- **Install dev dependencies**: `uv sync --dev`
- **Run tests**: `uv run pytest` or `make test`
- **Run integration tests**: `uv run pytest -m integration` or `make test/integration`
- **Code formatting**: `ruff format` or `make format`
- **Linting**: `ruff check` or `make lint`
- **Start local database**: `make db/start`
- **Reset local database**: `make db/clean`
- **Deploy server**: `make deploy/server`

## Architecture Overview

This is a FastAPI-based backend application that processes PDF books for podcast creation through the following workflow:

1. **PDF Processing Pipeline**:
   - Upload PDF files via API endpoints
   - Convert PDF pages to images using `pdf2image`
   - Extract text using Gemini API OCR via LangGraph workflows
   - Generate podcast scripts using AI
   - Text-to-speech conversion and audio processing

2. **FastAPI Backend Structure**:
   - `src/bookcast/main.py`: FastAPI application entry point with router registration
   - `src/bookcast/routers/`: API endpoints for project and chapter operations
   - `src/bookcast/internal/worker.py`: Background processing worker endpoints
   - `src/bookcast/config.py`: Environment configuration and API key management

3. **Data Layer**:
   - **Entities**: `src/bookcast/entities/` - Pydantic models (Project, Chapter) with status enums
   - **Repositories**: `src/bookcast/repositories/` - Data access layer for Supabase operations
   - **Services**: `src/bookcast/services/` - Business logic (OCR, TTS, script writing, audio processing)
   - **Database**: `src/bookcast/services/db.py` - Supabase client configuration
   - **Migrations**: `supabase/migrations/` - Database schema definitions

4. **Infrastructure**:
   - **Google Cloud Storage**: `src/bookcast/infrastructure/gcs.py` - File upload/storage
   - **Path Resolution**: `src/bookcast/path_resolver.py` - Consistent file path handling

5. **AI Processing**:
   - **OCR Service**: Uses LangGraph state machine with Gemini API for document text extraction
   - **Script Writing**: AI-powered podcast script generation from extracted text
   - **TTS Service**: Text-to-speech conversion for audio generation
   - **Audio Service**: Audio file processing and manipulation

6. **Dependencies**:
   - Uses `uv` for Python package management with workspace configuration
   - **Environment Variables**: `GEMINI_API_KEY`, `ENV`, `GOOGLE_CLOUD_STORAGE_BUCKET`, Supabase credentials
   - **AI**: `google-genai`, `langchain`, `langchain-google-genai`, `langgraph`
   - **PDF Processing**: `pypdf`, `pdf2image`, `pillow`
   - **Web Framework**: `fastapi` with standard features
   - **Database**: `supabase` for project and chapter data persistence
   - **Audio**: `pydub` for audio processing

7. **Data Flow**:
   - PDFs uploaded via API to Google Cloud Storage or local `downloads/` directory
   - PDF converted to images in `downloads/{book_name}/images/`
   - OCR text extracted to `downloads/{book_name}/texts/`
   - Generated scripts saved to `downloads/{book_name}/scripts/`
   - Audio files generated in `downloads/{book_name}/audio/`
   - Sample voices available in `downloads/sample_voices/` (30 voice options)
   - Project and chapter metadata persisted in Supabase database with status tracking

8. **Status Management**:
   - Both Project and Chapter entities have detailed status enums tracking processing stages
   - Status progression: not_started → start_ocr → ocr_completed → start_writing_script → writing_script_completed → start_tts → tts_completed → start_creating_audio → creating_audio_completed

The application uses Gemini AI for OCR text extraction and AI-powered podcast script generation with LangGraph workflows for robust processing pipelines.