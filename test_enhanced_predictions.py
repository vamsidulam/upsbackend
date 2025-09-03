#!/usr/bin/env python3
"""
Test script for the enhanced predictions endpoint
"""

import requests
import json
from datetime import datetime

def test_enhanced_predictions():
    """Test the enhanced predictions endpoint"""
    
    print("🧪 Testing Enhanced Predictions Endpoint")
    print("=" * 50)
    
    # Test the enhanced predictions endpoint
    try:
        response = requests.get("http://localhost:8000/api/predictions/enhanced?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            
            print(f"✅ Enhanced predictions endpoint working!")
            print(f"📊 Found {len(predictions)} predictions")
            print()
            
            if predictions:
                print("🔮 Sample Enhanced Predictions:")
                print("-" * 30)
                
                for i, pred in enumerate(predictions[:3], 1):
                    print(f"\n{i}. UPS: {pred.get('ups_id', 'Unknown')}")
                    print(f"   Name: {pred.get('ups_name', 'Unknown')}")
                    print(f"   Failure Probability: {pred.get('probability_failure', 0):.1%}")
                    print(f"   Confidence: {pred.get('confidence', 0):.1%}")
                    print(f"   Risk Level: {pred.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                    print(f"   Timestamp: {pred.get('timestamp', 'Unknown')}")
                    
                    # Check if enhanced features are present
                    if 'risk_assessment' in pred:
                        risk = pred['risk_assessment']
                        if 'failure_reasons' in risk:
                            print(f"   Failure Reasons: {len(risk['failure_reasons'])} detailed reasons")
                        if 'technical_details' in risk:
                            tech = risk['technical_details']
                            print(f"   Technical Analysis: Battery {tech.get('battery_health')}%, Temp {tech.get('temperature_status')}°C")
            else:
                print("⚠️ No predictions found - this might be normal if no UPS data exists")
                
        else:
            print(f"❌ Enhanced predictions endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend server")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error testing enhanced predictions: {e}")
    
    print("\n" + "=" * 50)
    
    # Also test the basic predictions endpoint for comparison
    print("\n🧪 Testing Basic Predictions Endpoint (for comparison)")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/predictions?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            
            print(f"✅ Basic predictions endpoint working!")
            print(f"📊 Found {len(predictions)} predictions")
            
            if predictions:
                print("\n🔮 Sample Basic Predictions:")
                print("-" * 30)
                
                for i, pred in enumerate(predictions[:3], 1):
                    print(f"\n{i}. UPS: {pred.get('ups_id', 'Unknown')}")
                    print(f"   Name: {pred.get('ups_name', 'Unknown')}")
                    print(f"   Failure Probability: {pred.get('probability_failure', 0):.1%}")
                    print(f"   Confidence: {pred.get('confidence', 0):.1%}")
                    print(f"   Risk Level: {pred.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                    print(f"   Timestamp: {pred.get('timestamp', 'Unknown')}")
                    
                    # Check if enhanced features are present
                    if 'risk_assessment' in pred:
                        risk = pred['risk_assessment']
                        if 'failure_reasons' in risk:
                            print(f"   Failure Reasons: {len(risk['failure_reasons'])} detailed reasons")
                        if 'technical_details' in risk:
                            tech = risk['technical_details']
                            print(f"   Technical Analysis: Battery {tech.get('battery_health')}%, Temp {tech.get('temperature_status')}°C")
            else:
                print("⚠️ No predictions found - this might be normal if no UPS data exists")
                
        else:
            print(f"❌ Basic predictions endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend server")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error testing basic predictions: {e}")

if __name__ == "__main__":
    test_enhanced_predictions()
