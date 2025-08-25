#!/usr/bin/env python3
"""
Test the main Supernote API with the fixed structure
"""

import os
import sys
from getpass import getpass
from pathlib import Path

# Add the src directory to Python path using absolute path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

def test_main_api():
    """Test the main SupernoteCloudAPI class"""
    
    print("🎯 Testing Main Supernote API")
    print("=" * 40)
    
    phone_number = "4139491742"
    password = getpass("🔐 Enter your Supernote password: ")
    
    try:
        from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
        
        # Create credentials
        creds = SupernoteCredentials(email=phone_number, password=password)
        
        # Create API client
        api = SupernoteCloudAPI(creds)
        
        # Test authentication
        print("🔑 Authenticating...")
        if not api.authenticate():
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful!")
        
        # List files
        print("📁 Fetching files...")
        files = api.list_files()
        
        print(f"✅ Found {len(files)} files!")
        
        for i, file in enumerate(files[:5]):
            print(f"  {i+1}. {file.name} ({file.file_type})")
            print(f"     📅 {file.modified_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"     📏 {file.size} bytes")
        
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more files")
        
        print(f"\n🎉 SUCCESS! Main API is working with {len(files)} files!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_main_api()