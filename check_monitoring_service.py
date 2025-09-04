#!/usr/bin/env python3
"""
Check if the monitoring service is running and generating predictions
"""

import os
import subprocess
import time
from datetime import datetime

def check_monitoring_service():
    """Check monitoring service status"""
    print("🔍 Checking UPS Monitoring Service Status")
    print("=" * 50)
    
    # Check if log file exists
    log_file = "ups_monitor_service.log"
    if os.path.exists(log_file):
        print(f"✅ Log file exists: {log_file}")
        
        # Check log file size and last modified time
        stat = os.stat(log_file)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        size_kb = stat.st_size / 1024
        
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if log has recent activity (last 10 minutes)
        time_diff = (datetime.now() - last_modified).total_seconds() / 60
        if time_diff < 10:
            print(f"   ✅ Recent activity: {time_diff:.1f} minutes ago")
        else:
            print(f"   ⚠️  No recent activity: {time_diff:.1f} minutes ago")
        
        # Show last few lines of log
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\n📋 Last {min(5, len(lines))} log entries:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
                else:
                    print("   Log file is empty")
        except Exception as e:
            print(f"   ❌ Error reading log: {e}")
    else:
        print(f"❌ Log file not found: {log_file}")
    
    # Check if monitoring service is running
    print(f"\n🔄 Checking for running monitoring processes...")
    try:
        # Check for Python processes with monitoring service
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            monitoring_processes = []
            
            for line in lines:
                if 'python.exe' in line and 'ups_monitor_service' in line:
                    monitoring_processes.append(line.strip())
            
            if monitoring_processes:
                print(f"✅ Found {len(monitoring_processes)} monitoring processes:")
                for proc in monitoring_processes:
                    print(f"   {proc}")
            else:
                print("❌ No monitoring service processes found")
                print("   This means the monitoring service is not running!")
        else:
            print("❌ Could not check running processes")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
    
    # Check if predictions are being generated
    print(f"\n🔮 Checking prediction generation...")
    try:
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['UPS_DATA_MONITORING']
        
        # Check predictions collection
        if 'ups_predictions' in db.list_collection_names():
            predictions_count = db['ups_predictions'].count_documents({})
            print(f"   Total predictions in database: {predictions_count}")
            
            if predictions_count > 0:
                # Check latest prediction timestamp
                latest_pred = db['ups_predictions'].find_one(sort=[('timestamp', -1)])
                if latest_pred:
                    timestamp = latest_pred.get('timestamp')
                    if timestamp:
                        if isinstance(timestamp, str):
                            try:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            except:
                                dt = datetime.fromisoformat(timestamp)
                        else:
                            dt = timestamp
                        
                        time_diff = (datetime.now() - dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') else datetime.now() - dt).total_seconds() / 60
                        
                        print(f"   Latest prediction: {time_diff:.1f} minutes ago")
                        
                        if time_diff < 20:
                            print(f"   ✅ Predictions are recent (within 15-minute cycle)")
                        else:
                            print(f"   ⚠️  Predictions are old: {time_diff:.1f} minutes ago")
                            print(f"      Expected: Every 15 minutes")
            else:
                print("   ❌ No predictions found in database")
        
        client.close()
        
    except Exception as e:
        print(f"   ❌ Error checking predictions: {e}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if not os.path.exists(log_file) or time_diff > 10:
        print("   1. Start the monitoring service:")
        print("      python scripts/start_monitoring_system.py")
        print("   2. Or start just the monitoring service:")
        print("      python scripts/ups_monitor_service.py")
    else:
        print("   1. Monitoring service appears to be running")
        print("   2. Check frontend for display issues")
        print("   3. Verify API endpoint: http://localhost:8000/api/predictions")

if __name__ == "__main__":
    check_monitoring_service()
