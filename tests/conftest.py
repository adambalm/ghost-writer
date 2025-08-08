"""
PyTest configuration and fixtures for Ghost Writer
"""

import pytest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock
from PIL import Image
import numpy as np

# Import our modules
import sys
sys.path.append('src')

from src.utils.database import DatabaseManager
from src.utils.config import Config
from src.utils.logging_setup import GhostWriterLogger


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration"""
    config_dict = {
        "database": {"path": str(temp_dir / "test.db")},
        "ocr": {
            "default_provider": "tesseract",
            "providers": {
                "tesseract": {"confidence_threshold": 60},
                "hybrid": {"cost_limit_per_day": 1.0}
            }
        },
        "faiss": {"index_path": str(temp_dir / "faiss/")},
        "style": {"corpus_path": str(temp_dir / "style/")},
        "logging": {"level": "DEBUG", "file_path": str(temp_dir / "test.log")}
    }
    
    config = Config.__new__(Config)
    config._config = config_dict
    config.config_path = temp_dir / "config.yaml"
    return config


@pytest.fixture
def test_db(test_config, temp_dir):
    """Create test database with proper isolation"""
    # Create unique database file for each test
    import uuid
    db_file = temp_dir / f"test_{uuid.uuid4().hex[:8]}.db"
    db = DatabaseManager(str(db_file))
    yield db
    # Cleanup database file after test
    if db_file.exists():
        db_file.unlink()


@pytest.fixture
def test_logger(temp_dir):
    """Create test logger"""
    config = {
        "level": "DEBUG",
        "file_path": str(temp_dir / "test.log"),
        "max_file_size": "1MB",
        "backup_count": 2
    }
    logger = GhostWriterLogger("test_logger", config)
    return logger


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image with text"""
    img = Image.new('RGB', (400, 100), color='white')
    # This would normally have text drawn on it, but for now just a white image
    img_path = temp_dir / "sample_image.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return "This is a sample handwritten note for testing OCR functionality."


@pytest.fixture
def sample_notes_data():
    """Sample notes data for database testing"""
    return [
        {
            "note_id": "note1",
            "source_file": "test1.png",
            "raw_text": "Raw text from OCR",
            "clean_text": "Clean text after processing",
            "ocr_provider": "tesseract",
            "ocr_confidence": 0.85,
            "processing_cost": 0.0
        },
        {
            "note_id": "note2",
            "source_file": "test2.png", 
            "raw_text": "Another raw text",
            "clean_text": "Another clean text",
            "ocr_provider": "cloud_vision",
            "ocr_confidence": 0.92,
            "processing_cost": 0.0015
        }
    ]


@pytest.fixture
def mock_tesseract():
    """Mock Tesseract OCR"""
    mock = MagicMock()
    mock.image_to_string.return_value = "Mocked OCR text"
    mock.image_to_data.return_value = {
        'conf': [85, 90, 80],
        'text': ['Mocked', 'OCR', 'text']
    }
    return mock


@pytest.fixture
def mock_cloud_vision():
    """Mock Google Cloud Vision"""
    mock = MagicMock()
    
    # Mock response structure
    mock_response = MagicMock()
    mock_response.text_annotations = [
        MagicMock(description="Mocked Cloud Vision text", confidence=0.95)
    ]
    mock_response.full_text_annotation.text = "Mocked Cloud Vision text"
    
    mock.detect_text.return_value = mock_response
    return mock


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer model"""
    mock = MagicMock()
    # Return consistent embeddings for testing
    mock.encode.return_value = np.random.rand(384)  # 384-dim embedding
    return mock


@pytest.fixture
def mock_faiss_index():
    """Mock FAISS index"""
    mock = MagicMock()
    mock.search.return_value = (
        np.array([[0.8, 0.7, 0.6]]),  # distances
        np.array([[0, 1, 2]])         # indices
    )
    mock.add.return_value = None
    return mock


@pytest.fixture
def mock_ollama():
    """Mock Ollama client"""
    mock = MagicMock()
    mock.generate.return_value = {
        'response': 'This is a mocked LLM response expanding the input text.',
        'done': True
    }
    return mock


@pytest.fixture(autouse=True)
def setup_test_dirs(temp_dir):
    """Automatically create test directories"""
    dirs = ['database', 'faiss_index', 'style_corpus', 'notes', 'logs', 'reports']
    for dir_name in dirs:
        (temp_dir / dir_name).mkdir(exist_ok=True)


class TestDataGenerator:
    """Utility class for generating test data"""
    
    @staticmethod
    def create_test_image_with_text(text: str, size=(400, 100)) -> Image.Image:
        """Create a PIL Image with text (requires PIL with text support)"""
        img = Image.new('RGB', size, color='white')
        # In a real implementation, you'd draw text on the image
        # For now, just return a white image
        return img
    
    @staticmethod
    def create_handwriting_sample(temp_dir: Path, text: str, filename: str = "handwriting.png"):
        """Create a simulated handwriting sample"""
        img = TestDataGenerator.create_test_image_with_text(text)
        img_path = temp_dir / filename
        img.save(img_path)
        return str(img_path)
    
    @staticmethod
    def create_style_corpus(temp_dir: Path, samples: list):
        """Create style corpus files"""
        style_dir = temp_dir / "style_corpus"
        style_dir.mkdir(exist_ok=True)
        
        files = []
        for i, sample in enumerate(samples):
            file_path = style_dir / f"style_sample_{i+1}.txt"
            file_path.write_text(sample)
            files.append(str(file_path))
        
        return files


@pytest.fixture
def test_data_generator():
    """Test data generator instance"""
    return TestDataGenerator()


# Performance testing utilities
@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
        
        def start_timer(self, operation: str):
            self.metrics[operation] = {"start": time.time()}
        
        def end_timer(self, operation: str):
            if operation in self.metrics:
                self.metrics[operation]["duration"] = time.time() - self.metrics[operation]["start"]
        
        def get_duration(self, operation: str) -> float:
            return self.metrics.get(operation, {}).get("duration", 0.0)
        
        def assert_duration_under(self, operation: str, max_duration: float):
            duration = self.get_duration(operation)
            assert duration < max_duration, f"{operation} took {duration:.3f}s, expected < {max_duration}s"
    
    return PerformanceTracker()


# Skip tests that require external resources
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "requires_tesseract: requires Tesseract OCR binary")
    config.addinivalue_line("markers", "requires_ollama: requires Ollama service") 
    config.addinivalue_line("markers", "requires_internet: requires internet connection")


# Parameterized test data
@pytest.fixture(params=["tesseract", "cloud_vision", "hybrid"])
def ocr_provider(request):
    """Parameterized OCR provider for testing all providers"""
    return request.param


@pytest.fixture(params=[0.6, 0.8, 0.9])
def confidence_threshold(request):
    """Parameterized confidence thresholds"""
    return request.param