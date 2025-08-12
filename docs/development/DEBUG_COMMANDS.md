# Debug Commands & Development Utilities

*Quick reference for debugging and development workflows*

## Environment Setup
```bash
# Activate development environment
source venv/bin/activate

# Check all dependencies are working
python -c "
import pytesseract, numpy, PIL, ollama, sqlite3
from sentence_transformers import SentenceTransformer
import faiss
from google.cloud import vision
print('✅ All dependencies available')
"
```

## Testing Commands

### Run Specific Test Categories
```bash
# All tests with coverage
python -m pytest -v --cov=src --cov-report=term-missing

# Fast tests only (skip slow/integration)
python -m pytest -v -m "not slow and not integration"

# Database tests only
python -m pytest -v -m database tests/test_database.py

# OCR tests only (when created)
python -m pytest -v -m ocr

# Run with debug output
GHOST_WRITER_LOG_LEVEL=DEBUG python -m pytest -v -s tests/test_database.py::TestDatabaseManager::test_database_initialization
```

### Continuous Testing During Development
```bash
# Watch for changes and re-run tests
python -m pytest --tb=short -x -v tests/test_database.py

# Run single test with full output
python -m pytest -v -s tests/test_database.py::TestDatabaseManager::test_insert_and_get_note
```

## Debugging Tools Usage

### Performance Profiling
```python
from src.utils.debug_helpers import profiler, start_profiling, stop_profiling

# Start profiling
start_profiling()

# Your code here
result = some_function()

# Stop and show results
stop_profiling()
```

### Memory Tracking
```python
from src.utils.debug_helpers import memory_tracker

# Track memory during operation
memory_tracker.take_snapshot("before_operation")
run_memory_intensive_operation()
memory_tracker.take_snapshot("after_operation") 
memory_tracker.compare_snapshots("before_operation", "after_operation")
```

### Quick Debug Inspection
```python
from src.utils.debug_helpers import quick_debug, debug_context

# Quick object inspection
quick_debug(complex_object, "my_object")

# Debug context for operations
with debug_context("ocr_processing"):
    result = process_image(image_path)
```

## Database Debugging

### Inspect Database State
```python
from src.utils.database import DatabaseManager

db = DatabaseManager()
stats = db.get_database_stats()
print(f"Database stats: {stats}")

# Check for data integrity issues
from src.utils.debug_helpers import validator
issues = validator.validate_database_state(db)
if issues:
    print(f"Database issues: {issues}")
```

### Manual Database Operations
```python
# Direct database inspection
import sqlite3
conn = sqlite3.connect("data/database/ghost_writer.db")
conn.row_factory = sqlite3.Row

# Check table contents
cursor = conn.execute("SELECT * FROM notes LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

# Check indexes
cursor = conn.execute("PRAGMA index_list('notes')")
indexes = cursor.fetchall()
print(f"Indexes: {indexes}")
```

## Configuration Debugging

### Check Current Configuration
```python
from src.utils.config import config

print(f"OCR Provider: {config.get('ocr.default_provider')}")
print(f"Database Path: {config.get('database.path')}")
print(f"Daily Budget: {config.get('ocr.providers.hybrid.cost_limit_per_day')}")

# Validate configuration
if config.validate_config():
    print("✅ Configuration valid")
else:
    print("❌ Configuration invalid")
```

### Override Configuration for Testing
```bash
# Temporary overrides
GHOST_WRITER_LOG_LEVEL=DEBUG GHOST_WRITER_DB_PATH=test.db python script.py
```

## Log Analysis

### View Recent Logs
```bash
# Show recent log entries
tail -f data/logs/ghost_writer.log

# Filter for errors only
grep "ERROR" data/logs/ghost_writer.log

# Filter for performance data
grep "PERFORMANCE" data/logs/ghost_writer.log

# Show call traces
grep "CALL\|RESULT" data/logs/ghost_writer.log | head -20
```

