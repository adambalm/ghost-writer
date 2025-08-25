#!/usr/bin/env python3
"""
Download fuckt.note from Supernote Cloud for testing
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def download_fuckt_note():
    """Download fuckt.note from Supernote Cloud"""
    
    print("Supernote Cloud Download")
    print("=" * 30)
    
    try:
        from utils.supernote_api import create_supernote_client
        from utils.config import config
        
        # Get credentials
        email = input("Enter your Supernote email: ")
        password = input("Enter your Supernote password: ")
        
        if not email or not password:
            print("Email and password required")
            return False
        
        # Create client
        print("Connecting to Supernote Cloud...")
        temp_config = config.copy()
        if 'supernote' not in temp_config:
            temp_config['supernote'] = {}
        temp_config['supernote']['email'] = email
        temp_config['supernote']['password'] = password
        
        client = create_supernote_client(temp_config)
        
        if not client:
            print("Failed to connect to Supernote Cloud")
            return False
        
        print("Connected successfully!")
        
        # Get file list
        print("Getting file list...")
        files = client.get_recent_files(limit=100)
        
        if not files:
            print("No files found")
            return False
        
        # Look for fuckt.note
        fuckt_file = None
        print(f"Found {len(files)} files:")
        
        for file in files:
            name = file.get('name', 'Unknown')
            size = file.get('size', 0)
            print(f"  {name} ({size:,} bytes)")
            
            if name == 'fuckt.note':
                fuckt_file = file
                print(f"  >>> Found target file: {name}")
        
        if not fuckt_file:
            print("fuckt.note not found in your Supernote Cloud")
            print("Available .note files:")
            for file in files:
                name = file.get('name', '')
                if name.endswith('.note'):
                    print(f"  - {name}")
            return False
        
        # Download fuckt.note
        file_id = fuckt_file.get('id')
        output_path = project_root / 'fuckt.note'
        
        print(f"Downloading {fuckt_file['name']}...")
        success = client.download_file(file_id, str(output_path))
        
        if success and output_path.exists():
            size = output_path.stat().st_size
            print(f"Downloaded fuckt.note: {size:,} bytes")
            return True
        else:
            print("Download failed")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = download_fuckt_note()
    if success:
        print("Ready to test with fuckt.note")
    else:
        print("Download failed")
        sys.exit(1)