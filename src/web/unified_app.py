#!/usr/bin/env python3
"""
Unified Web Interface using clean room Supernote implementation
Replaces all the duplicate web viewers with a single, properly architected solution
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project paths before other imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from flask import Flask, render_template, request, jsonify, send_file  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from services.supernote_service import supernote_service  # noqa: E402

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder=str(project_root / "templates"))
app.secret_key = os.urandom(24)

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = project_root / "uploads"
RESULTS_FOLDER = project_root / "results"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)

# Global state
authenticated = False
cloud_files: list = []
last_sync_time = None


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('unified_index.html', 
                         authenticated=authenticated,
                         file_count=len(cloud_files),
                         last_sync=last_sync_time)


@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Supernote Cloud"""
    global authenticated
    
    data = request.json
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    
    # Validate input
    if not phone:
        return jsonify({'success': False, 'error': 'Phone number is required'})
    
    if not password:
        return jsonify({'success': False, 'error': 'Password is required'})
    
    # Basic phone number validation (US format)
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'error': 'Please enter a 10-digit US phone number (digits only)'})
    
    try:
        logger.info(f"Attempting authentication for phone: {phone}")
        success = supernote_service.authenticate_supernote(phone, password)
        
        if success:
            authenticated = True
            # Load files after successful authentication
            refresh_cloud_files()
            logger.info(f"Authentication successful, found {len(cloud_files)} files")
            return jsonify({
                'success': True, 
                'message': f'Successfully connected! Found {len(cloud_files)} files in your account.'
            })
        else:
            logger.warning(f"Authentication failed for phone: {phone}")
            return jsonify({
                'success': False, 
                'error': 'Invalid phone number or password. Please check your Supernote account credentials.'
            })
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Authentication exception for {phone}: {error_msg}")
        
        # Provide user-friendly error messages
        if 'network' in error_msg.lower() or 'connection' in error_msg.lower():
            user_error = 'Network connection failed. Please check your internet connection and try again.'
        elif 'timeout' in error_msg.lower():
            user_error = 'Connection timed out. Supernote servers may be busy. Please try again.'
        elif 'credentials' in error_msg.lower() or 'authentication' in error_msg.lower():
            user_error = 'Authentication failed. Please verify your phone number and password.'
        else:
            user_error = f'Authentication error: {error_msg}'
            
        return jsonify({'success': False, 'error': user_error})


@app.route('/cloud-files')
def get_cloud_files():
    """Get list of files from Supernote Cloud"""
    if not authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        files = supernote_service.list_cloud_files()
        file_list = [{
            'id': f.file_id,
            'name': f.name,
            'size': f.size,
            'modified': f.modified_time.isoformat() if f.modified_time else None,
            'type': f.file_type
        } for f in files]
        
        return jsonify({'success': True, 'files': file_list})
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/process-file', methods=['POST'])
def process_file():
    """Process a .note file"""
    data = request.json
    file_id = data.get('file_id')
    local_path = data.get('local_path')
    
    try:
        if file_id:
            # Download from cloud first
            temp_file = UPLOAD_FOLDER / f"temp_{file_id}.note"
            success = supernote_service.download_cloud_file(file_id, temp_file)
            if not success:
                return jsonify({'success': False, 'error': 'Failed to download file'})
            file_path = temp_file
        elif local_path:
            file_path = Path(local_path)
            if not file_path.exists():
                return jsonify({'success': False, 'error': 'File not found'})
        else:
            return jsonify({'success': False, 'error': 'No file specified'})
        
        # Process using unified service
        result = supernote_service.process_note_file(file_path, RESULTS_FOLDER)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process a local .note file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if not file.filename.endswith('.note'):
        return jsonify({'success': False, 'error': 'Only .note files are supported'})
    
    try:
        # Save uploaded file
        file_path = UPLOAD_FOLDER / file.filename
        file.save(file_path)
        
        # Process using unified service
        result = supernote_service.process_note_file(file_path, RESULTS_FOLDER)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download/<path:filename>')
def download_file(filename):
    """Download processed files"""
    file_path = RESULTS_FOLDER / filename
    if file_path.exists():
        return send_file(file_path)
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/status')
def status():
    """Get system status"""
    return jsonify({
        'authenticated': authenticated,
        'cloud_files_count': len(cloud_files),
        'last_sync': last_sync_time.isoformat() if last_sync_time else None,
        'upload_folder': str(UPLOAD_FOLDER),
        'results_folder': str(RESULTS_FOLDER)
    })


@app.route('/reset-auth', methods=['POST'])
def reset_auth():
    """Reset authentication state (for testing only)"""
    global authenticated, cloud_files, last_sync_time
    authenticated = False
    cloud_files = []
    last_sync_time = None
    return jsonify({'success': True, 'message': 'Authentication reset'})


def refresh_cloud_files():
    """Refresh the list of cloud files"""
    global cloud_files, last_sync_time
    
    try:
        cloud_files = supernote_service.list_cloud_files()
        last_sync_time = datetime.now()
        logger.info(f"Refreshed {len(cloud_files)} cloud files")
    except Exception as e:
        logger.error(f"Failed to refresh cloud files: {e}")


if __name__ == '__main__':
    print("Starting Ghost Writer web interface on http://localhost:5000")
    print("User authentication required - no auto-login")
    app.run(host='0.0.0.0', port=5000, debug=True)