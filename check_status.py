#!/usr/bin/env python3
"""
Check UPS status distribution
"""

from pymongo import MongoClient

def check_status():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    db = client["UPS_DATA_MONITORING"]
    
    # Count by status
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    result = list(db.upsdata.aggregate(pipeline))
    
    print("📊 UPS Status Distribution:")
    for item in result:
        print(f"   • {item['_id']}: {item['count']}")
    
    # Count total alerts
    pipeline = [
        {"$unwind": "$alerts"},
        {"$group": {"_id": None, "total": {"$sum": 1}}}
    ]
    
    result = list(db.upsdata.aggregate(pipeline))
    total_alerts = result[0]["total"] if result else 0
    
    print(f"\n🚨 Total Alerts: {total_alerts}")
    
    client.close()

if __name__ == "__main__":
    check_status()
