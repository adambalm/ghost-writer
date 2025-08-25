#!/usr/bin/env python3
"""
Test script for Supernote Cloud API integration

Usage:
    SUPERNOTE_EMAIL=you@example.com SUPERNOTE_PASSWORD=your-password python test_supernote_api.py

This script reads Supernote credentials from environment variables and tests the API connection.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path using absolute path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.supernote_api import SupernoteCloudAPI, SupernoteCredentials


def test_supernote_api():
    """Test the Supernote API integration"""
    
    print("🚀 Testing Supernote Cloud API Integration")
    print("=" * 50)
    
    # Get credentials from environment
    email = os.environ.get("SUPERNOTE_EMAIL", "").strip()
    password = os.environ.get("SUPERNOTE_PASSWORD", "")

    if not email or not password:
        print("❌ SUPERNOTE_EMAIL and SUPERNOTE_PASSWORD must be set in the environment")
        return False

    # Create credentials
    credentials = SupernoteCredentials(
        email=email,
        password=password
    )
    
    # Create API client
    print("\n📡 Creating API client...")
    api = SupernoteCloudAPI(credentials)
    
    # Test authentication
    print("🔑 Testing authentication...")
    
    if not api.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful!")
    
    # Test file listing
    print("\n📁 Listing files in root directory...")
    
    try:
        files = api.list_files()
        
        if not files:
            print("📂 No files found in root directory")
        else:
            print(f"📄 Found {len(files)} files:")
            
            for i, file in enumerate(files[:10]):  # Show first 10 files
                print(f"  {i+1}. {file.name} ({file.file_type}) - {file.size} bytes")
                print(f"     Modified: {file.modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if len(files) > 10:
                print(f"     ... and {len(files) - 10} more files")
            
            # Test download of first .note file
            note_files = [f for f in files if f.file_type == 'note']
            
            if note_files:
                test_file = note_files[0]
                print(f"\n💾 Testing download of: {test_file.name}")
                
                download_path = Path("test_download") / test_file.name
                
                if api.download_file(test_file, download_path):
                    print(f"✅ Successfully downloaded to: {download_path}")
                    
                    # Show file info
                    if download_path.exists():
                        size = download_path.stat().st_size
                        print(f"📊 Downloaded file size: {size} bytes")
                        
                        # Clean up test download
                        download_path.unlink()
                        download_path.parent.rmdir() if download_path.parent.exists() else None
                        
                else:
                    print("❌ Download failed")
            else:
                print("ℹ️  No .note files found to test download")
        
        print("\n🎉 API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during file listing: {e}")
        return False


def main():
    """Main entry point"""
    
    try:
        success = test_supernote_api()
        
        if success:
            print("\n✅ All tests passed!")
            print("🚀 Your Supernote Cloud integration is ready to use!")
            print("\nNext steps:")
            print("1. Configure your credentials in config/config.yaml")
            print("2. Run: ghost-writer sync --since 2025-01-01")
            print("3. Or use: ghost-writer sync --output ~/Downloads/supernote_sync/")
        else:
            print("\n❌ Tests failed!")
            print("Please check your credentials and internet connection.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please report this issue with the full error message.")


if __name__ == "__main__":
    main()