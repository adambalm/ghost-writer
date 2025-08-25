# Ghost Writer System Patterns

## Architecture Patterns

### Unified Service Layer Pattern
```python
# Single service interface eliminating CLI/web duplication
class SupernoteService:
    def __init__(self):
        self.ocr_provider = create_hybrid_ocr_provider()
    
    def process_note_file(self, note_path: Path, output_dir: Path) -> Dict:
        # Standard processing workflow
        image_paths = convert_note_to_images(note_path, temp_dir)
        ocr_results = []
        for img_path in image_paths:
            if img_path.exists():
                result = self.ocr_provider.extract_text(str(img_path))
                if result.text.strip():
                    ocr_results.append({
                        "text": result.text,
                        "confidence": result.confidence,
                        "provider": result.provider
                    })
        return {
            "success": True,
            "note_path": str(note_path),
            "extracted_images": [str(p) for p in image_paths],
            "ocr_results": ocr_results,
            "processed_at": datetime.now().isoformat()
        }
```

### Error Handling Pattern
```python
# Comprehensive error handling with user-friendly messages
try:
    success = supernote_service.authenticate_supernote(phone, password)
    if success:
        return jsonify({'success': True, 'message': f'Successfully connected!'})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})
except Exception as e:
    if 'network' in str(e).lower():
        user_error = 'Network connection failed. Please check your internet connection.'
    elif 'timeout' in str(e).lower():
        user_error = 'Connection timed out. Please try again.'
    else:
        user_error = f'Authentication error: {str(e)}'
    return jsonify({'success': False, 'error': user_error})
```

### Flask Application Structure Pattern
```python
# Unified web application with standardized endpoints
app = Flask(__name__, template_folder=str(project_root / "templates"))
app.secret_key = os.urandom(24)

@app.route('/authenticate', methods=['POST'])  # Authentication
@app.route('/process-file', methods=['POST'])   # File processing
@app.route('/upload', methods=['POST'])         # File upload
@app.route('/status')                          # System status
@app.route('/reset-auth', methods=['POST'])    # Development helper
```

## Code Patterns

### Virtual Environment Enforcement
```bash
# MANDATORY pattern - never run Python without .venv
source .venv/bin/activate && python script.py
source .venv/bin/activate && python -m pytest tests/ -v
source .venv/bin/activate && python src/web/unified_app.py
```

### Testing Pattern - Direct Mocking
```python
# Avoid complex patching - use direct dependency injection
@pytest.fixture
def service(self):
    service = SupernoteService.__new__(SupernoteService)
    service.ocr_provider = Mock()
    return service

def test_process_note_file_success(self, mock_convert, service, temp_note_file):
    # Setup mocks for external dependencies
    mock_convert.return_value = [mock_image_path]
    service.ocr_provider.extract_text.return_value = mock_ocr_result
    
    # Test business logic
    result = service.process_note_file(temp_note_file, temp_output_dir)
    assert result["success"] is True
```

### Playwright E2E Pattern
```python
# End-to-end testing with real browser automation
class TestE2EWebProcessing:
    def setup_method(self):
        # Reset authentication state before each test
        response = requests.post('http://localhost:5000/reset-auth')
        assert response.json()['success'] is True
    
    def test_authentication_flow(self, page):
        page.goto('http://localhost:5000')
        page.fill('#phone', os.getenv('SUPERNOTE_PHONE'))
        page.fill('#password', os.getenv('SUPERNOTE_PASSWORD'))
        page.click('#authenticate-btn')
        expect(page.locator('#auth-success')).to_be_visible()
```

### Configuration Management Pattern
```python
# Environment-based configuration with fallbacks
from dotenv import load_dotenv
load_dotenv()

# Global state management
authenticated = False
cloud_files = []
last_sync_time = None

def refresh_cloud_files():
    global cloud_files, last_sync_time
    try:
        cloud_files = supernote_service.list_cloud_files()
        last_sync_time = datetime.now()
    except Exception as e:
        logger.error(f"Failed to refresh cloud files: {e}")
```

## Documentation Patterns

### Test Documentation Pattern
```python
"""
Comprehensive test descriptions following enterprise standards:

TestSupernoteService:
- test_process_note_file_success: Happy path with valid .note file
- test_process_note_file_no_images: Edge case handling when extraction fails
- test_process_note_file_exception: Error handling during processing
- test_authenticate_supernote_success: Valid credentials flow
- test_authenticate_supernote_failure: Invalid credentials handling
"""
```

### Memory Bank Documentation Pattern
```markdown
# Structured context preservation
- active-context.md: Current session state and pending tasks
- product-context.md: Complete project overview and architecture
- system-patterns.md: Reusable patterns and best practices
- decision-log.md: Technical decisions with rationale
- progress.md: Development timeline and achievements
```

### Enterprise Code Review Standards
```python
# Patterns that pass IBM/Google/Microsoft review standards:
1. 95%+ test coverage on core components
2. Comprehensive error handling with user-friendly messages
3. No hardcoded credentials or configuration
4. Proper separation of concerns (service layer pattern)
5. Consistent naming conventions and documentation
6. Edge case testing and exception handling
7. E2E validation with real browser automation
```

### Process Hygiene Pattern
```bash
# Standardized development workflow
1. Always use feature branches (feat/, fix/, chore/)
2. Activate .venv for ALL Python operations
3. Run tests before commits: source .venv/bin/activate && python -m pytest tests/ -v
4. Use port 5000 consistently (no process stranding)
5. Update memory bank with progress tracking
```