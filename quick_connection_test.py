#!/usr/bin/env python3
"""
Quick connection test - just check if we can reach the API
"""

import requests
import json

def test_connection():
    """Test basic connectivity to Supernote Cloud API"""
    
    print("🔍 Quick Supernote Connection Test")
    print("=" * 40)
    
    base_url = "https://cloud.supernote.com/api"
    phone_number = "4139491742"
    
    try:
        # Test 1: Basic connectivity
        print("1️⃣ Testing basic connectivity...")
        response = requests.get("https://cloud.supernote.com", timeout=10)
        print(f"   ✅ Can reach Supernote website (status: {response.status_code})")
        
        # Test 2: Random code endpoint
        print("2️⃣ Testing API endpoint...")
        random_params = {
            "countryCode": "1", 
            "account": phone_number
        }
        
        response = requests.post(f"{base_url}/official/user/query/random/code", 
                               json=random_params, timeout=10)
        
        print(f"   Status code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            if data.get("success"):
                random_code = data.get("randomCode")
                print(f"   ✅ API responds correctly")
                print(f"   ✅ Random code received: {random_code[:8]}...")
                print(f"   ✅ Phone number format accepted")
                
                print("\n🎉 CONNECTION SUCCESSFUL!")
                print("\n📋 Ready for authentication:")
                print(f"   📱 Phone number: {phone_number}")
                print("   🔐 Password: (will be requested securely)")
                print("   🎯 Next step: Full authentication test")
                
                return True
            else:
                print(f"   ❌ API error: {data}")
        else:
            print(f"   ❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
    return False

if __name__ == "__main__":
    test_connection()