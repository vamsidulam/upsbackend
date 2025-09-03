#!/usr/bin/env python3
"""
Simple script to start just the backend API without reload
This avoids the infinite logging issue caused by --reload
"""

import subprocess
import sys
import os

def start_backend_only():
    """Start just the backend API without reload"""
    
    print("🚀 Starting Backend API Only (No Reload)")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: Please run this script from the backend directory")
        print("   cd backend")
        print("   python start_backend_only.py")
        sys.exit(1)
    
    print("📋 Starting Backend API...")
    print("   ⚠️  Using --reload=false to avoid infinite logging")
    print()
    
    try:
        # Start uvicorn server WITHOUT reload
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], cwd=os.getcwd())
        
        print("✅ Backend API started successfully!")
        print("   🌐 Available at: http://localhost:8000")
        print("   📚 API docs at: http://localhost:8000/docs")
        print("   🧪 Test Enhanced Predictions: http://localhost:8000/api/predictions/enhanced")
        print()
        print("📊 No reload mode - changes require manual restart")
        print("   To stop: Press Ctrl+C")
        print("=" * 50)
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Backend API stopped by user")
    except Exception as e:
        print(f"❌ Error starting Backend API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_backend_only()
