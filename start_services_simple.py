#!/usr/bin/env python3
"""
Simple UPS Monitoring System Startup Script
Starts services reliably without complex subprocess management
"""

import subprocess
import time
import sys
import os

def start_services_simple():
    """Start services using simple subprocess calls"""
    
    print("🚀 Starting UPS Monitoring System (Simple Method)")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: Please run this script from the backend directory")
        print("   cd backend")
        print("   python start_services_simple.py")
        sys.exit(1)
    
    print("📋 Starting services...")
    print()
    
    try:
        # Start Backend API
        print("1. 🚀 Starting Backend API...")
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=os.getcwd())
        
        print("   ✅ Backend API started (PID: {})".format(api_process.pid))
        print("   🌐 Available at: http://localhost:8000")
        print("   📚 Docs at: http://localhost:8000/docs")
        
        # Wait for backend to start
        print("   ⏳ Waiting for backend to initialize...")
        time.sleep(5)
        
        # Start Continuous Predictions
        print("\n2. 🔮 Starting Continuous Predictions...")
        predictions_process = subprocess.Popen([
            sys.executable, "continuous_predictions.py"
        ], cwd=os.getcwd())
        
        print("   ✅ Continuous Predictions started (PID: {})".format(predictions_process.pid))
        print("   ⏰ Predictions every 15 minutes")
        
        # Wait for predictions to start
        time.sleep(3)
        
        # Start UPS Monitor Service
        print("\n3. 📊 Starting UPS Monitor Service...")
        monitor_process = subprocess.Popen([
            sys.executable, "scripts/ups_monitor_service.py"
        ], cwd=os.getcwd())
        
        print("   ✅ UPS Monitor Service started (PID: {})".format(monitor_process.pid))
        print("   ⏰ UPS data updates every 1 minute")
        
        print("\n" + "=" * 60)
        print("🎉 All services started successfully!")
        print()
        print("📋 Running Services:")
        print("   ✅ Backend API (PID: {})".format(api_process.pid))
        print("   ✅ Continuous Predictions (PID: {})".format(predictions_process.pid))
        print("   ✅ UPS Monitor Service (PID: {})".format(monitor_process.pid))
        print()
        print("🔗 System Access:")
        print("   🌐 Frontend: http://localhost:3000")
        print("   🔌 Backend API: http://localhost:8000")
        print("   📚 API Documentation: http://localhost:8000/docs")
        print("   🧪 Test Enhanced Predictions: http://localhost:8000/api/predictions/enhanced")
        print()
        print("📊 Monitoring:")
        print("   🔮 ML Predictions: Every 15 minutes")
        print("   📈 UPS Data Updates: Every 1 minute")
        print("   🚨 Real-time Alerts: Continuous")
        print()
        print("⏹️  To stop services, use Task Manager or:")
        print("   taskkill /PID {} /F  # Backend API".format(api_process.pid))
        print("   taskkill /PID {} /F  # Continuous Predictions".format(predictions_process.pid))
        print("   taskkill /PID {} /F  # UPS Monitor Service".format(monitor_process.pid))
        print("=" * 60)
        
        # Keep the script running to show status
        print("\n🔍 Services are running. Press Ctrl+C to exit this script.")
        print("   (Services will continue running in background)")
        
        try:
            while True:
                time.sleep(10)
                # Check if processes are still running
                if api_process.poll() is not None:
                    print("⚠️  Backend API stopped unexpectedly")
                if predictions_process.poll() is not None:
                    print("⚠️  Continuous Predictions stopped unexpectedly")
                if monitor_process.poll() is not None:
                    print("⚠️  UPS Monitor Service stopped unexpectedly")
                    
        except KeyboardInterrupt:
            print("\n🛑 Exiting startup script...")
            print("   Services will continue running in background")
            print("   Use Task Manager or taskkill to stop them if needed")
    
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_services_simple()
