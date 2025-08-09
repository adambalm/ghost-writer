#!/usr/bin/env python3
"""
Debug Supernote Cloud connection - detailed error reporting
"""

import os
import sys
import json
from getpass import getpass
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_supernote_connection():
    """Debug Supernote Cloud connection with detailed logging"""
    
    print("🔍 Ghost Writer - Debug Supernote Connection")
    print("=" * 50)
    print()
    
    # Get credentials
    print("Enter your Supernote Cloud credentials:")
    email = input("📧 Email: ").strip()
    password = getpass("🔐 Password: ")
    
    print("\n❓ Credential Verification:")
    print("   📧 Email format looks correct" if "@" in email and "." in email else "   ⚠️  Email format might be wrong")
    print("   🔐 Password received" if password else "   ❌ No password entered")
    
    print("\n💡 To verify these are correct:")
    print("   1. Can you log into https://cloud.supernote.com with these credentials?")
    print("   2. Do you see your .note files when you log in?")
    
    proceed = input("\n✅ Credentials look right? Press Enter to continue, or Ctrl+C to quit...")
    
    print("\n🔄 Testing connection with detailed logging...")
    
    try:
        import requests
        
        # Test 1: Basic connectivity
        print("1️⃣ Testing basic connectivity to Supernote...")
        base_url = "https://cloud.supernote.com/api"
        
        try:
            response = requests.get("https://cloud.supernote.com", timeout=10)
            print(f"   ✅ Can reach Supernote website (status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ Cannot reach Supernote website: {e}")
            return
        
        # Test 2: Random code endpoint
        print("2️⃣ Testing random code endpoint...")
        random_url = f"{base_url}/official/user/query/random/code"
        
        # Add required parameters based on working implementation
        random_params = {
            "countryCode": "1",
            "account": email
        }
        
        try:
            response = requests.post(random_url, json=random_params, timeout=10)
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.ok:
                try:
                    data = response.json()
                    if data.get("success"):
                        # The response format includes randomCode and timestamp directly
                        random_code = data.get("randomCode")
                        timestamp = data.get("timestamp")
                        print(f"   ✅ Got random code: {random_code}")
                        print(f"   ✅ Got timestamp: {timestamp}")
                    else:
                        print(f"   ❌ Random code request failed: {data}")
                        return
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response")
                    return
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                return
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return
        
        # Test 3: Login attempt
        print("3️⃣ Testing login with your credentials...")
        print(f"   📧 Using email: {email}")
        print("   🔐 Using password: [hidden]")
        
        import hashlib
        
        # Use the timestamp from the random code response
        # Encrypt password using Supernote's exact method
        # Based on working implementation: MD5(password) + randomCode, then SHA256
        md5_password = hashlib.md5(password.encode()).hexdigest()
        combined = f"{md5_password}{random_code}"
        final_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        print(f"   🔒 Password hash generated: {final_hash[:16]}...")
        
        login_data = {
            "countryCode": 1,
            "account": email,  # Use 'account' not 'loginName'
            "password": final_hash,
            "browser": "Chrome107",
            "equipment": "1",
            "loginMethod": "1",
            "timestamp": timestamp,
            "language": "en"
        }
        
        login_url = f"{base_url}/official/user/account/login/new"
        
        try:
            response = requests.post(login_url, json=login_data, timeout=10)
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text[:300]}...")
            
            if response.ok:
                try:
                    data = response.json()
                    if data.get("success"):
                        print("   ✅ Login successful!")
                        token = data.get("token")  # Token is directly in the response
                        print(f"   Token: {token[:20]}...")
                        
                        # Test 4: File listing
                        print("4️⃣ Testing file listing...")
                        files_url = f"{base_url}/file/list/query"
                        files_payload = {
                            "token": token,
                            "directoryId": "0"
                        }
                        
                        files_response = requests.post(files_url, json=files_payload, timeout=10)
                        print(f"   Status code: {files_response.status_code}")
                        
                        if files_response.ok:
                            files_data = files_response.json()
                            if files_data.get("success"):
                                files = files_data.get("data", [])
                                print(f"   ✅ Found {len(files)} files in your cloud!")
                                
                                for i, file in enumerate(files[:3]):
                                    print(f"      - {file.get('fileName', 'Unknown')}")
                                
                                print("\n🎉 SUCCESS! Everything is working!")
                                print("\nYour Supernote Cloud integration is ready to use!")
                                return
                            else:
                                print(f"   ❌ File listing failed: {files_data}")
                        else:
                            print(f"   ❌ File listing HTTP error: {files_response.status_code}")
                    else:
                        print(f"   ❌ Login failed: {data.get('errorMsg', 'Unknown error')}")
                        if "password" in str(data).lower():
                            print("   💡 This might be a password issue. Double-check your credentials.")
                        elif "user" in str(data).lower() or "email" in str(data).lower():
                            print("   💡 This might be an email issue. Make sure you use the same email as your Supernote account.")
                        
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response from login")
            else:
                print(f"   ❌ Login HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Login request failed: {e}")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_supernote_connection()