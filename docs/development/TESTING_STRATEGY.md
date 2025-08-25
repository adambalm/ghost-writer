# Ghost Writer Testing Strategy

## Testing Framework Overview

### Test Categories and Markers
```python
@pytest.mark.unit        # Fast, isolated tests
@pytest.mark.integration # End-to-end workflow tests  
@pytest.mark.slow        # Tests >5 seconds
@pytest.mark.ocr         # OCR functionality tests
@pytest.mark.database    # Database operation tests
@pytest.mark.api         # External API tests
@pytest.mark.cost        # Tests that may incur costs (disabled by default)
```

### Test Structure
```
tests/
├── conftest.py              # Fixtures and test configuration
├── test_database.py         # Database functionality tests
├── test_ocr_providers.py    # OCR provider tests (to be created)
├── test_embeddings.py       # Embedding and search tests (to be created)
├── test_llm.py             # LLM integration tests (to be created)
├── test_integration.py      # End-to-end tests (to be created)
└── fixtures/               # Test data and sample files
    ├── sample_images/       # Test images with known text
    ├── style_samples/       # Writing style examples
    └── test_data.json       # Structured test data
```

## Key Testing Fixtures Available

### Database Testing
- `test_db`: Clean SQLite database for each test
- `sample_notes_data`: Structured test data for database operations
- `test_config`: Configuration with temporary paths

### OCR Testing  
- `sample_image`: Generated test image
- `mock_tesseract`: Mocked Tesseract responses
- `mock_cloud_vision`: Mocked Google Cloud Vision responses
- `test_data_generator`: Utilities for creating test images

### Performance Testing
- `performance_tracker`: Time and measure operations
- `memory_tracker`: Track memory usage during tests

## Testing Patterns Established

### Unit Test Pattern
```python
@pytest.mark.unit
@pytest.mark.database
def test_specific_function(test_db, sample_data):
    # Arrange
    setup_data(sample_data)
    
    # Act  
    result = function_under_test(input_data)
    
    # Assert
    assert result.expected_property == expected_value
    assert len(result.items) == expected_count
```

### Integration Test Pattern
```python
@pytest.mark.integration
def test_full_workflow(test_db, test_config, sample_image):
    # Test complete pipeline: image -> OCR -> storage -> search
    with performance_tracker:
        result = complete_pipeline(sample_image)
    
    # Verify each stage worked
    assert result.ocr_confidence > 0.8
    assert result.note_id in database
    performance_tracker.assert_duration_under("full_workflow", 30.0)
```

### Mocking Pattern for External Dependencies
```python
def test_ocr_with_mocked_tesseract(mock_tesseract, sample_image):
    # Arrange
    mock_tesseract.image_to_string.return_value = "Expected OCR text"
    
    # Act
    with patch('pytesseract.image_to_string', mock_tesseract.image_to_string):
        result = ocr_provider.extract_text(sample_image)
    
    # Assert
    assert result.text == "Expected OCR text"
    mock_tesseract.image_to_string.assert_called_once()
```

## Test Data Management

### Static Test Data
- **Sample Images**: Pre-created images with known text content
- **Style Corpus**: Example writing samples for style matching
- **OCR Ground Truth**: Expected outputs for accuracy testing

### Dynamic Test Data Generation
```python
def test_with_generated_data(test_data_generator, temp_dir):
    # Generate test image with specific text
    image_path = test_data_generator.create_handwriting_sample(
        temp_dir, "This is test handwriting", "test.png"
    )
    
    # Test OCR on generated image
    result = ocr_provider.extract_text(image_path)
    assert "test handwriting" in result.text.lower()
```

## Performance Testing Guidelines

### Response Time Requirements
- **OCR Processing**: < 30 seconds per page
- **Database Operations**: < 100ms for basic CRUD
- **Search Operations**: < 500ms response time
- **Embedding Generation**: < 2 seconds per note

