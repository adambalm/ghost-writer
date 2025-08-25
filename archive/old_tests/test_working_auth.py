#!/usr/bin/env python3
"""
Test authentication using the exact code that works in test_main_api.py
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

def test_auth():
    from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
    
    # Use your phone number exactly as in the working script
    phone_number = "4139491742"
    password = input("Enter your Supernote password: ")
    
    # Create credentials exactly as in the working script
    creds = SupernoteCredentials(email=phone_number, password=password)
    
    # Create API client
    api = SupernoteCloudAPI(creds)
    
    # Test authentication
    print("Authenticating...")
    if not api.authenticate():
        print("Authentication failed")
        print("This is the exact same code that works in test_main_api.py")
        return False
    
    print("SUCCESS! Authentication successful!")
    
    # List files to verify it works
    files = api.list_files()
    print(f"Found {len(files)} files")
    
    # Show first few files
    for file in files[:3]:
        print(f"  - {file.name}")
    
    return True

if __name__ == "__main__":
    test_auth()