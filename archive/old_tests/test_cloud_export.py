#!/usr/bin/env python3
"""
Test Supernote Cloud for PDF/image export capabilities
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.supernote_api import SupernoteCloudAPI
import requests

def explore_cloud_export_options():
    """Explore Supernote Cloud API for export options"""
    
    print("🌐 Exploring Supernote Cloud Export Options")
    print("=" * 50)
    
    # Initialize API
    api = SupernoteCloudAPI()
    
    # Get credentials
    try:
        username = input("📱 Username (email or phone): ").strip()
        password = input("🔒 Password: ").strip()
        
        print("🔐 Authenticating...")
        success = api.login(username, password)
        
        if not success:
            print("❌ Authentication failed")
            return
            
        print("✅ Authentication successful")
        
        # List files to get file IDs
        print("\n📁 Getting file list...")
        files = api.list_files()
        
        if not files:
            print("❌ No files found")
            return
            
        print(f"✅ Found {len(files)} files")
        
        # Find a .note file to test with
        note_files = [f for f in files if f.file_type == 'note']
        
        if not note_files:
            print("❌ No .note files found")
            return
            
        test_file = note_files[0]
        print(f"🎯 Testing with file: {test_file.name}")
        
        # Test different API endpoints that might exist
        base_url = "https://cloud.supernote.com"
        
        # Common export endpoint patterns to try
        export_patterns = [
            f"/api/v1/file/{test_file.file_id}/export/pdf",
            f"/api/v1/file/{test_file.file_id}/export/image", 
            f"/api/v1/file/{test_file.file_id}/convert/pdf",
            f"/api/v1/file/{test_file.file_id}/convert/image",
            f"/api/v1/export/pdf/{test_file.file_id}",
            f"/api/v1/export/image/{test_file.file_id}",
            f"/api/v1/files/{test_file.file_id}/pdf",
            f"/api/v1/files/{test_file.file_id}/image",
        ]
        
        print(f"\n🔍 Testing export endpoints...")
        
        headers = api._get_headers()
        
        for pattern in export_patterns:
            url = base_url + pattern
            
            try:
                # Try GET first
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ GET {pattern} - Success!")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                    print(f"   Content-Length: {response.headers.get('content-length')}")
                elif response.status_code in [400, 401, 403, 404]:
                    print(f"❌ GET {pattern} - {response.status_code}")
                else:
                    print(f"⚠️  GET {pattern} - {response.status_code}")
                    
            except Exception as e:
                print(f"❌ GET {pattern} - Error: {e}")
                
            # Try POST with common payload
            try:
                payload = {"format": "pdf", "file_id": test_file.file_id}
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ POST {pattern} - Success!")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                
            except Exception as e:
                pass  # Don't spam POST errors
        
        print(f"\n💡 Results:")
        print("- Tested common export endpoint patterns")
        print("- If any returned 200, those endpoints support export")
        print("- May need to check Supernote Cloud web interface developer tools")
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_cloud_export_options()