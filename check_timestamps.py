#!/usr/bin/env python3
"""
Check exact timestamps of recent predictions and UPS updates
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import os

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "UPS_DATA_MONITORING")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def check_timestamps():
    """Check exact timestamps of recent data"""
    
    print("⏰ Checking Data Timestamps")
    print("=" * 50)
    
    current_time = datetime.now()
    print(f"🕐 Current Time: {current_time}")
    print()
    
    try:
        # Check UPS data timestamps
        print("📊 UPS Data Timestamps:")
        print("-" * 30)
        ups_collection = db['upsdata']
        
        # Get latest UPS updates
        latest_ups = list(ups_collection.find().sort("lastUpdate", -1).limit(3))
        
        for i, ups in enumerate(latest_ups, 1):
            last_update = ups.get('lastUpdate')
            ups_id = ups.get('upsId', 'Unknown')
            
            if last_update:
                if isinstance(last_update, str):
                    try:
                        last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    except:
                        last_update = None
                
                if last_update:
                    time_diff = (current_time - last_update).total_seconds() / 60  # in minutes
                    print(f"{i}. UPS {ups_id}: {last_update} ({time_diff:.1f} minutes ago)")
                else:
                    print(f"{i}. UPS {ups_id}: Invalid timestamp format")
            else:
                print(f"{i}. UPS {ups_id}: No timestamp")
        
        print()
        
        # Check predictions timestamps
        print("🔮 ML Predictions Timestamps:")
        print("-" * 30)
        predictions_collection = db['ups_predictions']
        
        # Get latest predictions
        latest_predictions = list(predictions_collection.find().sort("timestamp", -1).limit(3))
        
        for i, pred in enumerate(latest_predictions, 1):
            timestamp = pred.get('timestamp')
            ups_id = pred.get('ups_id', 'Unknown')
            
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = None
                
                if timestamp:
                    time_diff = (current_time - timestamp).total_seconds() / 60  # in minutes
                    print(f"{i}. UPS {ups_id}: {timestamp} ({time_diff:.1f} minutes ago)")
                else:
                    print(f"{i}. UPS {ups_id}: Invalid timestamp format")
            else:
                print(f"{i}. UPS {ups_id}: No timestamp")
        
        print()
        
        # Check if services should be running
        print("🔍 Service Status Analysis:")
        print("-" * 30)
        
        # Check UPS updates (should be every 1 minute)
        if latest_ups:
            last_ups_update = latest_ups[0].get('lastUpdate')
            if last_ups_update and isinstance(last_ups_update, str):
                try:
                    last_ups_update = datetime.fromisoformat(last_ups_update.replace('Z', '+00:00'))
                    ups_time_diff = (current_time - last_ups_update).total_seconds() / 60
                    
                    if ups_time_diff <= 2:  # Within 2 minutes
                        print(f"✅ UPS Updates: ACTIVE (Last update: {ups_time_diff:.1f} minutes ago)")
                    else:
                        print(f"⚠️  UPS Updates: SLOW (Last update: {ups_time_diff:.1f} minutes ago)")
                except:
                    print("❌ UPS Updates: Cannot parse timestamp")
            else:
                print("❌ UPS Updates: No valid timestamp")
        
        # Check predictions (should be every 15 minutes)
        if latest_predictions:
            last_prediction = latest_predictions[0].get('timestamp')
            if last_prediction and isinstance(last_prediction, str):
                try:
                    last_prediction = datetime.fromisoformat(last_prediction.replace('Z', '+00:00'))
                    pred_time_diff = (current_time - last_prediction).total_seconds() / 60
                    
                    if pred_time_diff <= 20:  # Within 20 minutes
                        print(f"✅ ML Predictions: ACTIVE (Last prediction: {pred_time_diff:.1f} minutes ago)")
                    else:
                        print(f"⚠️  ML Predictions: SLOW (Last prediction: {pred_time_diff:.1f} minutes ago)")
                except:
                    print("❌ ML Predictions: Cannot parse timestamp")
            else:
                print("❌ ML Predictions: No valid timestamp")
        
        print()
        print("=" * 50)
        print("🎯 Timestamp Check Complete!")
        
    except Exception as e:
        print(f"❌ Error checking timestamps: {e}")

if __name__ == "__main__":
    check_timestamps()
