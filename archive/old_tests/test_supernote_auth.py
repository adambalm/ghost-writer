#!/usr/bin/env python3
"""
Test Supernote authentication with detailed debugging
"""

import sys
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_auth():
    from utils.supernote_api import create_supernote_client
    from utils.config import Config
    
    # Get credentials
    email = input("Enter your Supernote email/phone: ")
    password = input("Enter your Supernote password: ")
    
    # Create config
    config = Config()
    
    # Try to authenticate
    print(f"Attempting to authenticate with account: {email}")
    client = create_supernote_client(config, email=email, password=password)
    
    if client:
        print("SUCCESS: Authentication successful!")
        return True
    else:
        print("FAILED: Authentication failed")
        print("Please check:")
        print("1. Your email/phone number is correct")
        print("2. Your password is correct")
        print("3. You can log in at https://cloud.supernote.com")
        return False

if __name__ == "__main__":
    test_auth()