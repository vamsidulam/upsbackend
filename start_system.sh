#!/bin/bash

echo "🚀 Starting UPS Monitoring System with Background Services..."
echo
echo "📊 This will start:"
echo "   - FastAPI server on port 10000"
echo "   - Continuous predictions service (every 15 minutes)"
echo "   - UPS monitoring service (every 1 minute)"
echo "   - Gemini AI integration for failure analysis"
echo
echo "🌐 Access the system at: http://localhost:10000"
echo "📖 API documentation at: http://localhost:10000/docs"
echo "🔍 Health check at: http://localhost:10000/api/health"
echo "📊 System status at: http://localhost:10000/api/status"
echo
echo "Press Ctrl+C to stop all services"
echo "============================================================"
echo

# Make sure the script is executable
chmod +x start_with_background_services.py

# Start the system
python3 start_with_background_services.py
