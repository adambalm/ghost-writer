"""
Tests for OCR provider implementations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
from PIL import Image

from src.utils.ocr_providers import (
    OCRProvider, OCRResult, TesseractOCR, GoogleVisionOCR, 
    GPT4VisionOCR, HybridOCR, create_ocr_provider
)


@pytest.mark.unit
@pytest.mark.ocr
class TestOCRResult:
    
    def test_ocr_result_creation(self):
        """Test OCRResult dataclass creation"""
        result = OCRResult(
            text="Sample text",
            confidence=0.85,
            provider="test",
            processing_time=1.5,
            cost=0.001
        )
        
        assert result.text == "Sample text"
        assert result.confidence == 0.85
        assert result.provider == "test"
        assert result.processing_time == 1.5
        assert result.cost == 0.001
        assert result.word_confidences == []
        assert result.bounding_boxes == []


@pytest.mark.unit
@pytest.mark.ocr
class TestTesseractOCR:
    
    def test_tesseract_initialization(self, test_config):
        """Test TesseractOCR initialization"""
        config = {"config": "--oem 3 --psm 6", "confidence_threshold": 60}
        provider = TesseractOCR(config)
        
        assert provider.name == "tesseract"
        assert provider.config == config
    
    @pytest.mark.requires_tesseract
    def test_tesseract_extract_text(self, sample_image):
        """Test Tesseract text extraction with real image"""
        config = {"config": "--oem 3 --psm 6", "confidence_threshold": 60}
        provider = TesseractOCR(config)
        
        result = provider.extract_text(sample_image)
        
        assert isinstance(result, OCRResult)
        assert result.provider == "tesseract"
        assert result.processing_time > 0
        assert result.cost == 0.0
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_tesseract_mock_extraction(self, sample_image, mock_tesseract):
        """Test Tesseract with mocked pytesseract"""
        config = {"config": "--oem 3 --psm 6", "confidence_threshold": 60}
        provider = TesseractOCR(config)
        
        # Mock pytesseract responses
        mock_tesseract.image_to_string.return_value = "Sample OCR text"
        mock_tesseract.image_to_data.return_value = {
            'text': ['Sample', 'OCR', 'text'],
            'conf': [85, 90, 80],
            'left': [10, 50, 90],
            'top': [20, 25, 30],
            'width': [40, 30, 35],
            'height': [15, 12, 18]
        }
        mock_tesseract.get_tesseract_version.return_value = "5.3.4"
        
        with patch('pytesseract.image_to_string', mock_tesseract.image_to_string), \
             patch('pytesseract.image_to_data', mock_tesseract.image_to_data), \
             patch('pytesseract.get_tesseract_version', mock_tesseract.get_tesseract_version):
            
            result = provider.extract_text(sample_image)
            
            assert result.text == "Sample OCR text"
            assert result.confidence == pytest.approx(0.85, abs=0.1)  # Average of 85,90,80
            assert result.provider == "tesseract"
            assert len(result.word_confidences) == 3
            assert len(result.bounding_boxes) == 3


@pytest.mark.unit  
@pytest.mark.ocr
class TestGoogleVisionOCR:
    
    def test_google_vision_initialization_no_credentials(self):
        """Test GoogleVisionOCR handles missing credentials gracefully"""
        config = {"confidence_threshold": 80, "features": ["DOCUMENT_TEXT_DETECTION"]}
        
        # Should not crash during initialization
        with patch('google.cloud.vision.ImageAnnotatorClient') as mock_client:
            provider = GoogleVisionOCR(config)
            assert provider.name == "google_vision"
    
    def test_google_vision_mock_extraction(self, sample_image):
        """Test Google Vision with mocked API response"""
        config = {
            "confidence_threshold": 80,
            "features": ["DOCUMENT_TEXT_DETECTION"],
            "cost_per_image": 0.0015
        }
        
        # Mock Google Vision response
        mock_response = MagicMock()
        mock_response.error.message = ""
        mock_response.full_text_annotation.text = "Sample Google Vision text"
        
        # Mock page/block/paragraph/word structure
        mock_word = MagicMock()
        mock_word.confidence = 0.92
        mock_word.symbols = [MagicMock(text='S'), MagicMock(text='a'), MagicMock(text='m')]
        mock_word.bounding_box.vertices = [
            MagicMock(x=10, y=20), MagicMock(x=50, y=20),
            MagicMock(x=50, y=35), MagicMock(x=10, y=35)
        ]
        
        mock_paragraph = MagicMock()
        mock_paragraph.words = [mock_word]
        
        mock_block = MagicMock()
        mock_block.paragraphs = [mock_paragraph]
        
        mock_page = MagicMock()
        mock_page.blocks = [mock_block]
        
        mock_response.full_text_annotation.pages = [mock_page]
        
        with patch('google.cloud.vision.ImageAnnotatorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.annotate_image.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            provider = GoogleVisionOCR(config)
            provider.client = mock_client  # Override initialized client
            
            result = provider.extract_text(sample_image)
            
            assert result.text == "Sample Google Vision text"
            assert result.confidence == 0.92
            assert result.provider == "google_vision"
            assert result.cost == 0.0015
            assert len(result.word_confidences) == 1


@pytest.mark.unit
@pytest.mark.ocr  
class TestGPT4VisionOCR:
    
    def test_gpt4_vision_initialization_no_api_key(self):
        """Test GPT4VisionOCR handles missing API key gracefully"""
        config = {"model": "gpt-4o", "confidence_threshold": 85}
        
        with patch.dict('os.environ', {}, clear=True):
            with patch('openai.OpenAI'):
                provider = GPT4VisionOCR(config)
                assert provider.name == "gpt4_vision"
    
    def test_gpt4_vision_mock_extraction(self, sample_image):
        """Test GPT-4 Vision with mocked API response"""
        config = {
            "model": "gpt-4o",
            "confidence_threshold": 85,
            "cost_per_image": 0.01,
            "system_prompt": "Transcribe exactly"
        }
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sample GPT-4 Vision transcription"
        mock_response.usage.total_tokens = 150
        
        with patch('openai.OpenAI') as mock_openai_class, \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client
            
            provider = GPT4VisionOCR(config)
            provider.client = mock_client  # Override initialized client
            
            result = provider.extract_text(sample_image)
            
            assert result.text == "Sample GPT-4 Vision transcription"
            assert result.confidence == 0.9  # High confidence (no [unclear] markers)
            assert result.provider == "gpt4_vision"
            assert result.cost == 0.01
            assert result.metadata['tokens_used'] == 150
    
    def test_gpt4_vision_unclear_text_confidence(self, sample_image):
        """Test confidence calculation with unclear markers"""
        config = {"model": "gpt-4o", "cost_per_image": 0.01}
        
        # Response with unclear markers
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sample [unclear] text with [unclear] markers"
        mock_response.usage.total_tokens = 100
        
        with patch('openai.OpenAI') as mock_openai_class, \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client
            
            provider = GPT4VisionOCR(config)
            provider.client = mock_client
            
            result = provider.extract_text(sample_image)
            
            # 2 unclear out of 6 words = lower confidence
            assert result.confidence < 0.9
            assert result.metadata['unclear_markers'] == 2


@pytest.mark.unit
@pytest.mark.ocr
class TestHybridOCR:
    
    def test_hybrid_initialization(self, test_config):
        """Test HybridOCR initialization"""
        config = {
            "provider_priority": ["tesseract", "google_vision"],
            "confidence_thresholds": {"tesseract": 75},
            "quality_mode": "balanced"
        }
        
        with patch('src.utils.ocr_providers.config') as mock_config:
            mock_config.get.return_value = {
                "providers": {
                    "tesseract": {"config": "--oem 3"},
                    "google_vision": {"confidence_threshold": 80}
                }
            }
            
            provider = HybridOCR(config)
            assert provider.name == "hybrid"
            assert "tesseract" in provider.providers
    
    def test_hybrid_provider_priority_modes(self):
        """Test provider priority based on quality mode"""
        config = {
            "provider_priority": ["qwen", "tesseract", "google_vision", "gpt4_vision"],
            "quality_mode": "premium"
        }
        
        with patch('src.utils.ocr_providers.config'):
            provider = HybridOCR(config)
            
            # Premium mode should prioritize quality
            priority = provider._get_provider_priority("premium", 0.0, 5.0)
            assert priority[0] == "qwen"  # Best handwriting recognition first
            
            # Fast mode should prioritize speed
            priority = provider._get_provider_priority("fast", 0.0, 5.0)
            assert priority[0] == "qwen"  # Fastest local model first
            
            # Over budget should only use free providers
            priority = provider._get_provider_priority("balanced", 6.0, 5.0)
            assert priority == ["qwen", "tesseract"]


@pytest.mark.unit
@pytest.mark.ocr
class TestOCRFactory:
    
    def test_create_ocr_provider_tesseract(self):
        """Test OCR provider factory for Tesseract"""
        with patch('src.utils.ocr_providers.config') as mock_config:
            mock_config.get.return_value = {
                "providers": {
                    "tesseract": {"config": "--oem 3 --psm 6"}
                }
            }
            
            provider = create_ocr_provider("tesseract")
            assert isinstance(provider, TesseractOCR)
    
    def test_create_ocr_provider_unknown(self):
        """Test OCR provider factory with unknown provider"""
        with patch('src.utils.ocr_providers.config') as mock_config:
            mock_config.get.return_value = {"providers": {}}
            
            with pytest.raises(ValueError, match="Unknown OCR provider"):
                create_ocr_provider("nonexistent")


@pytest.mark.integration
@pytest.mark.ocr
class TestOCRIntegration:
    
    def test_end_to_end_ocr_pipeline(self, test_db, sample_image):
        """Test complete OCR pipeline with database integration"""
        config = {
            "provider_priority": ["tesseract"],
            "quality_mode": "fast"
        }
        
        with patch('src.utils.ocr_providers.config') as mock_config:
            mock_config.get.return_value = {
                "providers": {
                    "tesseract": {"config": "--oem 3 --psm 6", "confidence_threshold": 60}
                }
            }
            
            # Mock tesseract for consistent results
            with patch('pytesseract.image_to_string', return_value="Integration test text"), \
                 patch('pytesseract.image_to_data', return_value={'conf': [80], 'text': ['test']}):
                
                provider = HybridOCR(config)
                result = provider.extract_text(sample_image)
                
                # Verify result
                assert result.text == "Integration test text"
                assert result.provider == "tesseract"
                
                # Test database integration
                success = test_db.insert_note(
                    note_id="integration_test",
                    source_file=str(sample_image),
                    raw_text=result.text,
                    clean_text=result.text,
                    ocr_provider=result.provider,
                    ocr_confidence=result.confidence,
                    processing_cost=result.cost
                )
                
                assert success
                
                # Verify data was stored
                stored_note = test_db.get_note("integration_test")
                assert stored_note is not None
                assert stored_note["ocr_provider"] == "tesseract"