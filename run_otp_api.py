#!/usr/bin/env python3
"""
Standalone script to run the OTP API server
This server receives OTP from Make and serves it to the login automation
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradeyouralgoextension.otp_api_server import start_otp_api_server
from tradeyouralgoextension.config import OTP_API_URL
from tradeyouralgoextension.logging_config import setup_logging
import logging
import os

# Configure logging with IST timezone
use_ist = os.getenv("USE_UTC", "false").lower() != "true"
setup_logging(level=logging.INFO, use_ist=use_ist)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from tradeyouralgoextension.config import OTP_API_HOST, OTP_API_PORT, OTP_API_URL
    
    logger.info("=" * 60)
    logger.info("🚀 Starting OTP API Server")
    logger.info(f"📡 Listening on: {OTP_API_HOST}:{OTP_API_PORT}")
    logger.info(f"🌐 OTP API URL: {OTP_API_URL}")
    logger.info("")
    logger.info("Make Configuration:")
    logger.info(f"  - Endpoint: POST {OTP_API_URL}/api/otp")
    logger.info("  - Payload: {\"otp\": \"123456\"}")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        start_otp_api_server(host=OTP_API_HOST, port=OTP_API_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("\n👋 OTP API Server stopped")

