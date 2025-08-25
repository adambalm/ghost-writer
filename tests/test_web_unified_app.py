"""
Tests for the unified web application
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.web.unified_app import app


class TestUnifiedWebApp:
    """Test the unified web application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_index_route(self, client):
        """Test the main index route"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_status_route(self, client):
        """Test the status endpoint"""
        response = client.get('/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'authenticated' in data
        assert 'cloud_files_count' in data
    
    def test_reset_auth_route(self, client):
        """Test authentication reset"""
        response = client.post('/reset-auth')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_authenticate_missing_phone(self, client):
        """Test authentication with missing phone"""
        response = client.post('/authenticate', 
                              json={'password': 'test123'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Phone number is required' in data['error']
    
    def test_authenticate_missing_password(self, client):
        """Test authentication with missing password"""  
        response = client.post('/authenticate',
                              json={'phone': '1234567890'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Password is required' in data['error']
    
    def test_authenticate_invalid_phone(self, client):
        """Test authentication with invalid phone number"""
        response = client.post('/authenticate',
                              json={'phone': '123', 'password': 'test123'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert '10-digit' in data['error']
    
    @patch('src.web.unified_app.supernote_service')
    def test_authenticate_success(self, mock_service, client):
        """Test successful authentication"""
        mock_service.authenticate_supernote.return_value = True
        mock_service.list_cloud_files.return_value = [Mock(), Mock()]
        
        response = client.post('/authenticate',
                              json={'phone': '1234567890', 'password': 'test123'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'Successfully connected' in data['message']
    
    @patch('src.web.unified_app.supernote_service')
    def test_authenticate_failure(self, mock_service, client):
        """Test failed authentication"""
        mock_service.authenticate_supernote.return_value = False
        
        response = client.post('/authenticate',
                              json={'phone': '1234567890', 'password': 'test123'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid phone number or password' in data['error']
    
    def test_cloud_files_not_authenticated(self, client):
        """Test cloud files without authentication"""
        # Reset auth state first
        client.post('/reset-auth')
        
        response = client.get('/cloud-files')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Not authenticated' in data['error']
    
    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/upload')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'No file uploaded' in data['error']
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename"""
        data = {'file': (open('/dev/null', 'rb'), '')}
        response = client.post('/upload', data=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'No file selected' in data['error']
    
    def test_upload_wrong_extension(self, client):
        """Test upload with wrong file extension"""
        data = {'file': (open('/dev/null', 'rb'), 'test.txt')}
        response = client.post('/upload', data=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Only .note files are supported' in data['error']
    
    def test_download_nonexistent_file(self, client):
        """Test downloading nonexistent file"""
        response = client.get('/download/nonexistent.png')
        assert response.status_code == 404
    
    def test_process_file_no_file_specified(self, client):
        """Test process file with no file specified"""
        response = client.post('/process-file',
                              json={},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'No file specified' in data['error']
    
    def test_process_file_local_path_not_found(self, client):
        """Test process file with nonexistent local path"""
        response = client.post('/process-file',
                              json={'local_path': '/nonexistent/path.note'},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'File not found' in data['error']