#!/usr/bin/env python3
"""
Quick Supernote Cloud test - minimal setup required

This script tests your Supernote connection with minimal configuration.
Set SUPERNOTE_EMAIL and SUPERNOTE_PASSWORD environment variables before running.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_supernote_connection():
    """Test Supernote Cloud connection with minimal setup"""
    
    print("🎯 Ghost Writer - Quick Supernote Test")
    print("=" * 40)
    print()
    
    # Get credentials from environment
    email = os.environ.get("SUPERNOTE_EMAIL", "").strip()
    password = os.environ.get("SUPERNOTE_PASSWORD", "")

    if not email or not password:
        print("❌ SUPERNOTE_EMAIL and SUPERNOTE_PASSWORD must be set in the environment")
        return
    
    print("\n🔄 Testing connection to Supernote Cloud...")
    
    try:
        # Import our API classes
        from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials
        
        # Create credentials
        creds = SupernoteCredentials(email=email, password=password)
        
        # Create API client
        api = SupernoteCloudAPI(creds)
        
        # Test authentication
        print("🔑 Authenticating...")
        if not api.authenticate():
            print("❌ Authentication failed - check your credentials")
            return
        
        print("✅ Authentication successful!")
        
        # List files
        print("📁 Fetching your files...")
        files = api.list_files()
        
        if not files:
            print("📂 No files found (or empty root directory)")
        else:
            print(f"📄 Found {len(files)} files in your cloud storage:")
            print()
            
            # Show file summary
            note_files = [f for f in files if f.file_type == 'note']
            pdf_files = [f for f in files if f.file_type == 'pdf']
            other_files = [f for f in files if f.file_type not in ['note', 'pdf']]
            
            print(f"  📝 {len(note_files)} .note files")
            print(f"  📄 {len(pdf_files)} PDF files") 
            print(f"  📁 {len(other_files)} other files")
            print()
            
            # Show recent files
            if files:
                print("Recent files:")
                sorted_files = sorted(files, key=lambda f: f.modified_time, reverse=True)
                for i, file in enumerate(sorted_files[:5]):
                    print(f"  {i+1}. {file.name} ({file.file_type})")
                    print(f"     📅 {file.modified_time.strftime('%Y-%m-%d %H:%M')}")
                print()
        
        print("🎉 SUCCESS! Your Supernote Cloud integration is working!")
        print()
        print("✨ Next steps:")
        print("1. Run: source venv/bin/activate")
        print("2. Run: ghost-writer sync --output supernote_downloads/")
        print("3. Check the downloaded files in supernote_downloads/")
        print("4. Process them: ghost-writer process supernote_downloads/ --format markdown")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Make sure you're in the Ghost Writer directory and have installed requirements")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your internet connection and credentials")

if __name__ == "__main__":
    test_supernote_connection()