#!/usr/bin/env python3
"""
Debug script for the alerts endpoint
"""

import requests
import json

def debug_alerts_endpoint():
    """Debug the alerts endpoint to see the exact data structure"""
    try:
        print("🔍 Debugging Alerts Endpoint...")
        print("=" * 50)
        
        # Test the alerts endpoint
        response = requests.get('http://localhost:8000/api/alerts?limit=2')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            
            print(f"✅ Alerts endpoint working!")
            print(f"📊 Found {len(alerts)} alerts")
            
            # Show the complete structure of the first alert
            if alerts:
                print("\n🔍 Complete structure of first alert:")
                print(json.dumps(alerts[0], indent=2))
                
                # Check specific fields
                print(f"\n📋 Field Analysis:")
                print(f"• _id: {alerts[0].get('_id')}")
                print(f"• ups_id: {alerts[0].get('ups_id')}")
                print(f"• ups_name: {alerts[0].get('ups_name')}")
                print(f"• probability_failure: {alerts[0].get('probability_failure')}")
                print(f"• failure_reasons: {alerts[0].get('failure_reasons')}")
                print(f"• risk_assessment: {alerts[0].get('risk_assessment')}")
                
                # Check if failure_reasons exists in risk_assessment
                risk_assessment = alerts[0].get('risk_assessment', {})
                if risk_assessment:
                    print(f"• risk_assessment.failure_reasons: {risk_assessment.get('failure_reasons')}")
                    print(f"• risk_assessment.risk_level: {risk_assessment.get('risk_level')}")
                    print(f"• risk_assessment.timeframe: {risk_assessment.get('timeframe')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing alerts endpoint: {e}")

if __name__ == "__main__":
    debug_alerts_endpoint()
