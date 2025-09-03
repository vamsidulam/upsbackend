#!/usr/bin/env python3
"""
Startup script for UPS Monitoring System with Background Services
This script starts the FastAPI server which automatically starts all background services
"""

import uvicorn
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server with background services"""
    try:
        logger.info("🚀 Starting UPS Monitoring System with Background Services...")
        logger.info("📊 This will start:")
        logger.info("   - FastAPI server on port 10000")
        logger.info("   - Continuous predictions service (every 15 minutes)")
        logger.info("   - UPS monitoring service (every 1 minute)")
        logger.info("   - Gemini AI integration for failure analysis")
        logger.info("")
        logger.info("🌐 Access the system at: http://localhost:10000")
        logger.info("📖 API documentation at: http://localhost:10000/docs")
        logger.info("🔍 Health check at: http://localhost:10000/api/health")
        logger.info("📊 System status at: http://localhost:10000/api/status")
        logger.info("")
        logger.info("Press Ctrl+C to stop all services")
        logger.info("=" * 60)
        
        # Start the FastAPI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=10000,
            reload=False,  # Disable reload to prevent duplicate background services
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down UPS Monitoring System...")
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
