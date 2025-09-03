#!/usr/bin/env python3
"""
Quick script to check current UPS status and data updates
"""

from pymongo import MongoClient
from datetime import datetime

def check_current_status():
    """Check current UPS status and data"""
    
    try:
        # Connect to MongoDB
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
        db = client['UPS_DATA_MONITORING']
        collection = db['upsdata']
        
        print("🔍 Current UPS Status Check")
        print("=" * 50)
        
        # Get all UPS systems
        ups_systems = list(collection.find({}))
        
        if not ups_systems:
            print("❌ No UPS systems found in database")
            return
        
        print(f"📊 Found {len(ups_systems)} UPS systems")
        print()
        
        # Check status counts
        status_counts = {}
        for ups in ups_systems:
            status = ups.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("📈 Current Status Counts:")
        print("-" * 30)
        for status, count in status_counts.items():
            print(f"  {status.capitalize()}: {count}")
        
        print()
        print("📋 Detailed UPS Information:")
        print("-" * 30)
        
        # Show first 5 UPS systems
        for i, ups in enumerate(ups_systems[:5]):
            print(f"\n{i+1}. UPS: {ups.get('name', 'Unknown')}")
            print(f"   ID: {ups.get('upsId', 'Unknown')}")
            print(f"   Status: {ups.get('status', 'Unknown')}")
            print(f"   Battery: {ups.get('batteryLevel', 'Unknown')}%")
            print(f"   Temperature: {ups.get('temperature', 'Unknown')}°C")
            print(f"   Power Input: {ups.get('powerInput', 'Unknown')}W")
            print(f"   Power Output: {ups.get('powerOutput', 'Unknown')}W")
            print(f"   Last Update: {ups.get('lastUpdate', 'Unknown')}")
            print(f"   Last Checked: {ups.get('lastChecked', 'Unknown')}")
        
        if len(ups_systems) > 5:
            print(f"\n... and {len(ups_systems) - 5} more UPS systems")
        
        # Check if data is recent
        print("\n⏰ Data Freshness Check:")
        print("-" * 30)
        
        current_time = datetime.now()
        recent_updates = 0
        
        for ups in ups_systems:
            last_update = ups.get('lastUpdate')
            if last_update:
                if isinstance(last_update, str):
                    try:
                        last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    except:
                        continue
                
                time_diff = current_time - last_update
                if time_diff.total_seconds() < 600:  # Less than 10 minutes
                    recent_updates += 1
        
        print(f"  UPS with recent updates (< 10 min): {recent_updates}/{len(ups_systems)}")
        
        if recent_updates == 0:
            print("  ⚠️  No recent updates detected!")
            print("  💡 UPS monitoring service may not be updating data")
        elif recent_updates < len(ups_systems):
            print("  ⚠️  Some UPS systems have outdated data")
        else:
            print("  ✅ All UPS systems have recent data")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_current_status()
