"""
Supernote Cloud API Integration

This module provides integration with Supernote's cloud sync service.
Based on the proven implementation at: https://github.com/bwhitman/supernote-cloud-python

Authentication and API endpoints tested with Supernote A6X2 "Nomad" devices.
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class SupernoteCredentials:
    """Supernote account credentials"""
    email: str
    password: str = ""
    access_token: str = ""
    refresh_token: str = ""
    device_id: str = ""


@dataclass
class SupernoteFile:
    """Represents a file in Supernote Cloud"""
    file_id: str
    name: str
    path: str
    size: int
    modified_time: datetime
    file_type: str  # "note", "pdf", "image"
    checksum: str
    download_url: Optional[str] = None


class SupernoteCloudAPI:
    """Client for Supernote Cloud API - Based on proven implementation"""
    
    BASE_URL = "https://cloud.supernote.com/api"
    
    # Actual API endpoints from working implementation
    ENDPOINTS = {
        "random_code": "/official/user/query/random/code",
        "login": "/official/user/account/login/new", 
        "file_list": "/file/list/query",
        "download_url": "/file/download/url",
        "file_url": "/file/url",  # Alternative endpoint found in research
        "upload_apply": "/file/upload/apply",
        "upload_finish": "/file/upload/finish"
    }
    
    def __init__(self, credentials: SupernoteCredentials):
        self.credentials = credentials
        self.session = self._create_session()
        self.authenticated = False
        self.last_error = None
        
        logger.info("SupernoteCloudAPI initialized")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set common headers
        session.headers.update({
            'User-Agent': 'GhostWriter/2.0 (Supernote Integration)',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        return session
    
    def authenticate(self) -> bool:
        """Authenticate with Supernote Cloud using proven method"""
        
        logger.info("Attempting to authenticate with Supernote Cloud...")
        
        if not self.credentials.email or not self.credentials.password:
            logger.error("Email and password required for authentication")
            return False
        
        try:
            # Determine if account is phone number or email
            is_phone = self.credentials.email.isdigit()
            
            # Step 1: Get random code with required parameters
            # For US phone numbers, countryCode should be "1"
            # For other countries, adjust accordingly
            random_params = {
                "countryCode": "1" if is_phone else "",
                "account": self.credentials.email  # Can be phone number or email
            }
            
            logger.debug(f"Getting random code for account: {self.credentials.email}")
            random_response = self.session.post(
                f"{self.BASE_URL}{self.ENDPOINTS['random_code']}",
                json=random_params
            )
            
            if not random_response.ok:
                logger.error(f"Failed to get random code: {random_response.status_code}")
                logger.debug(f"Response: {random_response.text}")
                return False
            
            random_data = random_response.json()
            if not random_data.get("success"):
                logger.error(f"Random code request unsuccessful: {random_data}")
                return False
            
            # Response format: randomCode and timestamp directly in response
            random_code = random_data.get("randomCode")
            timestamp = random_data.get("timestamp")
            
            # Step 2: Encrypt password using working method
            # Based on successful authentication: MD5(password) + randomCode → SHA256
            md5_password = hashlib.md5(self.credentials.password.encode()).hexdigest()
            combined = f"{md5_password}{random_code}"
            final_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            # Step 3: Login request with all required fields
            login_data = {
                "countryCode": 1,
                "account": self.credentials.email,  # Phone number or email
                "password": final_hash,
                "browser": "Chrome107",
                "equipment": "1",
                "loginMethod": "1",
                "timestamp": timestamp,
                "language": "en"
            }
            
            login_response = self.session.post(
                f"{self.BASE_URL}{self.ENDPOINTS['login']}",
                json=login_data
            )
            
            if not login_response.ok:
                logger.error(f"Login request failed: {login_response.status_code}")
                logger.debug(f"Login response: {login_response.text}")
                return False
            
            login_result = login_response.json()
            
            if not login_result.get("success"):
                error_msg = login_result.get('errorMsg', 'Unknown error')
                error_code = login_result.get('errorCode', 'No code')
                logger.error(f"Login unsuccessful: {error_msg} (Code: {error_code})")
                # Store the error for retrieval
                self.last_error = {'message': error_msg, 'code': error_code, 'full_response': login_result}
                return False
            
            # Store access token (token is directly in response)
            self.credentials.access_token = login_result.get("token")
            self.authenticated = True
            
            logger.info("Successfully authenticated with Supernote Cloud")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _validate_token(self) -> bool:
        """Validate existing access token"""
        try:
            headers = {'Authorization': f'Bearer {self.credentials.access_token}'}
            response = self.session.get(f"{self.BASE_URL}/profile", headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            return False
    
    def _login_with_password(self) -> bool:
        """Login with email and password"""
        try:
            auth_data = {
                'email': self.credentials.email,
                'password': self._hash_password(self.credentials.password),
                'device_id': self.credentials.device_id or self._generate_device_id()
            }
            
            response = self.session.post(self.AUTH_URL, json=auth_data)
            
            if response.status_code == 200:
                auth_result = response.json()
                self.credentials.access_token = auth_result.get('access_token', '')
                self.credentials.refresh_token = auth_result.get('refresh_token', '')
                
                self.authenticated = True
                logger.info("Successfully authenticated with Supernote Cloud")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password for authentication (placeholder)"""
        # This would need to match Supernote's hashing method
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_device_id(self) -> str:
        """Generate a unique device ID"""
        import uuid
        return str(uuid.uuid4())
    
    def list_files(self, directory_id: str = "0") -> List[SupernoteFile]:
        """
        List files in Supernote Cloud using proven API method
        
        Args:
            directory_id: Directory ID to list files from ("0" for root)
        """
        
        if not self.authenticated:
            logger.error("Not authenticated")
            return []
        
        try:
            # Use the proven API payload structure with correct parameter names
            payload = {
                "directoryId": directory_id,
                "pageNo": 1,
                "pageSize": 100,
                "order": "time",
                "sequence": "desc"
            }
            
            # Token goes in headers as x-access-token
            headers = {
                "x-access-token": self.credentials.access_token,
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{self.BASE_URL}{self.ENDPOINTS['file_list']}",
                json=payload,
                headers=headers
            )
            
            if not response.ok:
                logger.error(f"Failed to list files: {response.status_code}")
                return []
            
            result = response.json()
            
            if not result.get("success"):
                logger.error(f"File list request unsuccessful: {result.get('errorMsg', 'Unknown error')}")
                return []
            
            # Files are in userFileVOList, not data
            files_data = result.get("userFileVOList", [])
            
            # Filter out folders, only return actual files
            actual_files_data = [f for f in files_data if f.get('isFolder') != 'Y']
            
            # Parse the file data from current directory
            parsed_files = [self._parse_file_info(file_data) for file_data in actual_files_data]
            
            # If we're looking at root and find the Note folder, also get files from there
            if directory_id == "0":
                note_folder = next((f for f in files_data if f.get('fileName') == 'Note' and f.get('isFolder') == 'Y'), None)
                if note_folder:
                    logger.info("Found Note folder, fetching files from it...")
                    note_files = self.list_files(note_folder.get('id'))
                    parsed_files.extend(note_files)
            
            return parsed_files
                
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def _parse_file_info(self, file_data: Dict[str, Any]) -> SupernoteFile:
        """Parse file information from Supernote API response format"""
        try:
            # Parse file data from API response
            # Handle timestamp conversion
            modified_timestamp = file_data.get('updateTime', 0)
            if isinstance(modified_timestamp, (int, float)):
                modified_time = datetime.fromtimestamp(modified_timestamp / 1000, tz=timezone.utc)
            else:
                modified_time = datetime.now(timezone.utc)
            
            # Determine file type from filename extension
            filename = file_data.get('fileName', '')
            file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
            file_type = 'note' if file_extension == 'note' else file_extension
            
            # Construct path from directory and filename if filePath is empty
            file_path = file_data.get('filePath', '')
            if not file_path and filename:
                # If no filePath provided, use just the filename as path
                file_path = filename
            
            return SupernoteFile(
                file_id=file_data.get('id', ''),
                name=filename,
                path=file_path,
                size=file_data.get('size', 0),  # API uses 'size', not 'fileSize'
                modified_time=modified_time,
                file_type=file_type,
                checksum=file_data.get('fileMd5', ''),
                download_url=None  # Will be obtained via separate API call
            )
        except Exception as e:
            logger.warning(f"Error parsing file data: {e}")
            # Return minimal file info
            return SupernoteFile(
                file_id=file_data.get('id', ''),
                name=file_data.get('fileName', 'unknown'),
                path='',
                size=0,
                modified_time=datetime.now(timezone.utc),
                file_type='unknown',
                checksum='',
                download_url=None
            )
    
    def download_file(self, file: SupernoteFile, local_path: Path) -> bool:
        """
        Download a file from Supernote Cloud using proven API method
        
        Args:
            file: SupernoteFile object to download
            local_path: Local path to save the file
        """
        
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        try:
            # Step 1: Get download URL - use working implementation pattern
            payload = {
                "id": file.file_id,
                "type": 0  # Required parameter from working sncloud implementation
            }
            
            # Token goes in headers as x-access-token
            headers = {
                "x-access-token": self.credentials.access_token,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Requesting download URL for file: {file.name} (ID: {file.file_id})")
            logger.info(f"Download URL payload: {payload}")
            print(f"🔍 DEBUG: Requesting download URL for file: {file.name} (ID: {file.file_id})")
            print(f"🔍 DEBUG: Download URL payload: {payload}")
            
            # Use the correct endpoint from working implementation
            url_response = self.session.post(
                f"{self.BASE_URL}{self.ENDPOINTS['download_url']}",
                json=payload,
                headers=headers
            )
            
            if not url_response.ok:
                logger.error(f"Failed to get download URL: {url_response.status_code}")
                return False
            
            url_result = url_response.json()
            logger.info(f"Download URL response: {url_result}")
            print(f"🔍 DEBUG: Download URL response: {url_result}")
            
            if not url_result.get("success"):
                logger.error(f"Download URL request unsuccessful: {url_result.get('errorMsg', 'Unknown error')}")
                return False
            
            download_url = url_result.get("url")  # API returns 'url' field, not 'data'
            
            if not download_url:
                logger.error(f"No download URL returned for file: {file.name}")
                return False
            
            # Step 2: Download file content
            logger.info(f"Downloading {file.name} from {download_url}")
            
            download_response = self.session.get(download_url, stream=True)
            download_response.raise_for_status()
            
            # Ensure local directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(local_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded {file.name} to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {file.name}: {e}")
            return False
    
    def sync_recent_files(self, local_dir: Path, since: Optional[datetime] = None) -> List[Path]:
        """
        Sync recent files from Supernote Cloud to local directory
        
        Args:
            local_dir: Local directory to sync files to
            since: Only sync files modified after this datetime
        
        Returns:
            List of local file paths that were downloaded
        """
        
        if not self.authenticated:
            logger.error("Cannot sync - not authenticated")
            return []
        
        # Default to syncing files from last 7 days
        if since is None:
            since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            since = since.replace(day=since.day - 7)
        
        logger.info(f"Syncing files modified since: {since}")
        
        # Get list of files
        all_files = self.list_files()
        recent_files = [
            f for f in all_files
            if f.modified_time > since and f.file_type in ["note", "pdf"]
        ]
        
        logger.info(f"Found {len(recent_files)} recent files to sync")
        
        downloaded_files = []
        
        for file in recent_files:
            # Create local filename
            safe_name = "".join(c for c in file.name if c.isalnum() or c in "._-")
            local_path = local_dir / safe_name
            
            # Skip if file already exists and hasn't changed
            if local_path.exists():
                local_mtime = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
                if local_mtime >= file.modified_time:
                    logger.debug(f"Skipping {file.name} - already up to date")
                    continue
            
            # Download file
            if self.download_file(file, local_path):
                downloaded_files.append(local_path)
        
        logger.info(f"Successfully downloaded {len(downloaded_files)} files")
        return downloaded_files


def create_supernote_client(config: Dict[str, Any], email: Optional[str] = None, password: Optional[str] = None) -> Optional[SupernoteCloudAPI]:
    """
    Create Supernote Cloud API client from configuration or environment
    
    Args:
        config: Configuration dictionary with credentials
        email: Optional email override (for CLI prompts)
        password: Optional password override (for CLI prompts)
        
    Returns:
        SupernoteCloudAPI client or None if credentials not available
    """
    import os
    from dotenv import load_dotenv
    
    # Load .env file if it exists
    load_dotenv()
    
    supernote_config = config.get('supernote', {})
<<<<<<< HEAD

    if not supernote_config.get('enabled', False):
        logger.info("Supernote Cloud integration is disabled")
        return None

    def _get_env(name: str) -> str:
        return os.environ.get(name, '')

    credentials = SupernoteCredentials(
        email=_get_env(supernote_config.get('email_env', 'SUPERNOTE_EMAIL')),
        password=_get_env(supernote_config.get('password_env', 'SUPERNOTE_PASSWORD')),
        access_token=_get_env(supernote_config.get('access_token_env', 'SUPERNOTE_ACCESS_TOKEN')),
        refresh_token=_get_env(supernote_config.get('refresh_token_env', 'SUPERNOTE_REFRESH_TOKEN')),
        device_id=_get_env(supernote_config.get('device_id_env', 'SUPERNOTE_DEVICE_ID'))
    )

    if not credentials.email or not (credentials.password or credentials.access_token):
        logger.warning("Supernote credentials not configured in environment variables")
=======
    
    # Check if explicitly disabled
    if supernote_config.get('enabled') is False:
        logger.info("Supernote Cloud integration is disabled")
        return None
    
    # Priority order for credentials:
    # 1. Function parameters (from CLI prompts)
    # 2. Environment variables from .env
    # 3. Config file (deprecated for credentials)
    
    credentials = SupernoteCredentials(
        email=email or os.getenv('SUPERNOTE_EMAIL') or supernote_config.get('email', ''),
        password=password or os.getenv('SUPERNOTE_PASSWORD') or supernote_config.get('password', ''),
        access_token=os.getenv('SUPERNOTE_ACCESS_TOKEN') or supernote_config.get('access_token', ''),
        refresh_token=os.getenv('SUPERNOTE_REFRESH_TOKEN') or supernote_config.get('refresh_token', ''),
        device_id=os.getenv('SUPERNOTE_DEVICE_ID') or supernote_config.get('device_id', '')
    )
    
    if not credentials.email:
        logger.warning("No Supernote email configured (check .env file or use CLI prompt)")
        return None
    
    if not credentials.password and not credentials.access_token:
        logger.warning("No Supernote password or access token configured")
>>>>>>> chore/ignore-handoff
        return None
    
    client = SupernoteCloudAPI(credentials)
    
    if client.authenticate():
        return client
    else:
        logger.error("Failed to authenticate with Supernote Cloud")
        return None


# Example configuration for YAML file:
EXAMPLE_CONFIG = """
supernote:
  enabled: true
  email: "your.email@example.com"
  password: "your_password"  # Optional if using access tokens
  access_token: ""  # Can be obtained after first login
  refresh_token: ""
  device_id: ""  # Auto-generated if not provided
  sync_interval: 3600  # Sync every hour
  local_sync_dir: "data/supernote_sync/"
"""