"""
Tests for SupernoteService unified service layer
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.services.supernote_service import SupernoteService


class TestSupernoteService:
    """Test unified SupernoteService"""
    
    @pytest.fixture
    def service(self, test_config):
        """Create service instance for testing"""
        with patch('src.services.supernote_service.config', test_config):
            with patch.object(SupernoteService, '__init__', lambda self: None):
                service = SupernoteService()
                service.ocr_provider = Mock()
                return service
    
    @pytest.fixture
    def temp_note_file(self, temp_dir):
        """Create a temporary .note file for testing"""
        note_file = temp_dir / "test.note"
        note_file.write_bytes(b"\x00\x01\x02\x03")  # Minimal binary content
        return note_file
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_service_initialization(self, service):
        """Test service initializes with OCR provider"""
        assert service.ocr_provider is not None
        assert hasattr(service, 'ocr_provider')
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_success(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test successful note file processing"""
        # Mock image extraction
        mock_image_path = temp_output_dir / "page_1.png"
        mock_image_path.write_text("dummy image")
        mock_convert.return_value = [mock_image_path]
        
        # Mock OCR result
        mock_ocr_result = Mock()
        mock_ocr_result.text = "Sample extracted text"
        mock_ocr_result.confidence = 0.95
        mock_ocr_result.provider = "test_ocr"
        service.ocr_provider.extract_text = Mock(return_value=mock_ocr_result)
        
        # Process the file
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify success
        assert result["success"] is True
        assert "note_path" in result
        assert "extracted_images" in result
        assert "ocr_results" in result
        assert "processed_at" in result
        
        # Verify OCR results
        assert len(result["ocr_results"]) == 1
        assert result["ocr_results"][0]["text"] == "Sample extracted text"
        assert result["ocr_results"][0]["confidence"] == 0.95
        assert result["ocr_results"][0]["provider"] == "test_ocr"
        
        # Verify convert_note_to_images was called correctly
        mock_convert.assert_called_once()
        assert mock_convert.call_args[0][0] == temp_note_file
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_no_images(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test handling when no images are extracted"""
        # Mock no images extracted
        mock_convert.return_value = []
        
        # Process the file
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify failure
        assert result["success"] is False
        assert result["error"] == "No images extracted"
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_no_ocr_text(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test handling when OCR returns no text"""
        # Mock image extraction
        mock_image_path = temp_output_dir / "page_1.png"
        mock_image_path.write_text("dummy image")
        mock_convert.return_value = [mock_image_path]
        
        # Mock OCR result with no text
        mock_ocr_result = Mock()
        mock_ocr_result.text = "   "  # Only whitespace
        mock_ocr_result.confidence = 0.95
        mock_ocr_result.provider = "test_ocr"
        service.ocr_provider.extract_text = Mock(return_value=mock_ocr_result)
        
        # Process the file
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify success but no OCR results
        assert result["success"] is True
        assert len(result["ocr_results"]) == 0
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_exception(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test error handling in note processing"""
        # Mock exception during processing
        mock_convert.side_effect = Exception("Processing failed")
        
        # Process the file
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify error handling
        assert result["success"] is False
        assert "Processing failed" in result["error"]
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_success(self, mock_create_client, service):
        """Test successful Supernote authentication"""
        # Mock successful client creation
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Test authentication
        result = service.authenticate_supernote("1234567890", "password123")
        
        # Verify success
        assert result is True
        mock_create_client.assert_called_once()
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_failure(self, mock_create_client, service):
        """Test failed Supernote authentication"""
        # Mock failed client creation
        mock_create_client.return_value = None
        
        # Test authentication
        result = service.authenticate_supernote("1234567890", "wrongpassword")
        
        # Verify failure
        assert result is False
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_exception(self, mock_create_client, service):
        """Test exception handling during authentication"""
        # Mock exception during authentication
        mock_create_client.side_effect = Exception("Network error")
        
        # Test authentication
        result = service.authenticate_supernote("1234567890", "password123")
        
        # Verify failure
        assert result is False
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_success(self, mock_create_client, service):
        """Test successful cloud file listing"""
        # Mock successful client and files
        mock_client = Mock()
        mock_files = [Mock(name="file1.note"), Mock(name="file2.note")]
        mock_client.list_files.return_value = mock_files
        mock_create_client.return_value = mock_client
        
        # Test file listing
        result = service.list_cloud_files()
        
        # Verify success
        assert len(result) == 2
        mock_client.list_files.assert_called_once()
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_no_client(self, mock_create_client, service):
        """Test cloud file listing with no client"""
        # Mock no client
        mock_create_client.return_value = None
        
        # Test file listing
        result = service.list_cloud_files()
        
        # Verify empty result
        assert result == []
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_exception(self, mock_create_client, service):
        """Test exception handling during file listing"""
        # Mock exception during file listing
        mock_client = Mock()
        mock_client.list_files.side_effect = Exception("API error")
        mock_create_client.return_value = mock_client
        
        # Test file listing
        result = service.list_cloud_files()
        
        # Verify empty result on error
        assert result == []
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_download_cloud_file_success(self, mock_create_client, service, temp_output_dir):
        """Test successful cloud file download"""
        # Mock successful client and download
        mock_client = Mock()
        mock_client.download_file.return_value = True
        mock_create_client.return_value = mock_client
        
        download_path = temp_output_dir / "downloaded.note"
        
        # Test file download
        result = service.download_cloud_file("file123", download_path)
        
        # Verify success
        assert result is True
        mock_client.download_file.assert_called_once_with("file123", download_path)
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_download_cloud_file_no_client(self, mock_create_client, service, temp_output_dir):
        """Test cloud file download with no client"""
        # Mock no client
        mock_create_client.return_value = None
        
        download_path = temp_output_dir / "downloaded.note"
        
        # Test file download
        result = service.download_cloud_file("file123", download_path)
        
        # Verify failure
        assert result is False
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_multiple_images(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test processing note file with multiple images"""
        # Mock multiple image extraction
        mock_image_paths = [
            temp_output_dir / "page_1.png",
            temp_output_dir / "page_2.png"
        ]
        for path in mock_image_paths:
            path.write_text("dummy image")
        mock_convert.return_value = mock_image_paths
        
        # Mock OCR results for each image
        ocr_results = [
            Mock(text="Page 1 text", confidence=0.9, provider="test_ocr"),
            Mock(text="Page 2 text", confidence=0.8, provider="test_ocr")
        ]
        service.ocr_provider.extract_text = Mock(side_effect=ocr_results)
        
        # Process the file
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify success with multiple results
        assert result["success"] is True
        assert len(result["extracted_images"]) == 2
        assert len(result["ocr_results"]) == 2
        assert result["ocr_results"][0]["text"] == "Page 1 text"
        assert result["ocr_results"][1]["text"] == "Page 2 text"

class TestSupernoteServiceGlobalInstance:
    """Test the global service instance"""
    
    def test_global_service_exists(self):
        """Test that global service instance is available"""
        from src.services.supernote_service import supernote_service
        assert supernote_service is not None
        assert hasattr(supernote_service, 'process_note_file')
        assert hasattr(supernote_service, 'authenticate_supernote')