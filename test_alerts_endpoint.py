#!/usr/bin/env python3
"""
Test script for the alerts endpoint
"""

import requests
import json

def test_alerts_endpoint():
    """Test the alerts endpoint to see if it returns enhanced predictions"""
    try:
        print("🧪 Testing Alerts Endpoint...")
        print("=" * 50)
        
        # Test the alerts endpoint
        response = requests.get('http://localhost:8000/api/alerts?limit=5')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            
            print(f"✅ Alerts endpoint working!")
            print(f"📊 Found {len(alerts)} alerts")
            
            if alerts:
                print(f"\n🔮 Sample Alerts:")
                print("-" * 30)
                
                for i, alert in enumerate(alerts[:3]):
                    print(f"\n{i+1}. UPS: {alert.get('ups_name', 'Unknown')}")
                    print(f"   Failure Probability: {alert.get('probability_failure', 0):.1%}")
                    print(f"   Confidence: {alert.get('confidence', 0):.1%}")
                    print(f"   Risk Level: {alert.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                    
                    # Check for failure reasons
                    failure_reasons = alert.get('failure_reasons', [])
                    if failure_reasons:
                        print(f"   Failure Reasons: {len(failure_reasons)} detailed reasons")
                        print("   Sample reasons:")
                        for j, reason in enumerate(failure_reasons[:2]):
                            print(f"     {j+1}. {reason[:100]}...")
                    else:
                        print("   ❌ No failure reasons found")
                        
            else:
                print("⚠️ No alerts found")
                
        else:
            print(f"❌ Alerts endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running.")
    except Exception as e:
        print(f"❌ Error testing alerts endpoint: {e}")

if __name__ == "__main__":
    test_alerts_endpoint()
