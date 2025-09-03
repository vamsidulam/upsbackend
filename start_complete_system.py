#!/usr/bin/env python3
"""
Complete UPS Monitoring System Startup Script
Runs all necessary services for the complete system
"""

import subprocess
import time
import signal
import sys
import os
from datetime import datetime

class CompleteSystemManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
    
    def start_backend_api(self):
        """Start the FastAPI backend server"""
        print("🚀 Starting Backend API Server...")
        try:
            # Start uvicorn server
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "main:app", 
                "--reload", "--host", "0.0.0.0", "--port", "8000"
            ], cwd=os.getcwd())
            
            self.processes.append(("Backend API", process))
            print("✅ Backend API Server started successfully!")
            print("   🌐 API available at: http://localhost:8000")
            print("   📚 API docs at: http://localhost:8000/docs")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Backend API: {e}")
            return False
    
    def start_continuous_predictions(self):
        """Start the continuous predictions service"""
        print("🔮 Starting Continuous Predictions Service...")
        try:
            # Start continuous predictions service
            process = subprocess.Popen([
                sys.executable, "continuous_predictions.py"
            ], cwd=os.getcwd())
            
            self.processes.append(("Continuous Predictions", process))
            print("✅ Continuous Predictions Service started successfully!")
            print("   ⏰ Predictions generated every 15 minutes")
            print("   🎯 Using Enhanced AI Model Trainer")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Continuous Predictions: {e}")
            return False
    
    def start_real_time_monitor(self):
        """Start the real-time UPS monitoring service"""
        print("📊 Starting Real-time UPS Monitoring Service...")
        try:
            # Start real-time monitoring service
            process = subprocess.Popen([
                sys.executable, "scripts/ups_monitor_service.py"
            ], cwd=os.getcwd())
            
            self.processes.append(("Real-time Monitor", process))
            print("✅ Real-time UPS Monitoring Service started successfully!")
            print("   ⏰ UPS data updated every 1 minute")
            print("   🔍 Real-time status monitoring active")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Real-time Monitor: {e}")
            return False
    
    def start_all_services(self):
        """Start all services in the correct order"""
        print("🚀 Starting Complete UPS Monitoring System...")
        print("=" * 60)
        
        # Start services in order
        services = [
            ("Backend API", self.start_backend_api),
            ("Continuous Predictions", self.start_continuous_predictions),
            ("Real-time Monitor", self.start_real_time_monitor)
        ]
        
        started_services = []
        
        for service_name, start_func in services:
            print(f"\n🔄 Starting {service_name}...")
            if start_func():
                started_services.append(service_name)
                # Give each service time to initialize
                time.sleep(3)
            else:
                print(f"❌ Failed to start {service_name}, stopping all services...")
                self.stop_all_services()
                return False
        
        print("\n" + "=" * 60)
        print("🎉 All services started successfully!")
        print("📋 Running Services:")
        for service_name in started_services:
            print(f"   ✅ {service_name}")
        
        print("\n🔗 System Access:")
        print("   🌐 Frontend: http://localhost:3000")
        print("   🔌 Backend API: http://localhost:8000")
        print("   📚 API Documentation: http://localhost:8000/docs")
        print("   🧪 Test Enhanced Predictions: http://localhost:8000/api/predictions/enhanced")
        
        print("\n📊 Monitoring:")
        print("   🔮 ML Predictions: Every 15 minutes")
        print("   📈 UPS Data Updates: Every 1 minute")
        print("   🚨 Real-time Alerts: Continuous")
        
        print("\n⏹️  To stop all services, press Ctrl+C")
        print("=" * 60)
        
        return True
    
    def monitor_services(self):
        """Monitor running services"""
        try:
            print("\n🔍 Monitoring service health...")
            print("   (Press Ctrl+C to stop all services)")
            
            while self.running:
                # Check if all processes are still running
                for service_name, process in self.processes:
                    if process.poll() is not None:
                        print(f"⚠️  {service_name} service stopped unexpectedly!")
                        print(f"   Exit code: {process.returncode}")
                        
                        # Get any error output
                        if process.stderr:
                            stderr_output = process.stderr.read()
                            if stderr_output:
                                print(f"   Error output: {stderr_output}")
                        
                        # Restart the service
                        print(f"🔄 Restarting {service_name}...")
                        if service_name == "Backend API":
                            self.start_backend_api()
                        elif service_name == "Continuous Predictions":
                            self.start_continuous_predictions()
                        elif service_name == "Real-time Monitor":
                            self.start_real_time_monitor()
                    else:
                        # Service is running, check for output
                        if process.stdout and process.stdout.readable():
                            try:
                                # Non-blocking read to check for output
                                output = process.stdout.readline()
                                if output:
                                    print(f"📤 {service_name}: {output.strip()}")
                            except:
                                pass  # No output available
                
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.stop_all_services()
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        
        for service_name, process in self.processes:
            try:
                print(f"   Stopping {service_name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {service_name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  {service_name} didn't stop gracefully, forcing...")
                process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping {service_name}: {e}")
        
        self.processes.clear()
        print("✅ All services stopped")

def main():
    """Main function"""
    print("🚀 UPS Monitoring System - Complete Startup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: Please run this script from the backend directory")
        print("   cd backend")
        print("   python start_complete_system.py")
        sys.exit(1)
    
    # Check required files
    required_files = [
        "main.py",
        "continuous_predictions.py", 
        "scripts/ups_monitor_service.py",
        "ml/enhanced_model_trainer.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all required files are present in the backend directory.")
        sys.exit(1)
    
    # Create system manager and start services
    manager = CompleteSystemManager()
    
    if manager.start_all_services():
        try:
            manager.monitor_services()
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        finally:
            manager.stop_all_services()
    else:
        print("❌ Failed to start all services")
        sys.exit(1)

if __name__ == "__main__":
    main()
