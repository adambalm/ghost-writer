"""
Tests for Supernote Cloud API integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone

from src.utils.supernote_api import (
    SupernoteCredentials, SupernoteFile, SupernoteCloudAPI, create_supernote_client
)


class TestSuperNoteCredentials:
    """Test SupernoteCredentials dataclass"""

    def test_credentials_creation(self):
        """Test creating credentials with all fields"""
        credentials = SupernoteCredentials(
            email="test@example.com",
            password="password123",
            device_id="device123",
            access_token="token123",
            refresh_token="refresh123"
        )
        
        assert credentials.email == "test@example.com"
        assert credentials.password == "password123"
        assert credentials.device_id == "device123"
        assert credentials.access_token == "token123"
        assert credentials.refresh_token == "refresh123"

    def test_credentials_partial_creation(self):
        """Test creating credentials with minimal fields"""
        credentials = SupernoteCredentials(
            email="test@example.com",
            password="password123"
        )
        
        assert credentials.email == "test@example.com"
        assert credentials.password == "password123"
        assert credentials.device_id is None
        assert credentials.access_token is None
        assert credentials.refresh_token is None


class TestSuperNoteFile:
    """Test SupernoteFile dataclass"""

    def test_supernote_file_creation(self):
        """Test creating SupernoteFile with all fields"""
        file_time = datetime.now(timezone.utc)
        supernote_file = SupernoteFile(
            file_id="file123",
            name="test.note",
            path="/path/to/test.note",
            size=1024,
            modified_time=file_time,
            file_type="note",
            checksum="abc123",
            download_url="https://example.com/download"
        )
        
        assert supernote_file.file_id == "file123"
        assert supernote_file.name == "test.note"
        assert supernote_file.path == "/path/to/test.note"
        assert supernote_file.size == 1024
        assert supernote_file.modified_time == file_time
        assert supernote_file.file_type == "note"
        assert supernote_file.checksum == "abc123"
        assert supernote_file.download_url == "https://example.com/download"


class TestSuperNoteCloudAPI:
    """Test SupernoteCloudAPI class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.credentials = SupernoteCredentials(
            email="test@example.com",
            password="password123"
        )

    def test_api_initialization(self):
        """Test API initialization"""
        api = SupernoteCloudAPI(self.credentials)
        
        assert api.credentials == self.credentials
        assert api.authenticated is False
        assert api.last_error is None
        assert api.session is not None

    def test_generate_device_id(self):
        """Test device ID generation"""
        api = SupernoteCloudAPI(self.credentials)
        device_id = api._generate_device_id()
        
        assert isinstance(device_id, str)
        assert len(device_id) > 0

    def test_hash_password(self):
        """Test password hashing"""
        api = SupernoteCloudAPI(self.credentials)
        hashed = api._hash_password("test_password")
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != "test_password"

    @patch('requests.Session.post')
    def test_get_random_code_success(self, mock_post):
        """Test successful random code retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "123456"}
        mock_post.return_value = mock_response
        
        api = SupernoteCloudAPI(self.credentials)
        code = api._get_random_code()
        
        assert code == "123456"

    @patch('requests.Session.post')
    def test_get_random_code_failure(self, mock_post):
        """Test failed random code retrieval"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        api = SupernoteCloudAPI(self.credentials)
        code = api._get_random_code()
        
        assert code is None

    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication"""
        # Mock random code call
        mock_code_response = Mock()
        mock_code_response.status_code = 200
        mock_code_response.json.return_value = {"code": "123456"}
        
        # Mock login call  
        mock_login_response = Mock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "success": True,
            "token": "access_token_123"
        }
        
        mock_post.side_effect = [mock_code_response, mock_login_response]
        
        api = SupernoteCloudAPI(self.credentials)
        result = api.authenticate()
        
        assert result is True
        assert api.authenticated is True
        assert api.credentials.access_token == "access_token_123"

    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post):
        """Test failed authentication"""
        # Mock random code call
        mock_code_response = Mock()
        mock_code_response.status_code = 200
        mock_code_response.json.return_value = {"code": "123456"}
        
        # Mock failed login call
        mock_login_response = Mock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "success": False,
            "errorMsg": "Invalid credentials",
            "errorCode": "AUTH_FAILED"
        }
        
        mock_post.side_effect = [mock_code_response, mock_login_response]
        
        api = SupernoteCloudAPI(self.credentials)
        result = api.authenticate()
        
        assert result is False
        assert api.authenticated is False
        assert api.last_error is not None

    @patch('requests.Session.post')
    def test_authenticate_no_random_code(self, mock_post):
        """Test authentication when random code fails"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        api = SupernoteCloudAPI(self.credentials)
        result = api.authenticate()
        
        assert result is False
        assert api.authenticated is False

    @patch('requests.Session.get')
    def test_list_files_success(self, mock_get):
        """Test successful file listing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "test1.note", 
                    "path": "/test1.note",
                    "size": 1024,
                    "modifiedTime": "2023-01-01T00:00:00Z",
                    "type": "note",
                    "checksum": "abc123"
                },
                {
                    "id": "file2",
                    "name": "test2.pdf",
                    "path": "/test2.pdf", 
                    "size": 2048,
                    "modifiedTime": "2023-01-02T00:00:00Z",
                    "type": "pdf",
                    "checksum": "def456"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        api = SupernoteCloudAPI(self.credentials)
        api.authenticated = True  # Simulate authenticated state
        
        files = api.list_files()
        
        assert len(files) == 2
        assert files[0].name == "test1.note"
        assert files[1].name == "test2.pdf"

    @patch('requests.Session.get')
    def test_list_files_not_authenticated(self, mock_get):
        """Test file listing when not authenticated"""
        api = SupernoteCloudAPI(self.credentials)
        api.authenticated = False
        
        files = api.list_files()
        
        assert files == []
        mock_get.assert_not_called()

    @patch('requests.Session.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download"""
        # Mock download URL request
        mock_url_response = Mock()
        mock_url_response.status_code = 200
        mock_url_response.json.return_value = {"download_url": "https://example.com/download"}
        
        # Mock file download
        mock_file_response = Mock()
        mock_file_response.status_code = 200
        mock_file_response.content = b"file content"
        
        mock_get.side_effect = [mock_url_response, mock_file_response]
        
        test_file = SupernoteFile(
            file_id="file123",
            name="test.note",
            path="/test.note",
            size=1024,
            modified_time=datetime.now(timezone.utc),
            file_type="note",
            checksum="abc123"
        )
        
        api = SupernoteCloudAPI(self.credentials)
        api.authenticated = True
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = api.download_file(test_file, Path("/tmp/test.note"))
            
            assert result is True
            mock_file.write.assert_called_once_with(b"file content")

    def test_download_file_not_authenticated(self):
        """Test file download when not authenticated"""
        test_file = SupernoteFile(
            file_id="file123",
            name="test.note", 
            path="/test.note",
            size=1024,
            modified_time=datetime.now(timezone.utc),
            file_type="note",
            checksum="abc123"
        )
        
        api = SupernoteCloudAPI(self.credentials)
        api.authenticated = False
        
        result = api.download_file(test_file, Path("/tmp/test.note"))
        
        assert result is False


