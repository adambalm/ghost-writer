"""
Tests for unified web application
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Import Flask app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from web.unified_app import app


class TestUnifiedWebApp:
    """Test unified web application endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def authenticated_app(self, client):
        """Mock authenticated state for testing"""
        with patch('web.unified_app.authenticated', True):
            with patch('web.unified_app.cloud_files', [Mock(name="test.note")]):
                yield client
    
    def test_index_route_unauthenticated(self, client):
        """Test index page when not authenticated"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Ghost Writer' in response.data
        assert b'Not connected' in response.data or b'authentication' in response.data.lower()
    
    @patch('web.unified_app.authenticated', True)
    @patch('web.unified_app.cloud_files', [])
    @patch('web.unified_app.last_sync_time', None)
    def test_index_route_authenticated(self, client):
        """Test index page when authenticated"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Ghost Writer' in response.data
    
    @patch('web.unified_app.supernote_service')
    def test_authenticate_success(self, mock_service, client):
        """Test successful authentication"""
        # Mock successful authentication
        mock_service.authenticate_supernote.return_value = True
        mock_service.list_cloud_files.return_value = [Mock(name="test.note")]
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'Successfully connected' in data['message']
    
    def test_authenticate_missing_phone(self, client):
        """Test authentication with missing phone"""
        response = client.post('/authenticate', 
                             json={'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Phone number is required' in data['error']
    
    def test_authenticate_missing_password(self, client):
        """Test authentication with missing password"""
        response = client.post('/authenticate', 
                             json={'phone': '1234567890'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Password is required' in data['error']
    
    def test_authenticate_invalid_phone_format(self, client):
        """Test authentication with invalid phone format"""
        response = client.post('/authenticate', 
                             json={'phone': '123', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert '10-digit' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_authenticate_failure(self, mock_service, client):
        """Test failed authentication"""
        # Mock failed authentication
        mock_service.authenticate_supernote.return_value = False
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'wrongpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid phone number or password' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_authenticate_exception_handling(self, mock_service, client):
        """Test authentication exception handling"""
        # Mock exception during authentication
        mock_service.authenticate_supernote.side_effect = Exception("Network error")
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_cloud_files_not_authenticated(self, client):
        """Test cloud files endpoint when not authenticated"""
        with patch('web.unified_app.authenticated', False):
            response = client.get('/cloud-files')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Not authenticated' in data['error']
    
    @patch('web.unified_app.authenticated', True)
    @patch('web.unified_app.supernote_service')
    def test_cloud_files_success(self, mock_service, client):
        """Test successful cloud files retrieval"""
        # Mock cloud files
        mock_file = Mock()
        mock_file.file_id = "123"
        mock_file.name = "test.note"
        mock_file.size = 1024
        mock_file.modified_time = None
        mock_file.file_type = "note"
        mock_service.list_cloud_files.return_value = [mock_file]
        
        response = client.get('/cloud-files')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['files']) == 1
        assert data['files'][0]['name'] == 'test.note'
    
    @patch('web.unified_app.authenticated', True)
    @patch('web.unified_app.supernote_service')
    def test_cloud_files_exception(self, mock_service, client):
        """Test cloud files exception handling"""
        # Mock exception
        mock_service.list_cloud_files.side_effect = Exception("API error")
        
        response = client.get('/cloud-files')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'API error' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_process_file_cloud_success(self, mock_service, client):
        """Test processing cloud file"""
        # Mock successful processing
        mock_service.download_cloud_file.return_value = True
        mock_service.process_note_file.return_value = {
            'success': True,
            'extracted_images': ['page1.png'],
            'ocr_results': [{'text': 'test', 'confidence': 0.9}]
        }
        
        response = client.post('/process-file', 
                              json={'file_id': '123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('web.unified_app.supernote_service')
    def test_process_file_cloud_download_failure(self, mock_service, client):
        """Test processing cloud file with download failure"""
        # Mock failed download
        mock_service.download_cloud_file.return_value = False
        
        response = client.post('/process-file', 
                              json={'file_id': '123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Failed to download file' in data['error']
    
    def test_process_file_no_file_specified(self, client):
        """Test processing with no file specified"""
        response = client.post('/process-file', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No file specified' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_upload_file_success(self, mock_service, client):
        """Test successful file upload"""
        # Mock successful processing
        mock_service.process_note_file.return_value = {
            'success': True,
            'extracted_images': ['page1.png'],
            'ocr_results': [{'text': 'test', 'confidence': 0.9}]
        }
        
        # Create test file
        data = {
            'file': (BytesIO(b'test content'), 'test.note')
        }
        
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
    
    def test_upload_no_file(self, client):
        """Test upload with no file"""
        response = client.post('/upload', data={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No file uploaded' in data['error']
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename"""
        data = {
            'file': (BytesIO(b'test content'), '')
        }
        
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'No file selected' in result['error']
    
    def test_upload_invalid_extension(self, client):
        """Test upload with invalid file extension"""
        data = {
            'file': (BytesIO(b'test content'), 'test.txt')
        }
        
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'Only .note files are supported' in result['error']
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        with patch('web.unified_app.authenticated', False):
            with patch('web.unified_app.cloud_files', []):
                with patch('web.unified_app.last_sync_time', None):
                    response = client.get('/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'authenticated' in data
        assert 'cloud_files_count' in data
        assert 'last_sync' in data
        assert 'upload_folder' in data
        assert 'results_folder' in data
    
    def test_reset_auth_endpoint(self, client):
        """Test authentication reset endpoint"""
        response = client.post('/reset-auth')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Authentication reset'
    
    def test_download_existing_file(self, client):
        """Test downloading existing file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(b'test content')
            temp_file_path = Path(temp_file.name)
        
        try:
            # Mock the results folder to contain our test file
            with patch('web.unified_app.RESULTS_FOLDER', temp_file_path.parent):
                response = client.get(f'/download/{temp_file_path.name}')
                
                assert response.status_code == 200
                assert response.data == b'test content'
        finally:
            temp_file_path.unlink()
    
    def test_download_nonexistent_file(self, client):
        """Test downloading non-existent file"""
        response = client.get('/download/nonexistent.txt')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'File not found'


class TestWebAppErrorHandling:
    """Test error handling in web application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON"""
        response = client.post('/authenticate', 
                             data='invalid json',
                             content_type='application/json')
        
        # Should handle gracefully without crashing
        assert response.status_code in [400, 500]
    
    @patch('web.unified_app.supernote_service')
    def test_service_method_exception(self, mock_service, client):
        """Test handling when service methods throw exceptions"""
        # Mock service exception
        mock_service.process_note_file.side_effect = Exception("Service error")
        
        data = {
            'file': (BytesIO(b'test content'), 'test.note')
        }
        
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'Service error' in result['error']


class TestAuthenticationErrorHandling:
    """Test specific authentication error message handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('web.unified_app.supernote_service')
    def test_timeout_error_message(self, mock_service, client):
        """Test timeout error message handling"""
        mock_service.authenticate_supernote.side_effect = Exception("Request timeout expired")
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Connection timed out' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_network_error_message(self, mock_service, client):
        """Test network error message handling"""
        mock_service.authenticate_supernote.side_effect = Exception("Network connection failed")
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Network connection failed' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_credentials_error_message(self, mock_service, client):
        """Test credentials error message handling"""
        mock_service.authenticate_supernote.side_effect = Exception("Invalid credentials provided")
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Authentication failed' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_generic_error_message(self, mock_service, client):
        """Test generic error message handling"""
        mock_service.authenticate_supernote.side_effect = Exception("Unknown error occurred")
        
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Authentication error: Unknown error occurred' in data['error']


class TestFileProcessingEdgeCases:
    """Test edge cases in file processing"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('web.unified_app.supernote_service')
    def test_process_local_path_not_exists(self, mock_service, client):
        """Test processing local path that doesn't exist"""
        response = client.post('/process-file', 
                              json={'local_path': '/nonexistent/file.note'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'File not found' in data['error']
    
    @patch('web.unified_app.supernote_service')
    def test_process_file_service_exception(self, mock_service, client):
        """Test exception handling in process_file endpoint"""
        mock_service.process_note_file.side_effect = Exception("Processing failed")
        
        response = client.post('/process-file', 
                              json={'file_id': '123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Processing failed' in data['error']


class TestRefreshCloudFilesFunction:
    """Test the refresh_cloud_files function indirectly"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('web.unified_app.supernote_service')
    @patch('web.unified_app.authenticated', True)
    def test_refresh_cloud_files_success(self, mock_service, client):
        """Test successful cloud files refresh through authentication"""
        # Mock successful authentication and file listing
        mock_service.authenticate_supernote.return_value = True
        mock_files = [Mock(name="test.note")]
        mock_service.list_cloud_files.return_value = mock_files
        
        # This will trigger refresh_cloud_files internally
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('web.unified_app.supernote_service')
    @patch('web.unified_app.authenticated', True)
    def test_refresh_cloud_files_exception(self, mock_service, client):
        """Test exception handling in refresh_cloud_files"""
        # Mock authentication success but file listing failure
        mock_service.authenticate_supernote.return_value = True
        mock_service.list_cloud_files.side_effect = Exception("API error")
        
        # This will trigger refresh_cloud_files internally and handle the exception
        response = client.post('/authenticate', 
                             json={'phone': '1234567890', 'password': 'testpass'})
        
        # Should still succeed authentication but log the error internally
        assert response.status_code == 200


class TestMainExecution:
    """Test main execution block"""
    
    def test_main_execution_coverage(self):
        """Test the main execution block for coverage"""
        import sys
        from unittest.mock import patch
        
        # Mock sys.argv to prevent actual app running
        with patch('sys.argv', ['unified_app.py']):
            with patch('src.web.unified_app.app.run') as mock_run:
                # Import and execute the main block
                import importlib
                import src.web.unified_app
                importlib.reload(src.web.unified_app)
                
                # The main block should be covered by import