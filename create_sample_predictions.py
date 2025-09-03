#!/usr/bin/env python3
"""
Create Sample ML Predictions for Testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.alert_service import AlertService
from datetime import datetime

def create_sample_predictions():
    print("🎯 Creating Sample ML Predictions...")
    print("=" * 50)
    
    service = AlertService()
    
    # Create realistic sample predictions
    sample_predictions = [
        {
            'ups_id': 'ups_001',
            'ups_name': 'Data Center Primary',
            'probability_failure': 0.94,
            'confidence': 0.92,
            'battery_level': 15,
            'temperature': 45,
            'efficiency': 85,
            'load': 95,
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
            'load': 88,
            'status': 'warning'
        },
        {
            'ups_id': 'ups_003',
            'ups_name': 'Emergency Systems',
            'probability_failure': 0.78,
            'confidence': 0.85,
            'battery_level': 18,
            'temperature': 38,
            'efficiency': 82,
            'load': 92,
            'status': 'warning'
        },
        {
            'ups_id': 'ups_004',
            'ups_name': 'Lab Equipment',
            'probability_failure': 0.65,
            'confidence': 0.78,
            'battery_level': 35,
            'temperature': 35,
            'efficiency': 87,
            'load': 85,
            'status': 'healthy'
        },
        {
            'ups_id': 'ups_005',
            'ups_name': 'Security Systems',
            'probability_failure': 0.45,
            'confidence': 0.72,
            'battery_level': 65,
            'temperature': 32,
            'efficiency': 92,
            'load': 78,
            'status': 'healthy'
        }
    ]
    
    print("📝 Storing sample predictions...")
    if service.store_ml_predictions(sample_predictions):
        print("✅ Sample predictions stored successfully")
        
        print("\n📊 Retrieving predictions to verify...")
        predictions = service.get_latest_predictions(limit=10)
        
        if predictions:
            print(f"✅ Retrieved {len(predictions)} predictions")
            print("\n🔮 Sample Prediction Details:")
            for i, pred in enumerate(predictions[:2]):
                print(f"\n📋 Prediction {i+1}:")
                print(f"   • UPS: {pred.get('ups_name', 'Unknown')}")
                print(f"   • Failure Probability: {pred.get('probability_failure', 0):.1%}")
                print(f"   • Confidence: {pred.get('confidence', 0):.1%}")
                print(f"   • Risk Level: {pred.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                print(f"   • Timeframe: {pred.get('risk_assessment', {}).get('timeframe', 'Unknown')}")
                print(f"   • Battery: {pred.get('prediction_data', {}).get('battery_level', 'N/A')}%")
                print(f"   • Temperature: {pred.get('prediction_data', {}).get('temperature', 'N/A')}°C")
                print(f"   • Efficiency: {pred.get('prediction_data', {}).get('efficiency', 'N/A')}%")
                print(f"   • Load: {pred.get('prediction_data', {}).get('load', 'N/A')}%")
                print(f"   • Risk Factors: {pred.get('risk_assessment', {}).get('failure_reasons', 'N/A')}")
        else:
            print("❌ No predictions retrieved")
    else:
        print("❌ Failed to store sample predictions")

if __name__ == "__main__":
    create_sample_predictions()