class TestCreateSuperNoteClient:
    """Test the create_supernote_client factory function"""

    @patch.dict('os.environ', {
        'SUPERNOTE_EMAIL': 'test@example.com',
        'SUPERNOTE_PASSWORD': 'password123'
    })
    def test_create_client_from_environment(self):
        """Test creating client from environment variables"""
        config = {}
        
        client = create_supernote_client(config)
        
        assert client is not None
        assert isinstance(client, SupernoteCloudAPI)
        assert client.credentials.email == "test@example.com"
        assert client.credentials.password == "password123"

    def test_create_client_from_config(self):
        """Test creating client from config"""
        config = {
            "supernote": {
                "email": "config@example.com",
                "password": "configpass123"
            }
        }
        
        client = create_supernote_client(config)
        
        assert client is not None
        assert client.credentials.email == "config@example.com"
        assert client.credentials.password == "configpass123"

    def test_create_client_from_parameters(self):
        """Test creating client from direct parameters"""
        config = {}
        
        client = create_supernote_client(config, email="param@example.com", password="parampass123")
        
        assert client is not None
        assert client.credentials.email == "param@example.com"
        assert client.credentials.password == "parampass123"

    def test_create_client_no_credentials(self):
        """Test creating client without any credentials"""
        config = {}
        
        with patch.dict('os.environ', {}, clear=True):
            client = create_supernote_client(config)
            
            assert client is None

    def test_create_client_parameter_override(self):
        """Test that parameters override config and environment"""
        config = {
            "supernote": {
                "email": "config@example.com",
                "password": "configpass123"
            }
        }
        
        with patch.dict('os.environ', {
            'SUPERNOTE_EMAIL': 'env@example.com',
            'SUPERNOTE_PASSWORD': 'envpass123'
        }):
            client = create_supernote_client(config, email="param@example.com", password="parampass123")
            
            assert client is not None
            assert client.credentials.email == "param@example.com"
            assert client.credentials.password == "parampass123"


