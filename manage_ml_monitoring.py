#!/usr/bin/env python3
"""
ML Monitoring Management Script
Control and monitor the continuous ML prediction system
"""

import os
import sys
import time
import subprocess
import psutil
from datetime import datetime

def check_ml_monitoring_status():
    """Check if ML monitoring is currently running"""
    print("🔍 Checking ML Monitoring Status...")
    print("=" * 50)
    
    # Check for running Python processes with ML monitoring
    ml_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('integrate_ml_predictions.py' in arg for arg in cmdline):
                    ml_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if ml_processes:
        print("✅ ML Monitoring is RUNNING")
        print(f"   Active processes: {len(ml_processes)}")
        for proc in ml_processes:
            print(f"   PID: {proc.pid}, Started: {datetime.fromtimestamp(proc.create_time()).strftime('%H:%M:%S')}")
    else:
        print("❌ ML Monitoring is NOT RUNNING")
    
    return len(ml_processes) > 0

def start_ml_monitoring():
    """Start the ML monitoring system"""
    print("🚀 Starting ML Monitoring System...")
    
    try:
        # Start the continuous monitoring in background
        process = subprocess.Popen([
            sys.executable, 'integrate_ml_predictions.py', '--continuous'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ ML Monitoring started with PID: {process.pid}")
        print("   The system will generate predictions every 15 minutes")
        print("   Check the logs for prediction details")
        
        return process.pid
        
    except Exception as e:
        print(f"❌ Failed to start ML monitoring: {e}")
        return None

def stop_ml_monitoring():
    """Stop all ML monitoring processes"""
    print("🛑 Stopping ML Monitoring System...")
    
    stopped_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('integrate_ml_predictions.py' in arg for arg in cmdline):
                    proc.terminate()
                    stopped_count += 1
                    print(f"   Stopped process PID: {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if stopped_count > 0:
        print(f"✅ Stopped {stopped_count} ML monitoring processes")
    else:
        print("ℹ️ No ML monitoring processes found to stop")
    
    return stopped_count

def generate_predictions_now():
    """Generate predictions immediately"""
    print("⚡ Generating ML Predictions Now...")
    
    try:
        result = subprocess.run([
            sys.executable, 'integrate_ml_predictions.py', '--once'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Predictions generated successfully!")
            print("   Check the output above for details")
        else:
            print(f"❌ Failed to generate predictions: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Prediction generation timed out")
    except Exception as e:
        print(f"❌ Error generating predictions: {e}")

def show_help():
    """Show help information"""
    print("🚀 ML Monitoring Management Script")
    print("=" * 50)
    print("Usage:")
    print("  python manage_ml_monitoring.py [command]")
    print("")
    print("Commands:")
    print("  status     - Check if ML monitoring is running")
    print("  start      - Start continuous ML monitoring (15 min intervals)")
    print("  stop       - Stop all ML monitoring processes")
    print("  now        - Generate predictions immediately")
    print("  help       - Show this help message")
    print("")
    print("Examples:")
    print("  python manage_ml_monitoring.py status")
    print("  python manage_ml_monitoring.py start")
    print("  python manage_ml_monitoring.py stop")
    print("  python manage_ml_monitoring.py now")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        check_ml_monitoring_status()
        
    elif command == 'start':
        if check_ml_monitoring_status():
            print("⚠️ ML Monitoring is already running!")
        else:
            start_ml_monitoring()
            
    elif command == 'stop':
        stop_ml_monitoring()
        
    elif command == 'now':
        generate_predictions_now()
        
    elif command == 'help':
        show_help()
        
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
