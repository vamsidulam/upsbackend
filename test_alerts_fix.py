#!/usr/bin/env python3
"""
Test script to verify alerts system is working correctly
"""

import requests
import json

def test_alerts_system():
    """Test the alerts system for consistency"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Alerts System Consistency")
    print("=" * 50)
    
    try:
        # Test 1: Dashboard Stats
        print("\n1. 📊 Testing Dashboard Stats...")
        response = requests.get(f"{base_url}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Dashboard Stats:")
            print(f"      Total UPS: {stats.get('totalUPS', 0)}")
            print(f"      Total Predictions: {stats.get('predictionsCount', 0)}")
            print(f"      Alerts Count: {stats.get('alertsCount', 0)}")
        else:
            print(f"   ❌ Failed to get dashboard stats: {response.status_code}")
            return
        
        # Test 2: Alerts Endpoint
        print("\n2. 🚨 Testing Alerts Endpoint...")
        response = requests.get(f"{base_url}/api/alerts?limit=50")
        if response.status_code == 200:
            alerts = response.json()
            alerts_count = len(alerts.get('alerts', []))
            print(f"   ✅ Alerts Endpoint:")
            print(f"      Alerts Returned: {alerts_count}")
            
            # Check if any healthy predictions are included
            healthy_count = 0
            for alert in alerts.get('alerts', []):
                if alert.get('probability_failure', 0) < 0.4:
                    healthy_count += 1
            
            if healthy_count == 0:
                print(f"      ✅ No healthy predictions included (correct)")
            else:
                print(f"      ⚠️  {healthy_count} healthy predictions included (incorrect)")
        else:
            print(f"   ❌ Failed to get alerts: {response.status_code}")
            return
        
        # Test 3: Alerts Count Endpoint
        print("\n3. 📈 Testing Alerts Count Endpoint...")
        response = requests.get(f"{base_url}/api/alerts/count")
        if response.status_code == 200:
            counts = response.json()
            print(f"   ✅ Alerts Count Endpoint:")
            total_alerts = 0
            for count in counts.get('counts', []):
                risk_level = count.get('risk_level', 'unknown')
                count_value = count.get('count', 0)
                total_alerts += count_value
                print(f"      {risk_level.capitalize()}: {count_value}")
            print(f"      Total Alerts: {total_alerts}")
        else:
            print(f"   ❌ Failed to get alerts count: {response.status_code}")
            return
        
        # Test 4: Consistency Check
        print("\n4. 🔍 Consistency Check...")
        dashboard_alerts = stats.get('alertsCount', 0)
        alerts_endpoint_count = alerts_count
        alerts_count_total = total_alerts
        
        print(f"   Dashboard Alerts Count: {dashboard_alerts}")
        print(f"   Alerts Endpoint Count: {alerts_endpoint_count}")
        print(f"   Alerts Count Total: {alerts_count_total}")
        
        if dashboard_alerts == alerts_endpoint_count == alerts_count_total:
            print("   ✅ All counts are consistent!")
        else:
            print("   ❌ Counts are inconsistent!")
            if dashboard_alerts != alerts_endpoint_count:
                print(f"      Dashboard vs Alerts Endpoint: {dashboard_alerts} != {alerts_endpoint_count}")
            if alerts_endpoint_count != alerts_count_total:
                print(f"      Alerts Endpoint vs Count Total: {alerts_endpoint_count} != {alerts_count_total}")
        
        # Test 5: Sample Alerts
        print("\n5. 📋 Sample Alerts (first 3)...")
        if alerts.get('alerts'):
            for i, alert in enumerate(alerts.get('alerts', [])[:3]):
                print(f"   Alert {i+1}:")
                print(f"      UPS: {alert.get('ups_id', 'Unknown')}")
                print(f"      Risk Level: {alert.get('risk_assessment', {}).get('risk_level', 'Unknown')}")
                print(f"      Failure Probability: {alert.get('probability_failure', 0):.1%}")
                print(f"      Status: {alert.get('status', 'Unknown')}")
                print()
        else:
            print("   No alerts found")
        
        print("=" * 50)
        print("🎯 Test Complete!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_alerts_system()
