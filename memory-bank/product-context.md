# Project Overview

## Description
Ghost Writer is an OCR and document processing system for handwritten notes that transforms handwritten content into structured digital documents using hybrid OCR technology and intelligent document organization features.

## Objectives
- Provide privacy-conscious handwritten note transcription with local-first processing
- Help users organize scattered thoughts and ideas into coherent documents
- Deliver high-accuracy OCR through hybrid approach with multiple providers
- Generate structured documents from unstructured handwritten content
- Maintain commercial viability with careful dependency management

## Technologies

### Core Technologies
- **Python 3.12+**: Primary development language
- **SQLite**: Local database for privacy-first storage
- **Flask**: Web interface framework
- **pytest**: Comprehensive testing framework

### OCR Providers
- **Tesseract 5.3.4**: Local, free OCR baseline
- **Qwen2.5-VL 7B**: Local vision LLM via Ollama (2-4s response)
- **Google Cloud Vision**: Premium accuracy ($0.0015/image)
- **GPT-4 Vision**: Semantic understanding ($0.01/image)

### Processing Libraries
- **NumPy**: Array and image processing
- **Pillow**: Image manipulation
- **sentence-transformers**: Semantic similarity
- **FAISS**: Vector similarity search

## Architecture

### Three-Layer Architecture
1. **Input Layer**: File handling, image preprocessing, format conversion
2. **Processing Layer**: Hybrid OCR, relationship detection, concept clustering
3. **Output Layer**: Structure generation, format export, database storage

### Key Components
- **Hybrid OCR Router**: Intelligent provider selection based on quality/cost
- **Relationship Detector**: Visual and semantic relationship analysis
- **Concept Clusterer**: Multi-strategy concept extraction and grouping
- **Structure Generator**: Multiple document format generation

### Data Flow
```
Input (Image/.note) → OCR → Relationship Detection → Concept Clustering → Structure Generation → Output (MD/PDF/JSON)
```

## Project Structure

### Main Directories
- **src/**: Core application code
  - **cli.py**: Command-line interface
  - **utils/**: Processing modules (OCR, clustering, etc.)
- **tests/**: Comprehensive test suite (137 tests)
- **config/**: Configuration files
- **memory-bank/**: Persistent project context
- **docs/**: Documentation
- **scripts/**: Utility and deployment scripts

### Key Files
- **CLAUDE.md**: Development protocols
- **README.md**: User documentation
- **requirements.txt**: Python dependencies
- **mypy.ini**: Type checking configuration
- **pytest.ini**: Test configuration

## Current Status
- **Development Phase**: Beta/Pre-production
- **Test Coverage**: 76% (exceeds 65% requirement)
- **Code Quality**: MyPy compliant, Ruff passing
- **CI/CD**: Enterprise Production Pipeline active
- **Known Issues**: Clean room decoder needs enhancement