class TestSuperNoteAPIEdgeCases:
    """Test edge cases and error conditions"""

    def test_api_with_invalid_credentials(self):
        """Test API behavior with invalid credentials"""
        credentials = SupernoteCredentials(email="", password="")
        api = SupernoteCloudAPI(credentials)
        
        assert api.credentials.email == ""
        assert api.credentials.password == ""

    @patch('requests.Session.post')
    def test_authenticate_network_error(self, mock_post):
        """Test authentication with network error"""
        mock_post.side_effect = Exception("Network error")
        
        credentials = SupernoteCredentials(email="test@example.com", password="password123")
        api = SupernoteCloudAPI(credentials)
        
        result = api.authenticate()
        
        assert result is False
        assert api.authenticated is False

    @patch('requests.Session.get')
    def test_list_files_network_error(self, mock_get):
        """Test file listing with network error"""
        mock_get.side_effect = Exception("Network error")
        
        credentials = SupernoteCredentials(email="test@example.com", password="password123")
        api = SupernoteCloudAPI(credentials)
        api.authenticated = True
        
        files = api.list_files()
        
        assert files == []

    @patch('requests.Session.get')
    def test_download_file_network_error(self, mock_get):
        """Test file download with network error"""
        mock_get.side_effect = Exception("Network error")
        
        test_file = SupernoteFile(
            file_id="file123",
            name="test.note",
            path="/test.note", 
            size=1024,
            modified_time=datetime.now(timezone.utc),
            file_type="note",
            checksum="abc123"
        )
        
        credentials = SupernoteCredentials(email="test@example.com", password="password123")
        api = SupernoteCloudAPI(credentials)
        api.authenticated = True
        
        result = api.download_file(test_file, Path("/tmp/test.note"))
        
        assert result is False

    def test_password_hashing_consistency(self):
        """Test that password hashing is consistent"""
        credentials = SupernoteCredentials(email="test@example.com", password="password123")
        api = SupernoteCloudAPI(credentials)
        
        hash1 = api._hash_password("test_password")
        hash2 = api._hash_password("test_password")
        
        assert hash1 == hash2

    def test_device_id_generation_format(self):
        """Test device ID generation format"""
        credentials = SupernoteCredentials(email="test@example.com", password="password123")
        api = SupernoteCloudAPI(credentials)
        
        device_id = api._generate_device_id()
        
        # Should be a hex string
        assert all(c in '0123456789abcdef' for c in device_id.lower())
        assert len(device_id) > 10  # Should be reasonably long