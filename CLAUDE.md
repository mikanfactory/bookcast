# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the application**: `streamlit run src/bookcast/app.py`
- **Install dependencies**: `uv install`
- **Install dev dependencies**: `uv sync --dev`
- **Run tests**: `pytest` or `make test`
- **Code formatting**: `ruff format` or `make format`
- **Linting**: `ruff check` or `make lint`

## Architecture Overview

This is a Streamlit-based application that processes PDF books for podcast creation through the following workflow:

1. **PDF Processing Pipeline**:
   - Upload PDF files via Streamlit interface (`src/bookcast/pages/project.py`)
   - Convert PDF pages to images using `pdf2image` (`src/bookcast/pdf_to_image.py`)
   - Extract text using Gemini API OCR (`src/bookcast/ocr.py`)
   - Generate podcast scripts using AI (`src/bookcast/script_writing.py`)

2. **Core Components**:
   - `src/bookcast/app.py`: Entry point that creates the Streamlit multi-page navigation
   - `src/bookcast/page.py`: Defines multi-page Streamlit navigation with hidden positioning and Japanese UI
   - `src/bookcast/session_state.py`: Streamlit session state management enums
   - `src/bookcast/voice_option.py`: Voice selection system with male/female options
   - `src/bookcast/config.py`: Environment configuration and API key management

3. **Data Layer**:
   - **Entities**: `src/bookcast/entities/` - Pydantic models (Project, Chapter)
   - **Repositories**: `src/bookcast/repositories/` - Data access layer for Supabase operations
   - **Database**: `src/bookcast/services/db.py` - Supabase client configuration
   - **Migrations**: `supabase/migrations/` - Database schema definitions

4. **Page Flow** (Japanese UI):
   - Project selection (プロジェクトの選択): PDF upload and processing
   - Chapter selection (章の選択): Choose specific chapters/pages
   - Podcast setting (ポッドキャストの設定): Configure voices and conversation parameters
   - Podcast script (ポッドキャストの設定): AI-generated conversation scripts
   - Podcast generation (ポッドキャスト): Final output

5. **Dependencies**:
   - Uses `uv` for Python package management with workspace configuration
   - Requires Gemini API key (`GEMINI_API_KEY` environment variable)
   - Environment configuration: `ENV` (development/production), `GOOGLE_CLOUD_STORAGE_BUCKET`
   - PDF processing: `pypdf`, `pdf2image`, `pillow`
   - AI integration: `google-genai` (Gemini 2.0 Flash for script generation)
   - Web framework: `streamlit` with multi-page navigation
   - Database: `supabase` for project and chapter data persistence
   - Testing: `pytest`, `pytest-asyncio`, `pytest-cov`

6. **Data Flow**:
   - Uploaded PDFs stored in `downloads/` directory
   - PDF converted to images in `downloads/{book_name}/images/`
   - OCR text extracted to `downloads/{book_name}/texts/`
   - Generated scripts saved to `downloads/{book_name}/scripts/`
   - Sample voices available in `downloads/sample_voices/` (30 voice options)

   - Project metadata and chapter information persisted in Supabase database

7. **Project Structure**:
   - `src/bookcast/`: Main application code
   - `experiment/`: Development and testing scripts
   - `scripts/`: Utility scripts (e.g., `download_sample_tts.py`)
   - `tests/`: Test directory (currently empty)
   - Navigation uses hidden positioning with session state management

The application uses Gemini AI for OCR text extraction and AI-powered podcast script generation with configurable conversation personalities. The UI is in Japanese and supports multi-step workflow with persistent session state.