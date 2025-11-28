"""
Main entry point for Trade Your Algo Extension
"""
import asyncio
import logging
import sys
import os

from .fivepaisa_login import login_and_get_token
from .config import FIVEPAISA_MOBILE_NUMBER, OTP_API_ENABLED, OTP_API_URL
from .otp_api_server import start_otp_api_server_thread
from .logging_config import setup_logging

# Configure logging with IST timezone
# Set USE_UTC=true in environment to use UTC instead
use_ist = os.getenv("USE_UTC", "false").lower() != "true"
setup_logging(level=logging.INFO, use_ist=use_ist)

logger = logging.getLogger(__name__)


async def main_async():
    """Async main function"""
    try:
        # Validate configuration
        if not FIVEPAISA_MOBILE_NUMBER:
            logger.error("FIVEPAISA_MOBILE_NUMBER not set. Please configure in .env file")
            return False

        # Start OTP API server in background if enabled
        otp_api_thread = None
        if OTP_API_ENABLED:
            try:
                from .config import OTP_API_HOST, OTP_API_PORT
                
                logger.info(f"🚀 Starting OTP API server on {OTP_API_HOST}:{OTP_API_PORT}")
                logger.info(f"   OTP API URL: {OTP_API_URL}")
                logger.info(f"   Make can send OTP to: POST {OTP_API_URL}/api/otp")
                otp_api_thread = start_otp_api_server_thread(host=OTP_API_HOST, port=OTP_API_PORT, daemon=True)
                # Give server a moment to start
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Could not start OTP API server: {e}")
                logger.warning("Continuing without OTP API server...")

        logger.info("Starting 5paisa login automation...")
        
        # Step 1: Login to 5paisa and get access token
        logger.info("Step 1: Logging into 5paisa website...")
        access_token = await login_and_get_token()
        
        if not access_token:
            logger.error("Failed to obtain access token from 5paisa")
            return False
        
        logger.info(f"Access token obtained (first 20 chars): {access_token[:20]}...")
        print(f"AccessToken: {access_token}")
        logger.info("✅ Login completed and access token printed.")
        return True

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        return False


def main():
    """Main function - entry point"""
    try:
        success = asyncio.run(main_async())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
