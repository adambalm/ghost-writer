"""
Simplified tests for SupernoteService focused on high coverage
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.services.supernote_service import SupernoteService, supernote_service


class TestSupernotServiceDirect:
    """Direct testing of SupernoteService methods"""
    
    @pytest.fixture
    def service(self):
        """Create service instance with mocked dependencies"""
        service = SupernoteService.__new__(SupernoteService)
        service.ocr_provider = Mock()
        return service
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_note_file(self, temp_output_dir):
        """Create a temporary .note file for testing"""
        note_file = temp_output_dir / "test.note"
        note_file.write_bytes(b"\x00\x01\x02\x03")
        return note_file
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_success(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test successful note file processing"""
        # Setup mocks
        mock_image_path = temp_output_dir / "page_1.png"
        mock_image_path.write_text("dummy image")
        mock_convert.return_value = [mock_image_path]
        
        mock_ocr_result = Mock()
        mock_ocr_result.text = "Sample extracted text"
        mock_ocr_result.confidence = 0.95
        mock_ocr_result.provider = "test_ocr"
        service.ocr_provider.extract_text.return_value = mock_ocr_result
        
        # Test processing
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        # Verify results
        assert result["success"] is True
        assert "note_path" in result
        assert "extracted_images" in result
        assert "ocr_results" in result
        assert len(result["ocr_results"]) == 1
        assert result["ocr_results"][0]["text"] == "Sample extracted text"
        assert result["ocr_results"][0]["confidence"] == 0.95
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_no_images(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test handling when no images are extracted"""
        mock_convert.return_value = []
        
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        assert result["success"] is False
        assert result["error"] == "No images extracted"
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_empty_ocr_text(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test handling when OCR returns empty text"""
        mock_image_path = temp_output_dir / "page_1.png"
        mock_image_path.write_text("dummy image")
        mock_convert.return_value = [mock_image_path]
        
        mock_ocr_result = Mock()
        mock_ocr_result.text = "   "  # Only whitespace
        service.ocr_provider.extract_text.return_value = mock_ocr_result
        
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        assert result["success"] is True
        assert len(result["ocr_results"]) == 0
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_file_exception(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test exception handling in note processing"""
        mock_convert.side_effect = Exception("Processing failed")
        
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        assert result["success"] is False
        assert "Processing failed" in result["error"]
    
    @patch('src.services.supernote_service.convert_note_to_images')
    def test_process_note_multiple_images(self, mock_convert, service, temp_note_file, temp_output_dir):
        """Test processing multiple images"""
        mock_image_paths = [
            temp_output_dir / "page_1.png",
            temp_output_dir / "page_2.png"
        ]
        for path in mock_image_paths:
            path.write_text("dummy image")
        mock_convert.return_value = mock_image_paths
        
        ocr_results = [
            Mock(text="Page 1 text", confidence=0.9, provider="test_ocr"),
            Mock(text="Page 2 text", confidence=0.8, provider="test_ocr")
        ]
        service.ocr_provider.extract_text.side_effect = ocr_results
        
        result = service.process_note_file(temp_note_file, temp_output_dir)
        
        assert result["success"] is True
        assert len(result["extracted_images"]) == 2
        assert len(result["ocr_results"]) == 2
        assert result["ocr_results"][0]["text"] == "Page 1 text"
        assert result["ocr_results"][1]["text"] == "Page 2 text"
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_success(self, mock_create_client, service):
        """Test successful Supernote authentication"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        result = service.authenticate_supernote("1234567890", "password123")
        
        assert result is True
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_failure(self, mock_create_client, service):
        """Test failed Supernote authentication"""
        mock_create_client.return_value = None
        
        result = service.authenticate_supernote("1234567890", "wrongpass")
        
        assert result is False
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_authenticate_supernote_exception(self, mock_create_client, service):
        """Test exception handling during authentication"""
        mock_create_client.side_effect = Exception("Network error")
        
        result = service.authenticate_supernote("1234567890", "password123")
        
        assert result is False
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_success(self, mock_create_client, service):
        """Test successful cloud file listing"""
        mock_client = Mock()
        mock_files = [Mock(name="file1.note"), Mock(name="file2.note")]
        mock_client.list_files.return_value = mock_files
        mock_create_client.return_value = mock_client
        
        result = service.list_cloud_files()
        
        assert len(result) == 2
        mock_client.list_files.assert_called_once()
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_no_client(self, mock_create_client, service):
        """Test cloud file listing with no client"""
        mock_create_client.return_value = None
        
        result = service.list_cloud_files()
        
        assert result == []
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_list_cloud_files_exception(self, mock_create_client, service):
        """Test exception handling during file listing"""
        mock_client = Mock()
        mock_client.list_files.side_effect = Exception("API error")
        mock_create_client.return_value = mock_client
        
        result = service.list_cloud_files()
        
        assert result == []
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_download_cloud_file_success(self, mock_create_client, service, temp_output_dir):
        """Test successful cloud file download"""
        mock_client = Mock()
        mock_client.download_file.return_value = True
        mock_create_client.return_value = mock_client
        
        download_path = temp_output_dir / "downloaded.note"
        
        result = service.download_cloud_file("file123", download_path)
        
        assert result is True
        mock_client.download_file.assert_called_once_with("file123", download_path)
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_download_cloud_file_no_client(self, mock_create_client, service, temp_output_dir):
        """Test cloud file download with no client"""
        mock_create_client.return_value = None
        
        download_path = temp_output_dir / "downloaded.note"
        
        result = service.download_cloud_file("file123", download_path)
        
        assert result is False
    
    @patch('src.services.supernote_service.create_supernote_client')
    def test_download_cloud_file_exception(self, mock_create_client, service, temp_output_dir):
        """Test exception handling during file download"""
        mock_client = Mock()
        mock_client.download_file.side_effect = Exception("Download failed")
        mock_create_client.return_value = mock_client
        
        download_path = temp_output_dir / "downloaded.note"
        
        result = service.download_cloud_file("file123", download_path)
        
        assert result is False


class TestGlobalServiceInstance:
    """Test the global service instance"""
    
    def test_global_service_exists(self):
        """Test that global service instance is available"""
        assert supernote_service is not None
        assert hasattr(supernote_service, 'process_note_file')
        assert hasattr(supernote_service, 'authenticate_supernote')
    
    def test_global_service_has_ocr_provider(self):
        """Test that global service has OCR provider"""
        assert hasattr(supernote_service, 'ocr_provider')
        assert supernote_service.ocr_provider is not None


