# Ghost Writer Project - Complete Context

## Description
Ghost Writer: OCR and document processing system for handwritten notes with commercial-grade unified architecture.

## Primary Objectives
- Unified service layer eliminating CLI/web architectural duplication
- Enterprise-grade test coverage (95-100%) across all core components
- Commercial licensing compatibility (no GPL/AGPL dependencies)
- Supernote Cloud integration with .note file processing
- Hybrid OCR pipeline with intelligent routing

## Technologies
- **Backend**: Python 3.12.3, Flask web framework
- **Testing**: pytest, Playwright for E2E testing
- **OCR**: Tesseract 5.3.4, Google Vision API, GPT-4 Vision
- **Image Processing**: PIL/Pillow, numpy
- **File Processing**: Custom Supernote .note decoder
- **Database**: SQLite with vector embeddings
- **Environment**: Ubuntu 24.04, Virtual environment (.venv)

## Architecture
### Core Components:
- **SupernoteService**: Unified service layer for note processing, authentication, cloud operations
- **Unified Web App**: Single Flask application replacing duplicate viewers (port 5000)
- **Hybrid OCR Pipeline**: Multi-provider OCR with cost controls and intelligent routing
- **Concept Clustering**: Multi-strategy concept extraction and thematic organization
- **Structure Generation**: Multiple document formats (outline, mindmap, timeline, process)

### Service Layer Pattern:
```python
SupernoteService (unified interface)
├── process_note_file() - Core processing workflow
├── authenticate_supernote() - Cloud authentication
├── list_cloud_files() - File management
└── download_cloud_file() - File retrieval
```

## Project Structure
```
/home/ed/ghost-writer/
├── src/
│   ├── services/
│   │   └── supernote_service.py (100% coverage)
│   ├── web/
│   │   └── unified_app.py (98% coverage)
│   ├── utils/
│   │   ├── concept_clustering.py (98% coverage)
│   │   ├── ocr_providers.py (34% coverage - optional improvement)
│   │   └── supernote_parser_enhanced.py (10% coverage - optional)
│   └── cli.py
├── tests/
│   ├── test_supernote_service_simple.py (16 test cases)
│   ├── test_unified_app.py (33 test cases) 
│   ├── test_e2e_web_processing.py (5 Playwright tests)
│   └── test_concept_clustering.py
├── templates/
│   └── unified_index.html
├── .venv/ (Python virtual environment - MANDATORY)
├── uploads/ (temporary file storage)
├── results/ (processed output)
└── memory-bank/ (context persistence)
```

## Current Status
- **Test Coverage**: 84 tests passing, 0 failures
- **Core Components Coverage**: SupernoteService (100%), Web App (98%), Concept Clustering (98%)
- **CI/CD**: All GitHub Actions passing
- **Authentication**: Supernote Cloud integration verified (67 files discovered)
- **Architecture**: Unified service layer eliminating duplication
- **Standards**: Enterprise-grade quality suitable for IBM/Google/Microsoft review

## Dependencies & Licensing
- **Commercial Safe**: Flask, PIL, numpy, pytest, requests
- **LICENSING RISK**: sn2md/supernotelib (external dependency - priority for replacement)
- **Virtual Environment**: All operations MUST use .venv activation

## Critical Configuration
- **Port**: 5000 (standardized, no process stranding)
- **Authentication**: Phone-based Supernote Cloud login
- **File Processing**: .note files → images → OCR → structured output
- **Error Handling**: Comprehensive validation and user-friendly messages