### Log Levels for Different Scenarios
```bash
# Debug everything
export GHOST_WRITER_LOG_LEVEL=DEBUG

# Normal operation
export GHOST_WRITER_LOG_LEVEL=INFO  

# Errors only
export GHOST_WRITER_LOG_LEVEL=ERROR
```

## System Dependencies Check

### Verify External Tools
```bash
# Check Tesseract
tesseract --version
tesseract --list-langs

# Check Ollama
ollama list
ollama run llama3:latest "test message"

# Check disk space
df -h data/
```

### Performance Benchmarking
```python
from src.utils.debug_helpers import assert_performance
import time

# Ensure function meets performance requirements
def slow_operation():
    time.sleep(0.1)  # Simulate work
    return "result"

# This will fail if operation takes >0.05 seconds
try:
    result = assert_performance(slow_operation, 0.05)
    print("Performance test passed")
except AssertionError as e:
    print(f"Performance test failed: {e}")
```

## Test Data Management

### Regenerate Test Data
```bash
# Create fresh test images and data
python tests/fixtures/create_test_data.py

# Check what test data exists
ls -la tests/fixtures/
cat tests/fixtures/test_data.json | jq '.sample_notes[0]'
```

### Inspect Test Images
```python
from PIL import Image
import json

# Load ground truth data
with open("tests/fixtures/sample_images/ground_truth.json") as f:
    ground_truth = json.load(f)

for item in ground_truth:
    print(f"Image: {item['filename']}, Expected: {item['text']}")
    img = Image.open(item['path'])
    print(f"Size: {img.size}, Mode: {img.mode}")
```

## Common Debugging Scenarios

### OCR Not Working
```python
# Test Tesseract directly
import pytesseract
from PIL import Image

image = Image.open("tests/fixtures/sample_images/sample_1.png")
text = pytesseract.image_to_string(image)
print(f"OCR Result: {text}")

# Check confidence scores
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
print(f"Confidence scores: {data['conf']}")
```

### Database Locks/Issues
```bash
# Check for database locks
lsof data/database/ghost_writer.db

# Reset database (WARNING: destroys data)
rm data/database/ghost_writer.db
python -c "from src.utils.database import DatabaseManager; db = DatabaseManager()"
```

### Memory Issues
```python
import gc
import psutil

# Force garbage collection
gc.collect()

# Check memory usage
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Check for memory leaks
from src.utils.debug_helpers import MemoryTracker
tracker = MemoryTracker()
tracker.take_snapshot("start")
# ... run problematic code ...
tracker.take_snapshot("end")
tracker.compare_snapshots("start", "end")
```

## Emergency Reset Commands

### Clean Slate Reset
```bash
# WARNING: This destroys all data
rm -rf data/database/
rm -rf data/faiss_index/ 
rm -rf data/logs/
mkdir -p data/{database,faiss_index,logs,notes,style_corpus}

# Reinitialize
python -c "
from src.utils.database import DatabaseManager
from src.utils.config import config
db = DatabaseManager()
print('Database reinitialized')
"
```

### Partial Reset (Keep Notes)
```bash
# Reset only processing artifacts
rm -rf data/faiss_index/
rm -rf data/logs/
mkdir -p data/{faiss_index,logs}

# Clear embeddings but keep notes
python -c "
from src.utils.database import DatabaseManager
db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('DELETE FROM embeddings')
    conn.execute('DELETE FROM expansions')
    conn.commit()
print('Cleared embeddings and expansions')
"
```

## Development Workflow Integration

### Pre-commit Checks
```bash
# Run before committing code
python -m pytest -x --tb=short
python -m pytest --cov=src --cov-fail-under=80
```

### Quick Health Check
```bash
# Verify system is working
python -c "
from src.utils.database import DatabaseManager
from src.utils.config import config
db = DatabaseManager()
stats = db.get_database_stats()
print(f'✅ Database: {stats[\"total_notes\"]} notes')
print(f'✅ Config: {config.get(\"ocr.default_provider\")} provider')
print('✅ System healthy')
"
```