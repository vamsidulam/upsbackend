#!/usr/bin/env python3
"""
Test script to verify ObjectId serialization fix in /api/alerts endpoint
"""

import requests
import json

def test_alerts_endpoint():
    """Test the /api/alerts endpoint for ObjectId serialization issues"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing ObjectId Serialization Fix")
    print("=" * 50)
    
    try:
        # Test 1: Check if backend is running
        print("\n1. 🔌 Testing Backend Connection...")
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Backend is running")
            else:
                print(f"   ❌ Backend health check failed: {response.status_code}")
                return
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Cannot connect to backend: {e}")
            print("   💡 Make sure your backend is running with: uvicorn main:app --host 0.0.0.0 --port 8000")
            return
        
        # Test 2: Test /api/alerts endpoint
        print("\n2. 🚨 Testing /api/alerts Endpoint...")
        try:
            response = requests.get(f"{base_url}/api/alerts?limit=10&latest_only=true", timeout=10)
            if response.status_code == 200:
                print("   ✅ /api/alerts endpoint responded successfully")
                
                # Try to parse JSON response
                try:
                    data = response.json()
                    alerts = data.get('alerts', [])
                    print(f"   📊 Found {len(alerts)} alerts")
                    
                    # Check if response contains any ObjectId errors
                    if alerts:
                        first_alert = alerts[0]
                        print(f"   🔍 Sample alert structure:")
                        print(f"      - _id: {type(first_alert.get('_id'))} = {first_alert.get('_id')}")
                        print(f"      - ups_id: {type(first_alert.get('ups_id'))} = {first_alert.get('ups_id')}")
                        print(f"      - probability_failure: {first_alert.get('probability_failure')}")
                        
                        # Check if _id is a string (not ObjectId)
                        if isinstance(first_alert.get('_id'), str):
                            print("   ✅ ObjectId serialization working correctly")
                        else:
                            print("   ❌ ObjectId still not serialized correctly")
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing failed: {e}")
                    print(f"   📄 Response content: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ /api/alerts endpoint failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        # Test 3: Test /api/alerts/count endpoint
        print("\n3. 📈 Testing /api/alerts/count Endpoint...")
        try:
            response = requests.get(f"{base_url}/api/alerts/count", timeout=10)
            if response.status_code == 200:
                print("   ✅ /api/alerts/count endpoint responded successfully")
                
                try:
                    data = response.json()
                    counts = data.get('counts', [])
                    print(f"   📊 Found {len(counts)} risk level counts")
                    
                    for count in counts:
                        risk_level = count.get('risk_level', 'unknown')
                        count_value = count.get('count', 0)
                        print(f"      {risk_level.capitalize()}: {count_value}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing failed: {e}")
                    
            else:
                print(f"   ❌ /api/alerts/count endpoint failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 ObjectId Serialization Test Complete!")
        
        # Summary
        print("\n📋 Summary:")
        print("   - If you see '✅ ObjectId serialization working correctly', the fix is working")
        print("   - If you see '❌ ObjectId still not serialized correctly', there's still an issue")
        print("   - If you see connection errors, make sure your backend is running")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_alerts_endpoint()
