#!/usr/bin/env python3
"""
Create 12 UPS systems in the database
This script creates initial UPS data for the monitoring system
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

def create_ups_systems():
    """Create 12 UPS systems in MongoDB"""
    print("🔧 Creating 12 UPS systems...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client["UPS_DATA_MONITORING"]
        collection = db["upsdata"]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Check if UPS systems already exist
        existing_count = collection.count_documents({})
        if existing_count >= 12:
            print(f"✅ {existing_count} UPS systems already exist")
            client.close()
            return True
        
        # Create 12 UPS systems
        ups_systems = []
        for i in range(12):
            ups_system = {
                'name': f'UPS-{i+1:02d}',
                'location': f'Datacenter-{((i % 3) + 1)}',
                'capacity': random.randint(1000, 5000),
                'criticalLoad': random.randint(500, 2500),
                'status': 'healthy',
                'batteryLevel': random.randint(80, 100),
                'temperature': random.randint(20, 35),
                'efficiency': random.randint(90, 98),
                'uptime': random.randint(95, 100),
                'powerInput': random.randint(800, 4500),
                'powerOutput': random.randint(600, 4000),
                'lastUpdate': datetime.now(),
                'performanceHistory': []
            }
            ups_systems.append(ups_system)
        
        # Insert UPS systems
        result = collection.insert_many(ups_systems)
        print(f"✅ Created {len(result.inserted_ids)} UPS systems")
        
        # Display created systems
        print("\n📊 Created UPS Systems:")
        for ups in ups_systems:
            print(f"   • {ups['name']} - {ups['location']} - {ups['status']}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating UPS systems: {e}")
        return False

def main():
    """Main function"""
    print("🚀 UPS System Creation Script")
    print("=" * 40)
    
    success = create_ups_systems()
    
    if success:
        print("\n🎉 UPS systems created successfully!")
    else:
        print("\n❌ Failed to create UPS systems")
        sys.exit(1)

if __name__ == "__main__":
    main()
