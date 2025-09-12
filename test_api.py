#!/usr/bin/env python3
"""
Test script for Video Extractor API
Run this to test the API locally before deployment
"""

import requests
import time
import json

def test_api(base_url="http://localhost:5000"):
    """Test the video extractor API"""
    
    print("🧪 Testing Video Extractor API")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print()
    
    # Test 1: Health check
    print("1️⃣ Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    print()
    
    # Test 2: API documentation
    print("2️⃣ Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/?format=json")
        if response.status_code == 200:
            print("✅ API documentation accessible")
            data = response.json()
            print(f"   API Name: {data['name']}")
            print(f"   Version: {data['version']}")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API documentation error: {e}")
    print()
    
    # Test 3: Extract sources (using a test URL)
    print("3️⃣ Testing source extraction...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    try:
        response = requests.post(f"{base_url}/extract", 
                               json={"url": test_url},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Source extraction successful")
                print(f"   Sources found: {data['sources_found']}")
                if data['sources']:
                    source = data['sources'][0]
                    print(f"   Best source: {source['quality']}p {source['format']} via {source['method']}")
            else:
                print(f"⚠️ Source extraction returned no sources")
                print(f"   Response: {data}")
        else:
            print(f"❌ Source extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Source extraction error: {e}")
    print()
    
    # Test 4: Download (only if extraction worked)
    print("4️⃣ Testing download initiation...")
    try:
        response = requests.post(f"{base_url}/download",
                               json={"url": test_url, "quality": "worst"},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                download_id = data['download_id']
                print("✅ Download initiated successfully")
                print(f"   Download ID: {download_id}")
                print(f"   Selected quality: {data['selected_source']['quality']}p")
                
                # Test 5: Status checking
                print("\n5️⃣ Testing status checking...")
                for i in range(5):  # Check status 5 times
                    time.sleep(2)
                    status_response = requests.get(f"{base_url}/status/{download_id}")
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"   Status check {i+1}: {status['status']} - {status.get('progress', 0):.1f}%")
                        
                        if status['status'] in ['completed', 'failed', 'cancelled']:
                            break
                    else:
                        print(f"   Status check {i+1} failed: {status_response.status_code}")
                
                # Test 6: Cancel download (if still running)
                if status.get('status') == 'downloading':
                    print("\n6️⃣ Testing download cancellation...")
                    cancel_response = requests.post(f"{base_url}/cancel/{download_id}")
                    if cancel_response.status_code == 200:
                        print("✅ Download cancellation successful")
                    else:
                        print(f"❌ Download cancellation failed: {cancel_response.status_code}")
                
            else:
                print(f"⚠️ Download initiation failed")
                print(f"   Response: {data}")
        else:
            print(f"❌ Download initiation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Download test error: {e}")
    print()
    
    print("🏁 API testing completed!")
    print("\n💡 If all tests passed, your API is ready for deployment!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    test_api(base_url)