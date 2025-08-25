#!/usr/bin/env python3
"""Test Supernote login functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.supernote_api import create_supernote_client

def test_login():
    """Test login with phone number"""
    print("Testing Supernote Cloud login...")
    
    # Test credentials (you'll need to replace with actual ones)
    phone = input("Enter phone number (digits only, e.g., 4139491742): ")
    password = input("Enter password: ")
    
    config = {}  # Empty config, we'll pass credentials directly
    
    print(f"\nAttempting login with phone: {phone}")
    client = create_supernote_client(config, email=phone, password=password)
    
    if client:
        print("SUCCESS: Logged in to Supernote Cloud")
        
        # Try to list files
        print("\nFetching available notes...")
        files = client.list_files()
        print(f"Found {len(files)} files")
        
        if files:
            print("\nFirst 5 files:")
            for i, file in enumerate(files[:5]):
                print(f"  {i+1}. {file.name} ({file.file_type})")
        
        return True
    else:
        print("FAILED: Could not log in")
        return False

if __name__ == "__main__":
    test_login()