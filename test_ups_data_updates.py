#!/usr/bin/env python3
"""
Test script to verify UPS data updates every 5 minutes
"""

import requests
import json
import time
from datetime import datetime
from pymongo import MongoClient

def test_ups_data_updates():
    """Test if UPS data is being updated"""
    
    print("🧪 Testing UPS Data Updates")
    print("=" * 50)
    
    # Connect to MongoDB
    try:
        client = MongoClient("mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/")
        db = client["UPS_DATA_MONITORING"]
        collection = db["upsdata"]
        
        print("✅ Connected to MongoDB")
        
        # Get initial UPS data
        print("\n📊 Initial UPS Data:")
        print("-" * 30)
        
        initial_data = list(collection.find({}, {'name': 1, 'status': 1, 'batteryLevel': 1, 'temperature': 1, 'lastUpdate': 1}))
        
        for ups in initial_data:
            print(f"UPS: {ups.get('name', 'Unknown')}")
            print(f"  Status: {ups.get('status', 'Unknown')}")
            print(f"  Battery: {ups.get('batteryLevel', 'Unknown')}%")
            print(f"  Temperature: {ups.get('temperature', 'Unknown')}°C")
            print(f"  Last Update: {ups.get('lastUpdate', 'Unknown')}")
            print()
        
        # Monitor for changes
        print("🔍 Monitoring for UPS data changes...")
        print("   (This will run for 10 minutes to catch updates)")
        print("   Press Ctrl+C to stop early")
        print("-" * 30)
        
        start_time = datetime.now()
        check_interval = 60  # Check every minute
        total_checks = 10
        
        for check_num in range(total_checks):
            try:
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds() / 60
                
                print(f"\n⏰ Check {check_num + 1}/{total_checks} at {current_time.strftime('%H:%M:%S')} (Elapsed: {elapsed:.1f} min)")
                
                # Get current UPS data
                current_data = list(collection.find({}, {'name': 1, 'status': 1, 'batteryLevel': 1, 'temperature': 1, 'lastUpdate': 1}))
                
                changes_detected = False
                
                for i, current_ups in enumerate(current_data):
                    initial_ups = initial_data[i]
                    
                    # Check for changes
                    if (current_ups.get('status') != initial_ups.get('status') or
                        current_ups.get('batteryLevel') != initial_ups.get('batteryLevel') or
                        current_ups.get('temperature') != initial_ups.get('temperature')):
                        
                        changes_detected = True
                        print(f"🔄 Changes detected in {current_ups.get('name', 'Unknown')}:")
                        
                        if current_ups.get('status') != initial_ups.get('status'):
                            print(f"  Status: {initial_ups.get('status')} → {current_ups.get('status')}")
                        
                        if current_ups.get('batteryLevel') != initial_ups.get('batteryLevel'):
                            print(f"  Battery: {initial_ups.get('batteryLevel')}% → {current_ups.get('batteryLevel')}%")
                        
                        if current_ups.get('temperature') != initial_ups.get('temperature'):
                            print(f"  Temperature: {initial_ups.get('temperature')}°C → {current_ups.get('temperature')}°C")
                        
                        print(f"  Last Update: {current_ups.get('lastUpdate')}")
                
                if not changes_detected:
                    print("   No changes detected yet...")
                
                # Update initial data for next comparison
                initial_data = current_data
                
                # Wait for next check
                if check_num < total_checks - 1:
                    print(f"   Next check in {check_interval} seconds...")
                    time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error during check {check_num + 1}: {e}")
                time.sleep(check_interval)
        
        print("\n" + "=" * 50)
        print("📊 Final UPS Data:")
        print("-" * 30)
        
        final_data = list(collection.find({}, {'name': 1, 'status': 1, 'batteryLevel': 1, 'temperature': 1, 'lastUpdate': 1}))
        
        for ups in final_data:
            print(f"UPS: {ups.get('name', 'Unknown')}")
            print(f"  Status: {ups.get('status', 'Unknown')}")
            print(f"  Battery: {ups.get('batteryLevel', 'Unknown')}%")
            print(f"  Temperature: {ups.get('temperature', 'Unknown')}°C")
            print(f"  Last Update: {ups.get('lastUpdate', 'Unknown')}")
            print()
        
        # Check status counts
        status_counts = {}
        for ups in final_data:
            status = ups.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("📈 Status Counts:")
        print("-" * 30)
        for status, count in status_counts.items():
            print(f"  {status.capitalize()}: {count}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure MongoDB is running and the UPS monitoring service is active")

if __name__ == "__main__":
    test_ups_data_updates()
