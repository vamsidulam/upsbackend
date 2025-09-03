#!/usr/bin/env python3
"""
Test script to verify the predictions API endpoint
"""

import requests
import json
from datetime import datetime

def test_predictions_api():
    """Test the predictions API endpoint"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Predictions API Endpoint")
    print("=" * 50)
    
    try:
        # Test 1: Check if backend is running
        print("1️⃣ Testing backend connectivity...")
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
            return False
        
        # Test 2: Test predictions endpoint
        print("\n2️⃣ Testing predictions endpoint...")
        response = requests.get(f"{base_url}/api/predictions", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"✅ Predictions endpoint working!")
            print(f"📊 Retrieved {len(predictions)} predictions")
            
            if predictions:
                print("\n🔍 Sample prediction data:")
                sample = predictions[0]
                print(f"   UPS ID: {sample.get('ups_id', 'N/A')}")
                print(f"   UPS Name: {sample.get('ups_name', 'N/A')}")
                print(f"   Failure Probability: {sample.get('probability_failure', 'N/A')}")
                print(f"   Confidence: {sample.get('confidence', 'N/A')}")
                print(f"   Timestamp: {sample.get('timestamp', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ Predictions endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_ups_data_api():
    """Test the UPS data API endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing UPS Data API Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/ups", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ups_data = data.get('ups_data', [])
            print(f"✅ UPS data endpoint working!")
            print(f"📊 Retrieved {len(ups_data)} UPS records")
            
            if ups_data:
                print("\n🔍 Sample UPS data:")
                sample = ups_data[0]
                print(f"   UPS ID: {sample.get('ups_id', 'N/A')}")
                print(f"   UPS Name: {sample.get('ups_name', 'N/A')}")
                print(f"   Status: {sample.get('status', 'N/A')}")
                print(f"   Battery Level: {sample.get('battery_level', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ UPS data endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UPS data endpoint: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 UPS Monitoring System - API Test Suite")
    print("=" * 60)
    
    # Test predictions API
    predictions_working = test_predictions_api()
    
    # Test UPS data API
    ups_data_working = test_ups_data_api()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"🔮 Predictions API: {'✅ WORKING' if predictions_working else '❌ FAILED'}")
    print(f"📊 UPS Data API: {'✅ WORKING' if ups_data_working else '❌ FAILED'}")
    
    if predictions_working and ups_data_working:
        print("\n🎉 All API endpoints are working correctly!")
        print("🌐 Frontend should be able to fetch data successfully")
    else:
        print("\n⚠️ Some API endpoints are not working")
        print("🔧 Check backend logs for more details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
