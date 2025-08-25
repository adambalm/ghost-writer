# Ghost Writer Project Setup Guide

## Current System Status
- **Python Version**: 3.12.3 ✅ (meets requirement 3.9+)
- **Ollama**: Installed ✅ (/usr/local/bin/ollama)
- **Tesseract**: Installed ✅ (required for baseline OCR)

## Required Dependencies

### System Dependencies
```bash
# Install Tesseract OCR (if not already installed)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Qwen2.5-VL vision model for local transcription
ollama pull qwen2.5vl:7b

# Verify installations
tesseract --version
ollama --version
```

### Python Dependencies
Create `requirements.txt`:
```
pytesseract==3.10.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4
ollama==0.1.7
Pillow==10.0.1
numpy==1.24.3
PyYAML==6.0.1
click==8.1.7
```

Install with:
```bash
pip install -r requirements.txt
```

### Local Vision Model (Primary OCR)
```bash
# Download Qwen2.5-VL (7B parameters - superior handwriting recognition)
ollama pull qwen2.5vl:7b

# Optional: Llama 3.2 for text generation tasks
ollama pull llama3.2:3b

# Verify models are available
ollama list
```

## Required Services & Accounts

### No External API Tokens Required
✅ **Local-first architecture** - no cloud API dependencies
- SQLite: Local database (no setup required)
- FAISS: Local vector search (no setup required)  
- Ollama: Local LLM inference (no API keys)
- Tesseract: Local OCR processing (no API keys)

### Optional: Supernote Integration (Future)
- Supernote account credentials (for cloud sync)
- Local .note file processing (no credentials required)

## Project Directory Structure

```
ghost-writer/
├── src/
│   ├── __init__.py
│   ├── ingest.py              # OCR ingestion pipeline
│   ├── query.py               # Search interface  
│   ├── develop.py             # Content expansion
│   ├── evaluate.py            # Testing and metrics
│   └── utils/
│       ├── __init__.py
│       ├── ocr.py             # OCR processing utilities
│       ├── embeddings.py      # Semantic embedding utilities
│       ├── database.py        # SQLite operations
│       └── llm.py             # Ollama LLM utilities
├── data/
│   ├── notes/                 # Raw input notes (.note, .png)
│   ├── database/              # SQLite database files
│   ├── faiss_index/           # Vector search indices
│   └── style_corpus/          # Writing style examples
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_query.py
│   ├── test_develop.py
│   └── fixtures/              # Test data
├── config/
│   └── config.yaml            # Configuration settings
├── docs/
│   └── evaluation_report.md   # Results documentation
├── requirements.txt
├── setup.py
├── README.md
└── .env.example               # Environment variables template
```

## Configuration Setup

### config.yaml
```yaml
# Database settings
database:
  path: "data/database/ghost_writer.db"
  
# OCR settings  
ocr:
  tesseract_config: "--oem 3 --psm 6"
  confidence_threshold: 60
  
# Embedding settings
embeddings:
  model_name: "all-MiniLM-L6-v2"
  dimension: 384
  
# FAISS settings
faiss:
  index_path: "data/faiss_index/"
  
# LLM settings
llm:
  model: "llama3.2:3b"
  temperature: 0.7
  max_tokens: 1000
  
# Style corpus
style:
  corpus_path: "data/style_corpus/"
  min_examples: 3
  
# Processing settings
processing:
  max_retries: 3
  timeout_seconds: 30
  log_level: "INFO"
```

### .env.example
```bash
# Optional environment overrides
# GHOST_WRITER_DB_PATH=/custom/path/to/database.db
# GHOST_WRITER_LOG_LEVEL=DEBUG
# TESSERACT_CMD=/usr/local/bin/tesseract
```

## Development Environment Setup

### 1. Clone and Setup
```bash
cd /home/ed/ghost-writer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create Directory Structure
```bash
mkdir -p src/utils data/{notes,database,faiss_index,style_corpus} tests/fixtures config docs
```

### 3. Initialize Database
```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/database/ghost_writer.db')
conn.execute('''
    CREATE TABLE notes (
        note_id TEXT PRIMARY KEY,
        source_file TEXT,
        raw_text TEXT,
        clean_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.execute('''
    CREATE TABLE embeddings (
        note_id TEXT,
        vector BLOB,
        FOREIGN KEY(note_id) REFERENCES notes(note_id)
    )
''')
conn.execute('''
    CREATE TABLE expansions (
        expansion_id TEXT PRIMARY KEY,
        note_id TEXT,
        prompt TEXT,
        output TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('Database initialized successfully')
"
```

### 4. Setup Style Corpus
```bash
# Create sample style files
mkdir -p data/style_corpus
echo "This is a sample writing style example." > data/style_corpus/example1.txt
echo "Add your own writing samples here." > data/style_corpus/example2.txt
```

## Pre-Development Checklist

### System Requirements ✅/❌
- [ ] Python 3.9+ installed
- [ ] Tesseract OCR installed and accessible
- [ ] Ollama installed with llama3.2:3b model
- [ ] Virtual environment created and activated
- [ ] All Python dependencies installed
- [ ] Project directory structure created
- [ ] Database initialized with schema
- [ ] Configuration file created
- [ ] Style corpus directory prepared

### Development Environment ✅/❌
- [ ] IDE/editor configured with Python path
- [ ] Git repository initialized (optional)
- [ ] Linting tools configured (optional: black, flake8)
- [ ] Test framework setup (pytest)

### Testing Preparation ✅/❌
- [ ] Sample handwritten notes prepared for testing
- [ ] Ground truth text for OCR accuracy evaluation
- [ ] Test fixtures directory populated
- [ ] Evaluation metrics baseline established

## Installation Commands Summary

```bash
# 1. System dependencies
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# 2. Python environment  
python -m venv venv
source venv/bin/activate

# 3. Python packages
pip install -r requirements.txt

# 4. Local vision model (primary OCR)
ollama pull qwen2.5vl:7b

# 5. Project structure
mkdir -p src/utils data/{notes,database,faiss_index,style_corpus} tests/fixtures config docs

# 6. Verify setup
python -c "import pytesseract, sentence_transformers, faiss, ollama; print('All dependencies imported successfully')"
```

## Troubleshooting

### Common Issues:
1. **Tesseract not found**: Ensure `/usr/bin/tesseract` exists or update PATH
2. **FAISS installation fails**: Use `faiss-cpu` instead of `faiss-gpu` on non-GPU systems
3. **Ollama connection errors**: Start ollama service with `ollama serve`
4. **Permission errors**: Check write permissions for `data/` directories

### Verification Tests:
```bash
# Test OCR
python -c "import pytesseract; print('OCR ready')"

# Test embeddings
python -c "from sentence_transformers import SentenceTransformer; print('Embeddings ready')"

# Test vector search
python -c "import faiss; print('FAISS ready')"

# Test LLM
ollama run llama3.2:3b "Hello, world!"
```