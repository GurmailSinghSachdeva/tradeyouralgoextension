"""
OTP API Client - Fetches OTP from the local API server (which receives it from Make)
"""
import requests
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class OTPAPIClient:
    """Client to fetch OTP from the local API server"""

    def __init__(self, api_url: str = None):
        """
        Initialize OTP API client
        
        Args:
            api_url: Base URL of the OTP API server (default: from config)
        """
        if api_url is None:
            from .config import OTP_API_URL
            api_url = OTP_API_URL
        
        self.api_url = api_url.rstrip('/')
        self.otp_endpoint = f"{self.api_url}/api/otp"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_otp(self) -> Optional[str]:
        """
        Get OTP from the API server
        
        Returns:
            6-digit OTP string if available, None otherwise
        """
        try:
            response = self.session.get(self.otp_endpoint, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            otp = data.get('otp')
            
            if otp:
                logger.info(f"✅ OTP fetched from API: {otp[:2]}**")
                return otp
            else:
                message = data.get('message', 'No OTP available')
                logger.debug(f"No OTP available: {message}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OTP from API: {str(e)}")
            return None

    def wait_for_otp(self, max_wait_seconds: int = 300, check_interval_seconds: int = 2) -> Optional[str]:
        """
        Wait for OTP to become available from the API server
        
        Args:
            max_wait_seconds: Maximum time to wait (default: 5 minutes)
            check_interval_seconds: How often to check (default: 2 seconds)
            
        Returns:
            6-digit OTP string if found, None if timeout
        """
        logger.info(f"Waiting for OTP from API (max {max_wait_seconds}s, checking every {check_interval_seconds}s)...")
        
        elapsed_time = 0
        while elapsed_time < max_wait_seconds:
            otp = self.get_otp()
            if otp:
                return otp
            
            time.sleep(check_interval_seconds)
            elapsed_time += check_interval_seconds
            
            if elapsed_time % 10 == 0:  # Log every 10 seconds
                logger.info(f"Still waiting for OTP... ({elapsed_time}/{max_wait_seconds}s)")
        
        logger.warning(f"Timeout waiting for OTP after {max_wait_seconds} seconds")
        return None

    def clear_otp(self) -> bool:
        """
        Clear/consume OTP after use
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(f"{self.api_url}/api/otp/clear", timeout=5)
            response.raise_for_status()
            logger.info("OTP cleared from API")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error clearing OTP: {str(e)}")
            return False

    def verify_connection(self) -> bool:
        """
        Verify connection to OTP API server
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

