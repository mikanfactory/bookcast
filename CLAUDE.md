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
   - Upload PDF files via Streamlit interface
   - Split PDFs into chapters using AI-powered detection (`bookcast/pdf_chapter_splitter.py`)
   - Convert PDF pages to images for OCR processing
   - Extract text using Gemini API OCR (`bookcast/ocr.py`)

2. **Core Components**:
   - `app.py`: Main entry point that initializes Streamlit page navigation
   - `bookcast/page.py`: Defines the multi-page Streamlit application structure
   - `bookcast/config.py`: Environment configuration and API key management
   - `bookcast/pages/`: Individual page components for the workflow

3. **Page Structure**:
   - Project selection page: PDF file upload
   - Chapter selection page: Choose chapters to process
   - Podcast settings page: Configure output parameters
   - Podcast page: Generate and display results

4. **Dependencies**:
   - Uses `uv` for Python package management
   - Requires Gemini API key (`GEMINI_API_KEY` environment variable)
   - PDF processing: `pypdf`, `pdf2image`, `pillow`
   - OCR: Gemini API integration via `google-genai`

5. **Data Flow**:
   - Uploaded PDFs stored in `downloads/` directory
   - Chapter PDFs split into `downloads/{book_name}/pdf/`
   - OCR text results saved to `downloads/{book_name}/ocr/`

The application leverages Gemini AI for both OCR text extraction and intelligent chapter boundary detection in PDF documents.