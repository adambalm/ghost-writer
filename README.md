# Ghost Writer v2.0 - Multi-Agent Handwritten Note Intelligence

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-132%20passed%2C%208%20failed-yellow.svg)](https://pytest.org/)
[![Multi-Agent](https://img.shields.io/badge/architecture-multi--agent-purple.svg)](CLAUDE.md)
[![Coverage](https://img.shields.io/badge/coverage-79%25-orange.svg)](pytest.ini)

## System Overview

Ghost Writer is an OCR and document processing system for handwritten notes. It transforms handwritten content into structured digital documents using OCR technology and document organization features.

### Current Status

- Hybrid OCR Pipeline: Tesseract + Google Vision + GPT-4 Vision with intelligent routing
- Document Processing: Relationship detection, concept clustering, structure generation  
- Test Coverage: 112/119 tests passing with 7 behavioral test failures
- Privacy & Cost Controls: Local-first processing with automatic budget management

## Architecture

```
   Handwritten Notes → Hybrid OCR → Relationship Detection → Concept Clustering → Structure Generation
         ↓                ↓              ↓                    ↓                    ↓
   Input Processing   Smart Router    Semantic Analysis    Theme Organization   Document Formats
   Image/PDF         Cost-Optimized   Visual Patterns     Idea Clustering     (Outline/Timeline)
```

### **Dual Beachhead Strategy**

1. **Privacy-Conscious Professionals**: Premium accuracy transcription with local-first processing
2. **Idea Organization for Learning Differences**: Transform scattered thoughts into coherent documents

## 🎯 **Core Features**

### **✅ Premium OCR Processing**
- **Hybrid Intelligence**: Tesseract (local/free) + Google Vision (premium) + GPT-4 Vision (semantic) + Qwen2.5-VL (local vision LLM)
- **Local Vision Models**: Qwen2.5-VL 7B via Ollama for superior handwriting transcription (2-4 second response time)
- **Smart Routing**: Cost-aware provider selection with confidence thresholds
- **Budget Controls**: Daily limits with automatic fallbacks ($5/day default)
- **Quality Modes**: Fast, Balanced, Premium processing options

### **✅ Idea Organization Engine**
- **Relationship Detection**: Visual arrows, spatial proximity, hierarchical patterns
- **Concept Clustering**: Multi-strategy extraction (topics, actions, entities)
- **Structure Generation**: Outlines, mind maps, timelines, process flows
- **Confidence Scoring**: Quality metrics for all generated structures

### **✅ Multi-Agent Coordination**
- **Document-Based Handoffs**: Agents communicate through structured artifacts
- **QA Agent**: Testing and integration validation (Gemini 2.5 Pro)
- **Implementation Agent**: Code development and optimization (Claude 4 Sonnet)
- **Supervisor Oversight**: Task coordination and quality assurance

### **✅ Privacy & Security**
- **Local-First Processing**: Tesseract + SQLite for sensitive content
- **Encrypted Storage**: Secure local database with audit trails
- **Zero Data Leakage**: Optional cloud processing with privacy controls

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12+
- Tesseract OCR
- Ollama (for local Qwen2.5-VL vision model)
- Optional: Google Cloud Vision API key
- Optional: OpenAI API key

### **Installation**
```bash
# Clone repository
git clone https://github.com/adambalm/ghost-writer.git
cd ghost-writer

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and setup Ollama with Qwen2.5-VL model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5vl:7b

# Initialize Ghost Writer
python -m src.cli init

# Verify installation
python -m pytest tests/ --tb=short -q
```

### **Command Line Usage**

**Process a single file:**
```bash
# Process an image file
python -m src.cli process my_notes.png

# Process a Supernote .note file
python -m src.cli process my_notebook.note --format all

# Process with premium quality
python -m src.cli process notes.jpg --quality premium --format pdf
```

**Process a directory:**
```bash
# Process all images in a directory
ghost-writer process notes_folder/ --output processed_notes/

# Local-only processing (no cloud APIs)
ghost-writer process notes/ --local-only --format markdown
```

**Watch directory for new files:**
```bash
# Automatically process new files
ghost-writer watch notes_folder/ --format all --interval 5
```

**Sync from Supernote Cloud:**
```bash
# Sync recent notes (requires configuration)
ghost-writer sync --since 2025-01-01 --output supernote_notes/
```

**Check system status:**
```bash
ghost-writer status
```

### **Basic API Usage**
```python
from src.cli import process_single_file
from src.utils.ocr_providers import HybridOCR
from src.utils.relationship_detector import RelationshipDetector
from src.utils.concept_clustering import ConceptExtractor, ConceptClusterer
from src.utils.structure_generator import StructureGenerator
from src.utils.database import DatabaseManager
from pathlib import Path

# Initialize components
ocr = HybridOCR()
detector = RelationshipDetector()
extractor = ConceptExtractor()
clusterer = ConceptClusterer()
generator = StructureGenerator()
db = DatabaseManager()

# Process a file
result = process_single_file(
    file_path=Path("my_notes.jpg"),
    ocr_provider=ocr,
    relationship_detector=detector,
    concept_extractor=extractor,
    concept_clusterer=clusterer,
    structure_generator=generator,
    db_manager=db,
    output_dir=Path("output/"),
    output_format="markdown",
    quality="balanced"
)

print(f"Generated: {result}")
```

## 🧪 **Testing & Quality**

### **Comprehensive Test Suite**
```bash
# Run full test suite (140 tests)
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_e2e_integration.py -v    # End-to-end workflows
python -m pytest tests/test_ocr_providers.py -v     # OCR processing
python -m pytest tests/test_concept_clustering.py -v # Idea organization
python -m pytest tests/test_database.py -v          # Data persistence

# Performance testing
python -m pytest tests/test_e2e_integration.py::TestPerformanceAndScaling -v
```

### **Quality Metrics**
- **Test Success Rate**: 94% (132/140 tests passing)
- **Integration Coverage**: Complete E2E pipeline validation
- **Performance**: <30s OCR processing, <10s idea organization
- **Reliability**: Comprehensive error handling and fallback mechanisms

## 📁 **Project Structure**

```
ghost-writer/
├── src/utils/
│   ├── ocr_providers.py         # Hybrid OCR with smart routing
│   ├── relationship_detector.py # Visual and semantic relationships
│   ├── concept_clustering.py    # Multi-strategy concept extraction
│   ├── structure_generator.py   # Document structure generation
│   └── database.py             # SQLite persistence layer
├── tests/
│   ├── test_e2e_integration.py  # Complete workflow testing
│   ├── test_e2e_simple.py      # Simplified integration tests
│   ├── test_ocr_providers.py   # OCR provider testing
│   ├── test_ocr_mocks.py       # Mock-based OCR testing
│   └── test_*.py               # Comprehensive test coverage
├── config/config.yaml          # System configuration
├── CLAUDE.md                   # Multi-agent system protocols
├── AGENT_STATUS.md             # Real-time agent coordination
├── HANDOFF_ARTIFACTS.md        # Inter-agent communication log
├── QUALITY_DASHBOARD.md        # Test results and metrics
└── PRODUCT_SPECIFICATION.md    # Complete product specification
```

## ⚙️ **Configuration**

### **OCR Provider Setup**
```yaml
ocr:
  providers:
    tesseract:
      confidence_threshold: 60
      preprocessing:
        enhance_contrast: true
        remove_noise: true
    google_vision:
      confidence_threshold: 80
      cost_per_image: 0.0015
    gpt4_vision:
      confidence_threshold: 85
      cost_per_image: 0.01
    hybrid:
      cost_limit_per_day: 5.00
      quality_mode: "balanced"
```

### **Environment Variables**
```bash
# Optional API keys for premium processing
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
OPENAI_API_KEY=your-openai-api-key

# System configuration
GHOST_WRITER_LOG_LEVEL=INFO
GHOST_WRITER_DB_PATH=data/ghost_writer.db
```

## 📊 **Performance Benchmarks**

| Component | Performance | Status |
|-----------|-------------|---------|
| OCR Processing | <30s per page | Target |
| Relationship Detection | <10s per page | Target |
| Concept Clustering | <5s per page | Target |
| Structure Generation | <5s per page | Target |
| Database Operations | <100ms | Target |
| Test Suite Execution | ~113s (140 tests) | Target |

## 🤖 **Multi-Agent System**

### **Agent Architecture**
- **Supervisor Agent**: Task coordination and quality oversight
- **QA Agent**: Testing, validation, and integration verification
- **Implementation Agent**: Feature development and optimization
- **Document-Based Communication**: Agents coordinate through structured artifacts

### **Coordination Protocols**
- **AGENT_STATUS.md**: Real-time agent state tracking
- **HANDOFF_ARTIFACTS.md**: Inter-agent communication log
- **QUALITY_DASHBOARD.md**: Performance metrics and test results
- **Cost Monitoring**: <$25/day budget with automatic controls

## 💰 **Pricing & Cost Control**

### **Cost Structure**
- **Local Processing**: $0 (Tesseract + SQLite)
- **Google Vision**: $0.0015/image (premium accuracy)
- **GPT-4 Vision**: $0.01/image (semantic understanding)
- **Daily Budget**: $5.00 default with automatic fallbacks

### **Value Proposition**
- **Privacy-Conscious**: 10x faster than manual transcription, zero privacy risk
- **Idea Organization**: Transform scattered thoughts into publishable content
- **ROI**: Predictable costs with automatic budget management

## 🔐 **Privacy & Security**

### **Local-First Architecture**
- **Tesseract OCR**: Complete local processing for sensitive content
- **SQLite Database**: Local storage with encrypted data
- **Audit Logging**: Full processing history and decision tracking
- **Optional Cloud**: Premium features only when explicitly enabled

### **Security Features**
- Zero data leakage in local mode
- Comprehensive audit trails
- API key management with environment isolation
- Cost controls prevent unexpected charges

## 🧑‍💻 **Development & Contributing**

### **Multi-Agent Development**
See [CLAUDE.md](CLAUDE.md) for complete multi-agent development protocols and architecture details.

### **Key Development Files**
- **CLAUDE.md**: Multi-agent system protocols and architecture
- **PRODUCT_SPECIFICATION.md**: Complete product requirements and roadmap
- **DECISION_HISTORY.md**: Architectural decisions and research findings
- **TESTING_STRATEGY.md**: Comprehensive testing approach

### **Contributing**
1. Review multi-agent protocols in [CLAUDE.md](CLAUDE.md)
2. Run comprehensive test suite: `python -m pytest tests/ -v`
3. Follow document-based development coordination
4. Ensure 100% test success rate
5. Update relevant .md documentation files

## Supernote Integration

### Supernote Cloud Sync

Ghost Writer includes Supernote integration with API authentication and file synchronization.

**Quick Test:**
```bash
# Test your Supernote Cloud connection
python debug_supernote_test.py
# Enter phone number: 4139491742 (or your number)
# Enter password: [your Supernote Cloud password]
```

**Features:**
- ✅ **Real API Integration**: Authenticated connection to Supernote Cloud
- ✅ **Phone Number Login**: Support for phone-based authentication  
- ✅ **Secure Authentication**: MD5+SHA256 hashing with random salt
- ✅ **File Synchronization**: Download .note files directly from cloud
- ✅ **Binary .note Parsing**: Extract vector graphics for OCR processing
- ✅ **HTTPS Security**: All communication encrypted, no plaintext passwords

**Quick Start:**
1. **Test Connection**: `python debug_supernote_test.py`
2. **Sync Files**: `ghost-writer sync --output ~/Downloads/`
3. **Process Notes**: `ghost-writer process downloaded_file.note --format markdown`

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.

## 📄 **License**

MIT License - see LICENSE file for details.

---

**Ghost Writer v2.0** - Transform handwritten notes into structured intelligence with multi-agent AI coordination and **live Supernote Cloud integration**.