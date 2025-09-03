#!/usr/bin/env python3
"""
Simple ML Monitoring Status Checker
Check if ML predictions are running and show recent activity
"""

import os
import time
from datetime import datetime, timedelta

def check_ml_status():
    """Check ML monitoring status and recent activity"""
    print("🔍 ML Monitoring Status Check")
    print("=" * 50)
    
    # Check if the ML model exists
    model_path = "ml/ups_failure_model.pkl"
    if os.path.exists(model_path):
        model_time = datetime.fromtimestamp(os.path.getmtime(model_path))
        print(f"✅ ML Model: Found (trained: {model_time.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print("❌ ML Model: Not found - need to train first")
        return
    
    # Check for log files
    log_files = [
        "real_time_monitor.log",
        "integrate_ml_predictions.log"
    ]
    
    print("\n📋 Log Files:")
    for log_file in log_files:
        if os.path.exists(log_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            file_size = os.path.getsize(log_file)
            print(f"   ✅ {log_file}: {file_size} bytes, modified: {file_time.strftime('%H:%M:%S')}")
        else:
            print(f"   ❌ {log_file}: Not found")
    
    # Check for recent predictions in MongoDB
    print("\n📊 Recent ML Activity:")
    print("   ℹ️  To see recent predictions, run: python integrate_ml_predictions.py --once")
    print("   ℹ️  To start continuous monitoring: python integrate_ml_predictions.py --continuous")
    
    # Check if continuous monitoring is likely running
    print("\n🔄 Continuous Monitoring:")
    print("   ℹ️  Check Task Manager for Python processes running 'integrate_ml_predictions.py'")
    print("   ℹ️  Or run: python integrate_ml_predictions.py --once to test the system")

def show_quick_commands():
    """Show quick commands for ML monitoring"""
    print("\n🚀 Quick Commands:")
    print("=" * 50)
    print("1. Test ML System:")
    print("   python test_model_training.py")
    print("")
    print("2. Generate Predictions Now:")
    print("   python integrate_ml_predictions.py --once")
    print("")
    print("3. Start Continuous Monitoring (15 min intervals):")
    print("   python integrate_ml_predictions.py --continuous")
    print("")
    print("4. Run Simulation Mode:")
    print("   python real_time_monitor.py --simulation 5")
    print("")
    print("5. Check this status again:")
    print("   python check_ml_status.py")

def main():
    """Main function"""
    check_ml_status()
    show_quick_commands()
    
    print("\n" + "=" * 50)
    print("🎯 Your ML system is ready to use!")
    print("   Run the commands above to get started.")

if __name__ == "__main__":
    main()
