#!/usr/bin/env python3
"""
Check all alerts for data integrity
"""

from pymongo import MongoClient

def check_all_alerts():
    print("🔍 Checking All Alerts for Data Integrity...")
    print("=" * 60)
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["UPS_DATA_MONITORING"]
    
    # Get all alerts
    pipeline = [
        {"$unwind": "$alerts"},
        {"$group": {"_id": "$alerts.type", "count": {"$sum": 1}}}
    ]
    
    type_counts = list(db.upsdata.aggregate(pipeline))
    print("📊 Alert Type Distribution:")
    for item in type_counts:
        print(f"   • {item['_id']}: {item['count']}")
    
    print()
    
    # Check for alerts with missing critical fields
    pipeline = [
        {"$unwind": "$alerts"},
        {"$match": {
            "$or": [
                {"alerts.failure_reasons": {"$exists": False}},
                {"alerts.risk_category": {"$exists": False}},
                {"alerts.primary_risk": {"$exists": False}},
                {"alerts.prediction_timeframe": {"$exists": False}},
                {"alerts.recommended_action": {"$exists": False}}
            ]
        }}
    ]
    
    problematic_alerts = list(db.upsdata.aggregate(pipeline))
    
    if problematic_alerts:
        print("⚠️ Found alerts with missing critical fields:")
        for alert_doc in problematic_alerts:
            alert = alert_doc["alerts"]
            print(f"   • UPS: {alert.get('ups_name', 'Unknown')}")
            print(f"     Type: {alert.get('type', 'Unknown')}")
            print(f"     Missing fields:")
            if 'failure_reasons' not in alert:
                print(f"       - failure_reasons")
            if 'risk_category' not in alert:
                print(f"       - risk_category")
            if 'primary_risk' not in alert:
                print(f"       - primary_risk")
            if 'prediction_timeframe' not in alert:
                print(f"       - prediction_timeframe")
            if 'recommended_action' not in alert:
                print(f"       - recommended_action")
            print()
    else:
        print("✅ All alerts have complete data")
    
    # Check for alerts with empty or null values
    pipeline = [
        {"$unwind": "$alerts"},
        {"$match": {
            "$or": [
                {"alerts.failure_reasons": []},
                {"alerts.failure_reasons": None},
                {"alerts.risk_category": ""},
                {"alerts.risk_category": None},
                {"alerts.primary_risk": ""},
                {"alerts.primary_risk": None}
            ]
        }}
    ]
    
    empty_alerts = list(db.upsdata.aggregate(pipeline))
    
    if empty_alerts:
        print("⚠️ Found alerts with empty/null values:")
        for alert_doc in empty_alerts:
            alert = alert_doc["alerts"]
            print(f"   • UPS: {alert.get('ups_name', 'Unknown')}")
            print(f"     Type: {alert.get('type', 'Unknown')}")
            print(f"     Empty fields:")
            if not alert.get('failure_reasons'):
                print(f"       - failure_reasons: {alert.get('failure_reasons')}")
            if not alert.get('risk_category'):
                print(f"       - risk_category: {alert.get('risk_category')}")
            if not alert.get('primary_risk'):
                print(f"       - primary_risk: {alert.get('primary_risk')}")
            print()
    else:
        print("✅ All alerts have non-empty values")
    
    client.close()

if __name__ == "__main__":
    check_all_alerts()
