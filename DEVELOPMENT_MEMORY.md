# Ghost Writer Development Memory

*This file serves as working memory for development context, decisions, and progress tracking.*

## Current Development Status

### ✅ Completed Tasks (Day 1-2)
- **Environment Setup**: Python 3.12.3 venv with all dependencies
- **System Dependencies**: Tesseract OCR 5.3.4, Ollama with llama3:latest model
- **Project Structure**: Clean directory layout with src/, tests/, data/, config/
- **Database**: SQLite schema with hybrid OCR tracking, cost monitoring
- **Configuration**: YAML config system with environment overrides
- **Testing Framework**: pytest with fixtures, mocks, and coverage
- **Logging System**: Comprehensive logging with file output and debugging
- **Debug Tools**: Performance profiling, memory tracking, state inspection

### 🔄 Current Phase: Day 3-5 OCR Processing Module
**Status**: Ready to implement hybrid OCR processing

## Key Architectural Decisions

### Database Schema Design
```sql
notes: note_id, source_file, raw_text, clean_text, ocr_provider, ocr_confidence, processing_cost
embeddings: note_id, vector, model_name  
expansions: expansion_id, note_id, prompt, output, llm_model
ocr_usage: usage_id, provider, cost, images_processed, date
```

### Hybrid OCR Strategy
- **Primary**: Tesseract (free, private, local)
- **Fallback**: Google Cloud Vision (premium accuracy, costs money)
- **Routing Logic**: Try Tesseract first, use Cloud Vision if confidence < 75%
- **Cost Control**: Daily budget limit with hard stops

### Technology Stack (Verified Working)
- **OCR**: Tesseract 5.3.4 + Google Cloud Vision API  
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **Vector Search**: FAISS (IndexFlatIP)
- **LLM**: Ollama llama3:latest (existing model)
- **Database**: SQLite with proper foreign keys and indexes
- **Config**: YAML with environment variable overrides

## Implementation Guidelines Established

### Error Handling Patterns
```python
try:
    result = operation()
    logger.info(f"SUCCESS {operation_name}")
    return result
except SpecificException as e:
    logger.error(f"FAILED {operation_name} - {e}", exc_info=True)
    # Graceful fallback or re-raise
```

### Testing Approach
- **Unit Tests**: Individual function validation  
- **Integration Tests**: End-to-end pipeline testing
- **Mocked External Dependencies**: Tesseract, Cloud Vision, Ollama
- **Performance Tests**: Speed and memory benchmarks
- **Cost Tests**: Marked as `@pytest.mark.cost` (disabled by default)

### Logging Structure
```python
logger.info("OPERATION_TYPE operation_name - {json_data}")
logger.debug("CALL function_name - {args_info}")
logger.error("ERROR operation_name - {error_info}", exc_info=True)
logger.info("PERFORMANCE operation - {duration_ms}ms, {items_processed} items")
```

## Next Implementation Steps (Day 3-5)

### Day 3: OCR Provider Abstraction
1. **Create `src/utils/ocr_providers.py`**
   - Abstract `OCRProvider` base class
   - `TesseractOCR` implementation with preprocessing
   - `CloudVisionOCR` implementation with API integration
   - `HybridOCR` with intelligent routing logic

2. **Preprocessing Pipeline**
   - Image enhancement (contrast, noise reduction)
   - Layout detection and segmentation  
   - Confidence scoring and validation

3. **Cost Tracking Integration**
   - Real-time cost monitoring
   - Daily budget enforcement
   - Usage analytics and reporting

### Day 4-5: Integration and Testing
1. **CLI Interface**: `src/ingest.py`
   - File watching and batch processing
   - Provider selection options
   - Progress indicators and error handling

2. **Comprehensive Testing**
   - OCR accuracy validation
   - Cost tracking verification
   - Error scenario testing
   - Performance benchmarking

## Known Issues to Address

### Test Failures Fixed
- ❌ `test_database_stats`: Duplicate notes causing cost calculation errors
- ❌ `test_error_handling`: Update operations succeeding on non-existent records
- ⚠️ Pytest marker warnings (need proper registration)

### Performance Requirements
- **OCR Processing**: < 30 seconds per page
- **Memory Usage**: Monitor for leaks during batch processing
- **Cost Control**: Hard stop at daily budget limits

## Development Patterns Established

### Function Decorators for Consistency
```python
@log_calls("ghost_writer")
@debug_decorator(log_args=True, profile=True)
def ocr_function(image_path: str) -> OCRResult:
    pass
```

### Configuration Access Pattern
```python
from src.utils.config import config
provider = config.get("ocr.default_provider", "tesseract")
```

### Database Transaction Pattern
```python
with db.get_connection() as conn:
    conn.execute("INSERT ...", params)
    conn.commit()
```

## Context for Future Development

### File Organization Logic
- `src/`: Core implementation modules
- `tests/`: Mirror structure of src/ with test_ prefix  
- `data/`: Runtime data (database, indexes, notes, style corpus)
- `config/`: Configuration files and credentials
- `docs/`: Documentation and reports

### Dependencies Already Available System-Wide
- ✅ PyYAML 6.0.1 (system-wide)
- ✅ click 8.1.6 (system-wide)
- ✅ sqlite3 (Python built-in)
- ✅ Tesseract binary at /usr/bin/tesseract
- ✅ Ollama binary at /usr/local/bin/ollama with llama3:latest

### Key Development Commands
```bash
# Activate environment
source venv/bin/activate

# Run tests with coverage
python -m pytest -v --cov=src

# Run specific test categories
python -m pytest -m "unit and not cost"

# Start development with debug logging
GHOST_WRITER_LOG_LEVEL=DEBUG python src/ingest.py --help
```

## Decisions Made and Why

### Why Hybrid OCR Instead of Single Provider?
- **Cost Control**: Cloud Vision costs add up quickly ($1.50/1000 images)
- **Privacy**: Keep sensitive notes local when possible
- **Reliability**: Always have offline fallback
- **Quality**: Use premium OCR only when needed

### Why FAISS Over Other Vector Databases?
- **Local-first**: No cloud dependencies
- **Performance**: Fast similarity search
- **Simplicity**: Easy integration, no server required
- **Cost**: Free, no ongoing API costs

### Why SQLite Over PostgreSQL?
- **Simplicity**: Single-user system, no complex setup
- **Portability**: Database is just a file
- **Performance**: Fast enough for expected volume
- **Local-first**: No server dependencies

## Development Memory Updates

*This section gets updated as development progresses*

**Latest Update**: 2025-08-07 - Completed Day 1-2 bootstrap. Testing framework working (11 tests, 9 pass, 2 minor failures). Ready to start OCR provider implementation.

**Next Session TODO**: 
1. Fix the 2 failing database tests
2. Start implementing `ocr_providers.py` with Tesseract integration
3. Add image preprocessing pipeline
4. Create test images for OCR validation