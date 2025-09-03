#!/usr/bin/env python3
"""
Check alert count inconsistency between dashboard and alerts page
"""

from pymongo import MongoClient
import os

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "UPS_DATA_MONITORING")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def check_alert_inconsistency():
    """Check why dashboard and alerts page show different counts"""
    
    print("🔍 Checking Alert Count Inconsistency")
    print("=" * 50)
    
    try:
        # Check stored predictions collection
        predictions_collection = db['ups_predictions']
        
        # Count all predictions with probability_failure >= 0.4 (what dashboard counts)
        dashboard_alerts = predictions_collection.count_documents({"probability_failure": {"$gte": 0.4}})
        total_predictions = predictions_collection.count_documents({})
        
        print(f"📊 Stored Predictions Analysis:")
        print(f"   Total predictions in database: {total_predictions}")
        print(f"   Predictions with failure probability >= 0.4: {dashboard_alerts}")
        print()
        
        # Check what the dashboard is actually counting
        print("🔍 Dashboard Count Analysis:")
        print("-" * 30)
        
        # Get all predictions with failure probability >= 0.4
        dashboard_predictions = list(predictions_collection.find({"probability_failure": {"$gte": 0.4}}))
        
        if dashboard_predictions:
            print(f"   Found {len(dashboard_predictions)} predictions that dashboard counts as alerts:")
            print()
            
            for i, pred in enumerate(dashboard_predictions[:5], 1):  # Show first 5
                ups_id = pred.get('ups_id', 'Unknown')
                prob_failure = pred.get('probability_failure', 0)
                risk_level = pred.get('risk_assessment', {}).get('risk_level', 'Unknown')
                timestamp = pred.get('timestamp', 'Unknown')
                
                print(f"   {i}. UPS: {ups_id}")
                print(f"      Failure Probability: {prob_failure:.1%}")
                print(f"      Risk Level: {risk_level}")
                print(f"      Timestamp: {timestamp}")
                print()
            
            if len(dashboard_predictions) > 5:
                print(f"   ... and {len(dashboard_predictions) - 5} more predictions")
                print()
        
        # Check what the alerts endpoint would generate
        print("🔍 Alerts Endpoint Analysis:")
        print("-" * 30)
        
        # Get current UPS data to see what would be generated
        ups_collection = db['upsdata']
        current_ups_count = ups_collection.count_documents({})
        
        print(f"   Current UPS systems: {current_ups_count}")
        print(f"   Alerts endpoint generates real-time predictions for current UPS data")
        print(f"   Dashboard counts stored predictions from database")
        print()
        
        # Check if there are old predictions that shouldn't be counted
        print("🔍 Potential Issues:")
        print("-" * 30)
        
        # Check for predictions with very old timestamps
        from datetime import datetime, timedelta
        one_day_ago = datetime.now() - timedelta(days=1)
        
        old_predictions = predictions_collection.count_documents({
            "probability_failure": {"$gte": 0.4},
            "timestamp": {"$lt": one_day_ago.isoformat()}
        })
        
        if old_predictions > 0:
            print(f"   ⚠️  {old_predictions} old predictions (older than 1 day) are being counted")
            print(f"      These might be outdated and shouldn't be shown as current alerts")
        
        # Check for duplicate predictions per UPS
        from collections import defaultdict
        ups_prediction_counts = defaultdict(int)
        
        for pred in dashboard_predictions:
            ups_id = pred.get('ups_id', 'Unknown')
            ups_prediction_counts[ups_id] += 1
        
        duplicate_ups = {ups_id: count for ups_id, count in ups_prediction_counts.items() if count > 1}
        
        if duplicate_ups:
            print(f"   ⚠️  {len(duplicate_ups)} UPS systems have multiple predictions:")
            for ups_id, count in duplicate_ups.items():
                print(f"      {ups_id}: {count} predictions")
        
        print()
        print("🎯 Summary:")
        print("-" * 30)
        print(f"   Dashboard shows: {dashboard_alerts} alerts (from stored predictions)")
        print(f"   Alerts page shows: 2 alerts (from real-time generation)")
        print(f"   The difference is because:")
        print(f"      - Dashboard counts ALL stored predictions with failure probability >= 0.4")
        print(f"      - Alerts page generates fresh predictions only for current UPS data")
        print(f"      - Some stored predictions might be outdated or for UPS systems no longer active")
        
        print()
        print("💡 Recommendation:")
        print("   Update dashboard to use the same logic as alerts page:")
        print("   - Generate real-time predictions instead of counting stored ones")
        print("   - Or filter stored predictions to only include recent/active ones")
        
        print("\n" + "=" * 50)
        print("🎯 Alert Inconsistency Check Complete!")
        
    except Exception as e:
        print(f"❌ Error checking alert inconsistency: {e}")

if __name__ == "__main__":
    check_alert_inconsistency()
