import asyncio
import time
from datetime import datetime
import subprocess
import sys
import os

def start_monitoring_system():
    """Start the complete UPS monitoring system"""
    print("🚀 Starting UPS Monitoring System")
    print("=" * 50)
    
    try:
        # First, create 12 UPS systems if they don't exist
        print("📋 Step 1: Creating 12 UPS systems...")
        subprocess.run([sys.executable, "scripts/create_12_ups.py"], check=True)
        print("✅ UPS systems created/verified")
        
        # Set some UPS to failed status for realistic testing
        print("\n📋 Step 2: Setting some UPS to failed status for testing...")
        subprocess.run([sys.executable, "scripts/set_all_ups_failed.py"], check=True)
        print("✅ Realistic failure scenario created (1-2 UPS failed, rest healthy)")
        
        # Start the monitoring service
        print("\n📋 Step 3: Starting monitoring service...")
        print("📊 Data updates: Every 1 minute")
        print("🔮 ML predictions: Every 15 minutes")
        print("🔄 Status changes: Real-time based on data")
        print("🚨 Alerts: Generated automatically")
        
        # Start the monitoring service in a separate process
        monitor_process = subprocess.Popen([
            sys.executable, "scripts/ups_monitor_service.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"✅ Monitoring service started (PID: {monitor_process.pid})")
        
        # Start the backend API server
        print("\n📋 Step 4: Starting backend API server...")
        backend_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"✅ Backend API server started (PID: {backend_process.pid})")
        
        # Wait a moment for services to start
        time.sleep(3)
        
        print("\n🎉 UPS Monitoring System is now running!")
        print("=" * 50)
        print("📊 Monitoring Schedule:")
        print("   • Data updates: Every 1 minute")
        print("   • Status changes: Real-time")
        print("   • ML predictions: Every 15 minutes")
        print("   • Failure alerts: Based on predictions")
        print("\n🌐 Access the dashboard at: http://localhost:5173")
        print("🔌 API endpoint: http://localhost:8000")
        print("\n⏹️  Press Ctrl+C to stop all services")
        
        # Keep the main process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring system...")
            
            # Stop the monitoring service
            if monitor_process.poll() is None:
                monitor_process.terminate()
                print("✅ Monitoring service stopped")
            
            # Stop the backend server
            if backend_process.poll() is None:
                backend_process.terminate()
                print("✅ Backend server stopped")
            
            print("🎉 All services stopped successfully!")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running script: {e}")
    except Exception as e:
        print(f"❌ Error starting monitoring system: {e}")

if __name__ == "__main__":
    start_monitoring_system()
