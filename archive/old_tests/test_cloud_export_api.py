#!/usr/bin/env python3
"""
Test Supernote Cloud API for export capabilities
"""

import sys
from pathlib import Path
import requests
import json

# Add the src directory to Python path
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))

from utils.supernote_api import SupernoteCloudAPI

def test_cloud_export_endpoints():
    """Test if Supernote Cloud has export endpoints we can use"""
    
    print("🌐 Testing Supernote Cloud Export API")
    print("=" * 45)
    
    try:
        username = input("📱 Username: ").strip()
        password = input("🔒 Password: ").strip()
        
        api = SupernoteCloudAPI()
        
        print("🔐 Authenticating...")
        if not api.login(username, password):
            print("❌ Authentication failed")
            return
        
        print("✅ Authenticated")
        
        # Get file list
        files = api.list_files()
        note_files = [f for f in files if f.file_type == 'note']
        
        if not note_files:
            print("❌ No .note files found")
            return
        
        test_file = note_files[0]
        print(f"🎯 Testing with: {test_file.name}")
        
        # Test export endpoints
        base_url = "https://cloud.supernote.com"
        headers = api._get_headers()
        
        export_endpoints = [
            # Common patterns for file export APIs
            f"/api/v1/file/{test_file.file_id}/export",
            f"/api/v1/file/{test_file.file_id}/render", 
            f"/api/v1/file/{test_file.file_id}/image",
            f"/api/v1/file/{test_file.file_id}/png",
            f"/api/v1/export/{test_file.file_id}",
            f"/api/v1/render/{test_file.file_id}",
            f"/api/v1/files/{test_file.file_id}/export",
            f"/api/v1/files/{test_file.file_id}/render"
        ]
        
        successful_endpoints = []
        
        for endpoint in export_endpoints:
            url = base_url + endpoint
            print(f"🔍 Testing: {endpoint}")
            
            try:
                # Test GET request
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    print(f"   ✅ Success! Type: {content_type}, Size: {content_length:,} bytes")
                    
                    # If it looks like an image, save it
                    if 'image' in content_type or content_length > 10000:
                        output_path = f"/home/ed/ghost-writer/cloud_export_{test_file.file_id}.png"
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        print(f"   💾 Saved to: {output_path}")
                        successful_endpoints.append((endpoint, output_path))
                    
                elif response.status_code == 404:
                    print(f"   ❌ Not found")
                elif response.status_code in [401, 403]:
                    print(f"   ❌ Auth issue")
                else:
                    print(f"   ⚠️  Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Also test POST with format parameter
            try:
                payload = {"format": "png"}
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ POST also works!")
                    
            except Exception:
                pass  # Don't spam POST errors
        
        # Summary
        print(f"\n📊 Export Test Results:")
        if successful_endpoints:
            print(f"   ✅ Found {len(successful_endpoints)} working endpoints:")
            for endpoint, file_path in successful_endpoints:
                print(f"      {endpoint} → {file_path}")
            
            print(f"\n🎉 Cloud export is possible!")
            return True
        else:
            print(f"   ❌ No working export endpoints found")
            print(f"   💡 Supernote Cloud may not have public export API")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_cloud_export_endpoints()
    
    if not success:
        print(f"\n💭 Alternative approaches:")
        print("   1. Improve RLE decoder contrast/thickness")
        print("   2. Use browser automation to export from web interface")
        print("   3. Build photo-based workflow for immediate functionality")
        print("   4. Focus on notes that can be exported as PDF first")