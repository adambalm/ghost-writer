#!/usr/bin/env python3
"""Test Supernote authentication with correct credentials"""

import requests
import hashlib

def test_auth():
    phone = "4139491742"
    password = "cesterCAT50supernote"  # Testing second option
    base_url = "https://cloud.supernote.com/api"
    
    print(f"Testing authentication for {phone}")
    
    try:
        # Step 1: Get random code
        print("1. Getting random code...")
        random_params = {"countryCode": "1", "account": phone}
        response = requests.post(f"{base_url}/official/user/query/random/code", json=random_params, timeout=10)
        
        if response.ok:
            data = response.json()
            if data.get("success"):
                random_code = data.get("randomCode")
                timestamp = data.get("timestamp")
                print(f"   ✅ Random code: {random_code}")
                print(f"   ✅ Timestamp: {timestamp}")
                
                # Step 2: Authenticate with correct parameters
                print("2. Authenticating...")
                password_md5 = hashlib.md5(password.encode()).hexdigest()
                password_hash = hashlib.sha256((password_md5 + random_code).encode()).hexdigest()
                
                auth_params = {
                    "countryCode": 1,
                    "account": phone,
                    "password": password_hash,
                    "browser": "Chrome107",
                    "equipment": "1",
                    "loginMethod": "1",
                    "timestamp": timestamp,
                    "language": "en"
                }
                
                auth_response = requests.post(f"{base_url}/official/user/account/login/new", json=auth_params, timeout=10)
                
                if auth_response.ok:
                    auth_data = auth_response.json()
                    print(f"   Response: {auth_data}")
                    
                    if auth_data.get("success"):
                        token = auth_data.get("token")
                        print(f"   ✅ Authentication successful!")
                        print(f"   Token: {token[:20]}...")
                        return True
                    else:
                        print(f"   ❌ Auth failed: {auth_data}")
                else:
                    print(f"   ❌ HTTP error: {auth_response.status_code}")
                    print(f"   Response: {auth_response.text}")
            else:
                print(f"   ❌ Random code failed: {data}")
        else:
            print(f"   ❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return False

if __name__ == "__main__":
    test_auth()