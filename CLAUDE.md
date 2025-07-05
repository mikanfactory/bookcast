# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the application**: `streamlit run app.py`
- **Install dependencies**: `uv install`
- **Code formatting**: `ruff format`
- **Linting**: `ruff check`

## Architecture Overview

This is a Streamlit-based application that processes PDF books for podcast creation through the following workflow:

1. **PDF Processing Pipeline**:
   - Upload PDF files via Streamlit interface (`bookcast/pages/project.py`)
   - Convert PDF pages to images using `pdf2image` (`bookcast/pdf_to_image.py`)
   - Extract text using Gemini API OCR (`bookcast/ocr.py`)
   - Generate podcast scripts using AI (`bookcast/script_writing.py`)

2. **Core Components**:
   - `app.py`: Entry point (currently configured to run script writing directly)
   - `bookcast/page.py`: Defines multi-page Streamlit navigation with hidden positioning
   - `bookcast/models.py`: Pydantic models for data validation (ChapterConfig, Chapters, PodcastSetting)
   - `bookcast/session_state.py`: Streamlit session state management enums
   - `bookcast/voice_option.py`: Voice selection system with male/female options

3. **Page Flow**:
   - Project selection: PDF upload and processing
   - Chapter selection: Choose specific chapters/pages
   - Podcast script: AI-generated conversation scripts
   - Podcast setting: Configure voices and conversation parameters  
   - Podcast generation: Final output

4. **Dependencies**:
   - Uses `uv` for Python package management
   - Requires Gemini API key (`GEMINI_API_KEY` environment variable)
   - PDF processing: `pypdf`, `pdf2image`, `pillow`
   - AI integration: `google-genai` (Gemini 2.0 Flash for script generation)

5. **Data Flow**:
   - Uploaded PDFs stored in `downloads/` directory
   - PDF converted to images in `downloads/{book_name}/images/`
   - OCR text extracted to `downloads/{book_name}/texts/`
   - Generated scripts saved to `downloads/{book_name}/scripts/`
   - Sample voices available in `downloads/sample_voices/`

The application uses Gemini AI for OCR text extraction and AI-powered podcast script generation with configurable conversation personalities.