### Memory Testing
```python
def test_memory_usage_during_batch_processing(memory_tracker):
    memory_tracker.take_snapshot("start")
    
    # Process many files
    for i in range(100):
        process_file(f"test_{i}.png")
    
    memory_tracker.take_snapshot("end")
    memory_tracker.compare_snapshots("start", "end")
    
    # Assert memory didn't grow excessively
    assert memory_difference < 100  # MB
```

## Cost Testing Strategy

### Mock All Expensive Operations by Default
```python
# Default: All tests use free mocks
@pytest.fixture(autouse=True)
def mock_expensive_operations():
    with patch('google.cloud.vision.ImageAnnotatorClient'):
        yield
```

### Explicit Cost Tests (Disabled by Default)
```python
@pytest.mark.cost
@pytest.mark.skipif(not os.getenv("ENABLE_COST_TESTS"), reason="Cost tests disabled")
def test_real_cloud_vision_accuracy():
    # Only run when explicitly enabled
    # Will actually call Google Cloud Vision API
    pass
```

## Error Testing Patterns

### Network Failures
```python
def test_ocr_with_network_failure(mock_cloud_vision):
    mock_cloud_vision.side_effect = ConnectionError("Network failed")
    
    # Should gracefully fall back to Tesseract
    result = hybrid_ocr.extract_text(sample_image)
    assert result.provider == "tesseract"
    assert result.text is not None
```

### File System Errors
```python
def test_database_with_read_only_filesystem(test_db, tmp_path):
    # Make directory read-only
    tmp_path.chmod(0o444)
    
    with pytest.raises(sqlite3.OperationalError):
        test_db.insert_note("test", "file.png", "text", "clean", "tesseract", 0.8)
```

### Invalid Input Data
```python
@pytest.mark.parametrize("invalid_image", [
    "nonexistent.png",
    "corrupted_file.png", 
    "",
    None
])
def test_ocr_with_invalid_images(invalid_image):
    with pytest.raises(ValueError, match="Invalid image"):
        ocr_provider.extract_text(invalid_image)
```

## Continuous Testing Commands

### Run All Tests
```bash
# Full test suite with coverage
python -m pytest -v --cov=src --cov-report=html

# Fast tests only (no integration/slow tests)
python -m pytest -v -m "not slow and not integration"

# Specific test categories
python -m pytest -m "unit and database"
python -m pytest -m "ocr and not cost"
```

### Watch Mode for Development
```bash
# Re-run tests on file changes
python -m pytest --tb=short -x -v tests/test_database.py
```

### Coverage Requirements
- **Minimum Coverage**: 80% (enforced by pytest)
- **Critical Modules**: Database, OCR providers must have >90%
- **Integration Tests**: Must cover complete workflows
- **Error Handling**: All exception paths must be tested

## Test Data Validation

### OCR Result Validation
```python
def validate_ocr_result(result):
    assert hasattr(result, 'text')
    assert hasattr(result, 'confidence')  
    assert hasattr(result, 'provider')
    assert 0 <= result.confidence <= 1
    assert result.provider in ['tesseract', 'cloud_vision', 'hybrid']
```

### Database State Validation  
```python
def validate_database_integrity(db):
    # Check for orphaned records
    issues = validator.validate_database_state(db)
    assert len(issues) == 0, f"Database integrity issues: {issues}"
```

## Debugging Failed Tests

### Enable Debug Logging for Tests
```bash
GHOST_WRITER_LOG_LEVEL=DEBUG python -m pytest -v -s tests/test_failing.py
```

### Inspect Test State
```python
def test_with_debug_inspection(test_db):
    # Use debug helpers
    quick_debug(test_db.get_database_stats(), "db_stats")
    
    with debug_context("test_operation"):
        result = operation_under_test()
    
    # Check result state
    StateInspector.log_variable_state("result", result, "test_end")
```

This comprehensive testing strategy ensures reliability, performance, and maintainability throughout development.