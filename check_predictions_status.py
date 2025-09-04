#!/usr/bin/env python3
"""
Quick check for predictions generation status
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import os

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "UPS_DATA_MONITORING")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def check_predictions_status():
    """Check if predictions are being generated continuously"""
    
    print("🔮 Checking ML Predictions Status")
    print("=" * 50)
    
    try:
        # Check predictions collection
        predictions_collection = db['ups_predictions']
        
        # Get total predictions count
        total_predictions = predictions_collection.count_documents({})
        print(f"📊 Total Predictions in Database: {total_predictions}")
        
        if total_predictions == 0:
            print("❌ No predictions found in database")
            return
        
        # Get latest predictions
        latest_predictions = list(predictions_collection.find().sort("timestamp", -1).limit(5))
        
        print(f"\n📅 Latest 5 Predictions:")
        print("-" * 40)
        
        for i, pred in enumerate(latest_predictions, 1):
            timestamp = pred.get('timestamp', 'Unknown')
            ups_id = pred.get('ups_id', 'Unknown')
            prob_failure = pred.get('probability_failure', 0)
            risk_level = pred.get('risk_assessment', {}).get('risk_level', 'Unknown')
            
            print(f"{i}. UPS: {ups_id}")
            print(f"   Risk Level: {risk_level}")
            print(f"   Failure Probability: {prob_failure:.1%}")
            print(f"   Timestamp: {timestamp}")
            print()
        
        # Check predictions in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_predictions = predictions_collection.count_documents({
            "timestamp": {"$gte": one_hour_ago.isoformat()}
        })
        
        print(f"⏰ Predictions in Last Hour: {recent_predictions}")
        
        # Check predictions in last 15 minutes
        fifteen_min_ago = datetime.now() - timedelta(minutes=15)
        very_recent_predictions = predictions_collection.count_documents({
            "timestamp": {"$gte": fifteen_min_ago.isoformat()}
        })
        
        print(f"⏰ Predictions in Last 15 Minutes: {very_recent_predictions}")
        
        # Calculate expected predictions per hour (4 per hour = every 15 minutes)
        expected_per_hour = 4
        if recent_predictions >= expected_per_hour:
            print(f"✅ Predictions generation: ACTIVE (Expected: {expected_per_hour}, Found: {recent_predictions})")
        else:
            print(f"⚠️  Predictions generation: SLOW (Expected: {expected_per_hour}, Found: {recent_predictions})")
        
        # Check if continuous predictions service is running
        print(f"\n🔍 Continuous Predictions Service Status:")
        print("-" * 40)
        
        # Check if there are predictions with timestamps close to each other (indicating continuous service)
        if total_predictions > 1:
            # Get timestamps of last 10 predictions
            recent_timestamps = list(predictions_collection.find(
                {}, {"timestamp": 1}
            ).sort("timestamp", -1).limit(10))
            
            if len(recent_timestamps) > 1:
                # Check time intervals between predictions
                intervals = []
                for j in range(len(recent_timestamps) - 1):
                    try:
                        time1 = datetime.fromisoformat(recent_timestamps[j]['timestamp'].replace('Z', '+00:00'))
                        time2 = datetime.fromisoformat(recent_timestamps[j+1]['timestamp'].replace('Z', '+00:00'))
                        interval = abs((time1 - time2).total_seconds() / 60)  # in minutes
                        intervals.append(interval)
                    except:
                        continue
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"   Average interval between predictions: {avg_interval:.1f} minutes")
                    
                    if avg_interval <= 20:  # Allow some variance
                        print("   ✅ Continuous predictions service appears to be running")
                    else:
                        print("   ⚠️  Predictions intervals are longer than expected")
        
        print("\n" + "=" * 50)
        print("🎯 Predictions Status Check Complete!")
        
    except Exception as e:
        print(f"❌ Error checking predictions: {e}")

if __name__ == "__main__":
    check_predictions_status()
