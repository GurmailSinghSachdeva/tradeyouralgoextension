"""
Configuration settings for Trade Your Algo Extension
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 5paisa Vendor Login Credentials
FIVEPAISA_MOBILE_NUMBER = os.getenv("FIVEPAISA_MOBILE_NUMBER", "7838856179")
FIVEPAISA_OTP = os.getenv("FIVEPAISA_OTP", "")  # Leave empty for manual entry
FIVEPAISA_PIN = os.getenv("FIVEPAISA_PIN", "634863")

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
BACKEND_API_ENDPOINT = f"{BACKEND_API_URL}/api/auth/token"

# OTP API Configuration (for Make integration)
# For AWS Elastic Beanstalk, set OTP_API_URL to your EB domain
# Elastic Beanstalk sets PORT automatically - use it if available
OTP_API_PORT = int(os.getenv("PORT", os.getenv("OTP_API_PORT", "5000")))
OTP_API_HOST = os.getenv("OTP_API_HOST", "0.0.0.0")  # 0.0.0.0 to accept external connections
OTP_API_URL = os.getenv("OTP_API_URL", "")  # Leave empty to auto-detect from PORT
OTP_API_ENABLED = os.getenv("OTP_API_ENABLED", "true").lower() == "true"

# Auto-detect OTP_API_URL if not set (for Elastic Beanstalk)
if not OTP_API_URL:
    # Check if we're in AWS (Elastic Beanstalk sets these)
    eb_domain = os.getenv("ELASTIC_BEANSTALK_DOMAIN") or os.getenv("EB_DOMAIN")
    if eb_domain:
        OTP_API_URL = f"https://{eb_domain}"
    else:
        # Fallback to localhost for local development
        OTP_API_URL = f"http://localhost:{OTP_API_PORT}"

# 5paisa Vendor Login URLs
FIVEPAISA_VENDOR_KEY = os.getenv("FIVEPAISA_VENDOR_KEY", "NgsvVsF61rnO6VAXASdlhvXqLnkZuKCT")
FIVEPAISA_RESPONSE_URL = os.getenv("FIVEPAISA_RESPONSE_URL", "http://tradealgo-env.eba-dughp7yu.ap-south-1.elasticbeanstalk.com/api/reqToken")
FIVEPAISA_VENDOR_LOGIN_URL = f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index?VendorKey={FIVEPAISA_VENDOR_KEY}&ResponseURL={FIVEPAISA_RESPONSE_URL}"

# Playwright Settings
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))  # 30 seconds default

