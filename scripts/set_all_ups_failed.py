#!/usr/bin/env python3
"""
Set some UPS systems to failed status for realistic testing
This script sets 1-2 UPS systems to failed while keeping others healthy
"""

import os
import sys
import random
from datetime import datetime
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()
# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def set_some_ups_failed():
    """Set 1-2 UPS systems to failed status for realistic testing"""
    print("🔧 Setting some UPS systems to failed status for realistic testing...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client["UPS_DATA_MONITORING"]
        collection = db["upsdata"]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Get all UPS systems
        cursor = collection.find({})
        ups_systems = list(cursor)
        
        if not ups_systems:
            print("⚠️ No UPS systems found in database")
            client.close()
            return False
        
        print(f"📊 Found {len(ups_systems)} UPS systems")
        
        # Randomly select 1-2 UPS systems to fail
        num_to_fail = random.randint(1, 2)
        ups_to_fail = random.sample(ups_systems, num_to_fail)
        
        print(f"🎯 Setting {num_to_fail} UPS system(s) to failed status")
        
        # Set selected UPS systems to failed
        for ups in ups_to_fail:
            collection.update_one(
                {'_id': ups['_id']},
                {
                    '$set': {
                        'status': 'failed',
                        'batteryLevel': random.randint(5, 15),  # Very low battery
                        'temperature': random.randint(42, 48),  # High temperature
                        'efficiency': random.randint(82, 88),   # Low efficiency
                        'lastUpdate': datetime.now()
                    }
                }
            )
            print(f"   • {ups['name']} set to FAILED status")
        
        # Set remaining UPS systems to healthy with good values
        remaining_ups = [u for u in ups_systems if u not in ups_to_fail]
        for ups in remaining_ups:
            collection.update_one(
                {'_id': ups['_id']},
                {
                    '$set': {
                        'status': 'healthy',
                        'batteryLevel': random.randint(75, 95),  # Good battery
                        'temperature': random.randint(22, 32),   # Normal temperature
                        'efficiency': random.randint(92, 98),    # Good efficiency
                        'lastUpdate': datetime.now()
                    }
                }
            )
            print(f"   • {ups['name']} set to HEALTHY status")
        
        # Display final status
        print(f"\n📊 Final UPS Status:")
        final_cursor = collection.find({})
        failed_count = 0
        healthy_count = 0
        
        for ups in final_cursor:
            if ups['status'] == 'failed':
                failed_count += 1
                print(f"   🔴 {ups['name']} - FAILED - Battery: {ups['batteryLevel']}%")
            else:
                healthy_count += 1
                print(f"   🟢 {ups['name']} - HEALTHY - Battery: {ups['batteryLevel']}%")
        
        print(f"\n📈 Summary: {healthy_count} healthy, {failed_count} failed")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error updating UPS systems: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Realistic UPS Status Update Script")
    print("=" * 50)
    
    success = set_some_ups_failed()
    
    if success:
        print("\n🎉 UPS systems updated with realistic failure scenario!")
        print("💡 This creates a more realistic testing environment")
    else:
        print("\n❌ Failed to update UPS systems")
        sys.exit(1)

if __name__ == "__main__":
    main()
