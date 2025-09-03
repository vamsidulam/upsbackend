#!/usr/bin/env python3
"""
Test the predictions API endpoint
"""
import requests

def test_predictions_api():
    try:
        print("🧪 Testing Predictions API...")
        print("=" * 40)
        
        # Test the predictions endpoint
        response = requests.get('http://localhost:8000/api/predictions')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"✅ API Working! Found {len(predictions)} predictions")
            
            if predictions:
                print("\n📋 First Prediction:")
                pred = predictions[0]
                print(f"   • UPS: {pred.get('ups_name', 'Unknown')}")
                print(f"   • Failure Probability: {pred.get('probability_failure', 0):.1%}")
                print(f"   • Risk Level: {pred.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_predictions_api()
