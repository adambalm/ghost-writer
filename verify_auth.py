#!/usr/bin/env python3
"""
Verify Supernote authentication and note retrieval
Run this to test if you can connect to your Supernote Cloud account
"""

import sys
import getpass
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.supernote_api import create_supernote_client
from dotenv import load_dotenv

def main():
    print("Supernote Cloud Authentication Test")
    print("-" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Try environment variables first
    account = os.getenv('SUPERNOTE_PHONE') or os.getenv('SUPERNOTE_EMAIL')
    password = os.getenv('SUPERNOTE_PASSWORD')
    
    if not account or not password:
        print("\nEnter your Supernote Cloud credentials:")
        print("(For US phone numbers, enter digits only, e.g., 5551234567)")
        print("(For email accounts, enter your full email address)")
        
        account = input("\nAccount (phone/email): ").strip()
        password = getpass.getpass("Password: ")
    else:
        print("\nUsing credentials from environment variables")
    
    print(f"\nConnecting with account: {account}")
    print("Authenticating...")
    
    config = {}
    client = create_supernote_client(config, email=account, password=password)
    
    if not client:
        print("\nFAILED: Could not authenticate")
        print("Please check your credentials and try again")
        return False
    
    print("\nSUCCESS: Authenticated with Supernote Cloud")
    
    # List available notes
    print("\nFetching your notes...")
    files = client.list_files()
    
    print(f"\nFound {len(files)} files in your account")
    
    if files:
        print("\nYour notes:")
        for i, file in enumerate(files[:10], 1):  # Show first 10
            size_mb = file.size / (1024 * 1024)
            print(f"  {i}. {file.name} ({size_mb:.1f} MB) - {file.file_type}")
        
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
    
    print("\n" + "=" * 40)
    print("Authentication test complete!")
    print("You can now use the web interface at http://localhost:5001")
    print("Use the same credentials to log in there.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)