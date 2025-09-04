#!/usr/bin/env python3
"""
Create diverse training data for ML model
"""

import random
from datetime import datetime, timedelta
from pymongo import MongoClient

def create_training_data():
    """Create diverse UPS data for ML training"""
    print("🔧 Creating diverse training data...")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["UPS_DATA_MONITORING"]
    collection = db["upsdata"]
    
    # Get existing UPS systems
    existing_ups = list(collection.find({}))
    
    if not existing_ups:
        print("❌ No UPS systems found")
        return
    
    print(f"📊 Found {len(existing_ups)} existing UPS systems")
    
    # Create diverse scenarios for training
    scenarios = [
        # Healthy scenarios
        {'status': 'healthy', 'batteryLevel': (80, 100), 'temperature': (20, 35), 'efficiency': (90, 98)},
        {'status': 'healthy', 'batteryLevel': (70, 85), 'temperature': (25, 40), 'efficiency': (85, 95)},
        
        # Warning scenarios
        {'status': 'warning', 'batteryLevel': (15, 25), 'temperature': (35, 45), 'efficiency': (80, 90)},
        {'status': 'warning', 'batteryLevel': (20, 30), 'temperature': (40, 50), 'efficiency': (75, 85)},
        
        # Failed scenarios
        {'status': 'failed', 'batteryLevel': (5, 15), 'temperature': (45, 55), 'efficiency': (70, 80)},
        {'status': 'failed', 'batteryLevel': (0, 10), 'temperature': (50, 60), 'efficiency': (65, 75)},
    ]
    
    # Update each UPS with diverse data
    for i, ups in enumerate(existing_ups):
        # Select a scenario (cycle through them)
        scenario = scenarios[i % len(scenarios)]
        
        # Generate data based on scenario
        battery = random.uniform(*scenario['batteryLevel'])
        temp = random.uniform(*scenario['temperature'])
        efficiency = random.uniform(*scenario['efficiency'])
        
        # Add some randomness
        battery += random.uniform(-5, 5)
        temp += random.uniform(-3, 3)
        efficiency += random.uniform(-2, 2)
        
        # Ensure values are within bounds
        battery = max(0, min(100, battery))
        temp = max(15, min(60, temp))
        efficiency = max(60, min(100, efficiency))
        
        # Update UPS with new data
        collection.update_one(
            {'_id': ups['_id']},
            {
                '$set': {
                    'status': scenario['status'],
                    'batteryLevel': round(battery, 2),
                    'temperature': round(temp, 2),
                    'efficiency': round(efficiency, 2),
                    'lastUpdate': datetime.now()
                }
            }
        )
        
        print(f"   • {ups['name']}: {scenario['status']} - Battery: {battery:.1f}%, Temp: {temp:.1f}°C, Eff: {efficiency:.1f}%")
    
    print(f"\n✅ Updated {len(existing_ups)} UPS systems with diverse training data")
    
    # Show final distribution
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    result = list(collection.aggregate(pipeline))
    print("\n📊 Final Status Distribution:")
    for item in result:
        print(f"   • {item['_id']}: {item['count']}")
    
    client.close()

if __name__ == "__main__":
    create_training_data()
