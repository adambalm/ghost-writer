# Ghost Writer - Handwritten Note Processing System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org/)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-brightgreen.svg)](pytest.ini)

A focused, local-first toolkit that transforms handwritten notes into structured digital artifacts with AI-assisted content expansion.

## 🎯 Project Status: Phase 1 Development

**Current Status**: Foundation Complete - OCR Implementation Next
- ✅ Database schema and operations
- ✅ Configuration system with hybrid OCR support  
- ✅ Comprehensive testing and debugging framework
- ✅ Logging and performance monitoring
- 🔄 **Next**: Hybrid OCR provider implementation (Tesseract + Google Cloud Vision)

## 🏗️ Architecture Overview

```
Handwritten Notes → OCR Processing → SQLite Storage → Semantic Search → LLM Expansion
                         ↓              ↓              ↓              ↓
                    Tesseract/      Vector Index    FAISS Search   Ollama LLM
                   Cloud Vision     (384-dim)       (similarity)   (llama3)
```

## 📋 Features (MVP Scope)

### ✅ Completed
- **Database Layer**: SQLite with cost tracking and provider metadata
- **Configuration**: YAML config with environment overrides
- **Testing**: pytest with fixtures, mocks, and 80%+ coverage requirement
- **Logging**: Structured logging with performance tracking
- **Debug Tools**: Profiling, memory tracking, state inspection

### 🔄 In Progress  
- **Hybrid OCR**: Tesseract (free/private) + Cloud Vision (premium/accurate)
- **Cost Control**: Daily budget limits with automatic fallbacks
- **Image Preprocessing**: Enhancement pipeline for better OCR accuracy

### 📅 Planned
- **Semantic Search**: FAISS vector search with sentence-transformers
- **Content Expansion**: Local LLM via Ollama for style-consistent generation
- **CLI Interface**: Simple command-line tools for ingestion and querying

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Tesseract OCR
- Ollama with llama3 model

### Installation
```bash
# Clone and setup
git clone https://github.com/adambalm/ghost-writer.git
cd ghost-writer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python -c "from src.utils.database import DatabaseManager; print('✅ Setup complete')"
```

### Basic Usage (Coming Soon)
```bash
# Ingest handwritten notes
python src/ingest.py --input data/notes/ --provider hybrid

# Search archived notes
python src/query.py --text "machine learning concepts" --limit 5

# Expand note into content
python src/develop.py --note-id abc123 --prompt "Expand into blog post"
```

## 🧪 Testing & Development

### Run Tests
```bash
# Full test suite with coverage
python -m pytest -v --cov=src --cov-report=html

# Quick tests (no slow/integration)
python -m pytest -v -m "not slow and not integration"

# Database tests only
python -m pytest -v -m database
```

### Generate Test Data
```bash
python tests/fixtures/create_test_data.py
```

### Debug Mode
```bash
GHOST_WRITER_LOG_LEVEL=DEBUG python -m pytest -v -s
```

## 📁 Project Structure

```
ghost-writer/
├── src/
│   ├── utils/
│   │   ├── database.py          # SQLite operations
│   │   ├── config.py            # Configuration management
│   │   ├── logging_setup.py     # Logging utilities
│   │   └── debug_helpers.py     # Development tools
│   ├── ingest.py               # OCR processing (planned)
│   ├── query.py                # Search interface (planned)
│   └── develop.py              # Content expansion (planned)
├── tests/
│   ├── conftest.py             # Test fixtures
│   ├── test_database.py        # Database tests
│   └── fixtures/               # Test data
├── config/
│   └── config.yaml             # Main configuration
├── data/                       # Runtime data (gitignored)
│   ├── database/               # SQLite files
│   ├── notes/                  # Input notes
│   └── style_corpus/           # Writing samples
└── docs/                       # Documentation
    ├── DEVELOPMENT_MEMORY.md   # Development context
    ├── TESTING_STRATEGY.md     # Testing approach
    └── DEBUG_COMMANDS.md       # Debugging reference
```

## ⚙️ Configuration

### OCR Providers
```yaml
ocr:
  default_provider: "hybrid"
  providers:
    tesseract:
      confidence_threshold: 60
    cloud_vision:
      confidence_threshold: 70  
    hybrid:
      cost_limit_per_day: 5.00
      prefer_local: true
```

### Environment Variables
```bash
# Optional overrides
GHOST_WRITER_LOG_LEVEL=DEBUG
GHOST_WRITER_DB_PATH=custom/path.db
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## 📊 Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| OCR Processing | <30s per page | 🔄 Testing |
| Database CRUD | <100ms | ✅ Achieved |
| Search Query | <500ms | 📅 Planned |
| Embedding Gen | <2s per note | 📅 Planned |

## 🔐 Privacy & Cost Control

### Local-First Design
- **Tesseract OCR**: Completely local processing, zero cost
- **SQLite**: Local database, no cloud dependencies
- **Ollama LLM**: Local inference, private content

### Cost Monitoring
- Real-time tracking of Google Cloud Vision API usage
- Daily budget limits with automatic fallbacks
- Detailed cost analytics and reporting

## 🧑‍💻 Development

### Key Development Files
- **`DEVELOPMENT_MEMORY.md`**: Current context and architectural decisions
- **`TESTING_STRATEGY.md`**: Comprehensive testing approach  
- **`DEBUG_COMMANDS.md`**: Quick debugging reference
- **`PHASE1_IMPLEMENTATION_PLAN.md`**: Detailed implementation roadmap

### Development Workflow
1. Review current context in `DEVELOPMENT_MEMORY.md`
2. Run tests: `python -m pytest -v`
3. Use debug helpers from `src.utils.debug_helpers`
4. Update development memory after changes

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure 80%+ test coverage
5. Update `DEVELOPMENT_MEMORY.md` with context
6. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.