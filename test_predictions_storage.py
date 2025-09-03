#!/usr/bin/env python3
"""
Test ML Predictions Storage and Retrieval
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.alert_service import AlertService

def test_predictions_storage():
    print("🧪 Testing ML Predictions Storage and Retrieval...")
    print("=" * 60)
    
    service = AlertService()
    
    # Create sample predictions
    sample_predictions = [
        {
            'ups_id': 'ups_001',
            'ups_name': 'Data Center Primary',
            'probability_failure': 0.94,
            'confidence': 0.92,
            'battery_level': 15,
            'temperature': 45,
            'efficiency': 85,
            'status': 'warning'
        },
        {
            'ups_id': 'ups_002',
            'ups_name': 'Network Equipment',
            'probability_failure': 0.87,
            'confidence': 0.89,
            'battery_level': 22,
            'temperature': 42,
            'efficiency': 88,
            'status': 'warning'
        },
        {
            'ups_id': 'ups_003',
            'ups_name': 'Emergency Systems',
            'probability_failure': 0.45,
            'confidence': 0.78,
            'battery_level': 65,
            'temperature': 35,
            'efficiency': 92,
            'status': 'healthy'
        }
    ]
    
    print("📝 Storing sample predictions...")
    if service.store_ml_predictions(sample_predictions):
        print("✅ Predictions stored successfully")
    else:
        print("❌ Failed to store predictions")
        return
    
    print("\n📊 Retrieving latest predictions...")
    predictions = service.get_latest_predictions(limit=10)
    
    if predictions:
        print(f"✅ Retrieved {len(predictions)} predictions")
        print("\n📋 Sample Prediction Structure:")
        for i, pred in enumerate(predictions[:2]):
            print(f"\n🔮 Prediction {i+1}:")
            print(f"   • UPS: {pred.get('ups_name', 'Unknown')}")
            print(f"   • Failure Probability: {pred.get('probability_failure', 0):.1%}")
            print(f"   • Confidence: {pred.get('confidence', 0):.1%}")
            print(f"   • Risk Level: {pred.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
            print(f"   • Timeframe: {pred.get('risk_assessment', {}).get('timeframe', 'Unknown')}")
            print(f"   • Battery: {pred.get('prediction_data', {}).get('battery_level', 'N/A')}%")
            print(f"   • Temperature: {pred.get('prediction_data', {}).get('temperature', 'N/A')}°C")
            print(f"   • Efficiency: {pred.get('prediction_data', {}).get('efficiency', 'N/A')}%")
            print(f"   • Risk Factors: {pred.get('risk_assessment', {}).get('failure_reasons', 'N/A')}")
    else:
        print("❌ No predictions retrieved")
    
    print("\n🎯 Testing API endpoint...")
    try:
        import requests
        response = requests.get("http://localhost:8000/api/predictions?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working - got {len(data.get('predictions', []))} predictions")
        else:
            print(f"❌ API endpoint failed: {response.status_code}")
    except ImportError:
        print("⚠️ requests module not available - skipping API test")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    test_predictions_storage()
