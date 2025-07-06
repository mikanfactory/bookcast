# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the application**: `streamlit run src/bookcast/app.py`
- **Install dependencies**: `uv install`
- **Install dev dependencies**: `uv sync --dev`
- **Run tests**: `pytest`
- **Code formatting**: `ruff format`
- **Linting**: `ruff check`

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
   - `src/bookcast/models.py`: Pydantic models for data validation (ChapterConfig, Chapters, PodcastSetting)
   - `src/bookcast/session_state.py`: Streamlit session state management enums
   - `src/bookcast/voice_option.py`: Voice selection system with male/female options
   - `src/bookcast/config.py`: Environment configuration and API key management

3. **Page Flow** (Japanese UI):
   - Project selection (プロジェクトの選択): PDF upload and processing
   - Chapter selection (章の選択): Choose specific chapters/pages
   - Podcast setting (ポッドキャストの設定): Configure voices and conversation parameters
   - Podcast script (ポッドキャストの設定): AI-generated conversation scripts
   - Podcast generation (ポッドキャスト): Final output

4. **Dependencies**:
   - Uses `uv` for Python package management with workspace configuration
   - Requires Gemini API key (`GEMINI_API_KEY` environment variable)
   - Environment configuration: `ENV` (development/production), `GOOGLE_CLOUD_STORAGE_BUCKET`
   - PDF processing: `pypdf`, `pdf2image`, `pillow`
   - AI integration: `google-genai` (Gemini 2.0 Flash for script generation)
   - Web framework: `streamlit` with multi-page navigation
   - Testing: `pytest`, `pytest-asyncio`, `pytest-cov`

5. **Data Flow**:
   - Uploaded PDFs stored in `downloads/` directory
   - PDF converted to images in `downloads/{book_name}/images/`
   - OCR text extracted to `downloads/{book_name}/texts/`
   - Generated scripts saved to `downloads/{book_name}/scripts/`
   - Sample voices available in `downloads/sample_voices/` (30 voice options)

6. **Project Structure**:
   - `src/bookcast/`: Main application code
   - `experiment/`: Development and testing scripts
   - `scripts/`: Utility scripts (e.g., `download_sample_tts.py`)
   - `tests/`: Test directory (currently empty)
   - Navigation uses hidden positioning with session state management

The application uses Gemini AI for OCR text extraction and AI-powered podcast script generation with configurable conversation personalities. The UI is in Japanese and supports multi-step workflow with persistent session state.