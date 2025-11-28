"""
Backend API Client for sending access tokens
"""
import requests
import logging
from typing import Optional, Dict

from .config import BACKEND_API_ENDPOINT

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for communicating with backend API"""

    def __init__(self, api_endpoint: str = BACKEND_API_ENDPOINT):
        self.api_endpoint = api_endpoint
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def send_access_token(self, access_token: str, additional_data: Optional[Dict] = None) -> bool:
        """
        Send access token to backend API
        
        Args:
            access_token: The access token from 5paisa login
            additional_data: Optional additional data to send with token
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "access_token": access_token,
            "source": "5paisa",
            "timestamp": None  # Will be set by backend or add datetime.utcnow().isoformat()
        }
        
        if additional_data:
            payload.update(additional_data)

        try:
            logger.info(f"Sending access token to {self.api_endpoint}")
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"Token sent successfully. Response: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send access token: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return False

    def verify_connection(self) -> bool:
        """
        Verify connection to backend API
        
        Returns:
            True if backend is reachable, False otherwise
        """
        try:
            # Try a simple GET request or health check endpoint
            health_endpoint = self.api_endpoint.replace("/api/auth/token", "/health")
            response = self.session.get(health_endpoint, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Backend health check failed: {str(e)}")
            return False

