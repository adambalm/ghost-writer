"""
Simple focused tests to validate OCR business logic step by step
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile
from pathlib import Path

from src.utils.ocr_providers import OCRResult, HybridOCR


def test_hybrid_provider_priority_logic():
    """Test the core provider priority logic in isolation"""
    
    config = {
        'quality_mode': 'balanced',
        'cost_limit_per_day': 5.0,
        'provider_priority': ['qwen', 'tesseract', 'google_vision', 'gpt4_vision']
    }
    
    # Create HybridOCR but bypass provider initialization
    hybrid = HybridOCR.__new__(HybridOCR)  # Skip __init__
    hybrid.config = config
    hybrid.providers = {}  # Empty providers for now
    
    # Test priority calculation logic directly
    priority = hybrid._get_provider_priority('balanced', 0.0, 5.0)
    
    assert priority == ['qwen', 'tesseract', 'google_vision', 'gpt4_vision']
    
    # Test over-budget scenario
    priority_over_budget = hybrid._get_provider_priority('balanced', 6.0, 5.0)
    
    assert priority_over_budget == ['qwen', 'tesseract']  # Only free provider when over budget


def test_ocr_result_confidence_validation():
    """Test OCR result validation logic"""
    
    from src.utils.ocr_providers import TesseractOCR
    
    # Use concrete provider for testing validation
    config = {'confidence_threshold': 75}
    provider = TesseractOCR(config)
    
    # Test high confidence result
    high_confidence = OCRResult("Good text", 0.85, "test", 1.0)
    assert provider.validate_result(high_confidence) == True
    
    # Test low confidence result  
    low_confidence = OCRResult("Poor text", 0.65, "test", 1.0)
    assert provider.validate_result(low_confidence) == False
    
    # Test empty result
    empty_result = OCRResult("", 0.0, "test", 1.0)
    assert provider.validate_result(empty_result) == False


def test_provider_selection_with_mocked_database():
    """Test provider selection with properly mocked dependencies"""
    
    # Create temp image
    temp_dir = Path(tempfile.mkdtemp())
    test_image = temp_dir / "test.png"
    Image.new('RGB', (100, 100), 'white').save(test_image)
    
    config = {
        'quality_mode': 'balanced',
        'confidence_thresholds': {'tesseract': 75, 'google_vision': 85},
        'cost_limit_per_day': 5.0,
        'provider_priority': ['tesseract', 'google_vision']
    }
    
    # Mock the database calls completely
    mock_db = MagicMock()
    mock_db.get_daily_ocr_cost.return_value = {}  # Zero daily costs
    mock_db.track_ocr_usage.return_value = True
    
    # Create provider manually to control initialization
    hybrid = HybridOCR.__new__(HybridOCR)
    hybrid.config = config
    hybrid.name = "hybrid"
    
    # Create mock providers with predictable behavior
    mock_tesseract = MagicMock()
    mock_tesseract.extract_text.return_value = OCRResult(
        text="Tesseract result",
        confidence=0.70,  # Below threshold
        provider="tesseract",
        processing_time=1.0,
        cost=0.0
    )
    
    mock_google = MagicMock() 
    mock_google.extract_text.return_value = OCRResult(
        text="Google Vision result",
        confidence=0.90,  # Above threshold
        provider="google_vision",
        processing_time=2.0,
        cost=0.0015
    )
    
    hybrid.providers = {
        'tesseract': mock_tesseract,
        'google_vision': mock_google
    }
    
    # Patch the DatabaseManager creation within the method
    with patch('src.utils.ocr_providers.DatabaseManager', return_value=mock_db):
        
        result = hybrid.extract_text(test_image)
        
        print(f"Result: provider={result.provider}, confidence={result.confidence}, text='{result.text}'")
        print(f"Mock calls: {mock_db.track_ocr_usage.call_args_list}")
        
        # Verify behavior
        assert result.provider == "google_vision"
        assert result.confidence == 0.90
        
        # Verify database tracking was called
        mock_db.track_ocr_usage.assert_called_with("google_vision", 0.0015)
    
    # Cleanup
    test_image.unlink()
    temp_dir.rmdir()


if __name__ == "__main__":
    test_hybrid_provider_priority_logic()
    test_ocr_result_confidence_validation() 
    test_provider_selection_with_mocked_database()
    print("All simple tests passed!")