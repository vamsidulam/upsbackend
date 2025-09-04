#!/usr/bin/env python3
"""
Check ML prediction alerts structure
"""

from pymongo import MongoClient

def check_ml_alerts():
    print("🔍 Checking ML Prediction Alerts...")
    print("=" * 50)
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["UPS_DATA_MONITORING"]
    
    # Get ML prediction alerts
    pipeline = [
        {"$unwind": "$alerts"},
        {"$match": {"alerts.type": "ml_prediction"}},
        {"$limit": 3}
    ]
    
    alerts = list(db.upsdata.aggregate(pipeline))
    
    if not alerts:
        print("❌ No ML prediction alerts found")
        return
    
    print(f"✅ Found {len(alerts)} ML prediction alerts")
    print()
    
    for i, alert_doc in enumerate(alerts):
        alert = alert_doc["alerts"]
        print(f"📋 Alert {i+1}:")
        print(f"   • Title: {alert.get('title', 'N/A')}")
        print(f"   • Message: {alert.get('message', 'N/A')}")
        print(f"   • Severity: {alert.get('severity', 'N/A')}")
        print(f"   • Risk Category: {alert.get('risk_category', 'N/A')}")
        print(f"   • Primary Risk: {alert.get('primary_risk', 'N/A')}")
        print(f"   • Timeframe: {alert.get('prediction_timeframe', 'N/A')}")
        print(f"   • Recommended Action: {alert.get('recommended_action', 'N/A')}")
        print(f"   • Failure Reasons: {alert.get('failure_reasons', 'N/A')}")
        print(f"   • Confidence: {alert.get('confidence', 'N/A')}")
        print()
    
    client.close()

if __name__ == "__main__":
    check_ml_alerts()
