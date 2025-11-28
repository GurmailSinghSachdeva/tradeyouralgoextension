"""
OTP API Server - Receives OTP from Make and serves it to the login automation
"""
from flask import Flask, request, jsonify
import logging
import threading
import os
from datetime import datetime, timedelta
from typing import Optional

# Setup logging with IST timezone if not already configured
if not logging.getLogger().handlers:
    from .logging_config import setup_logging
    use_ist = os.getenv("USE_UTC", "false").lower() != "true"
    setup_logging(level=logging.INFO, use_ist=use_ist)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory storage for OTP (with expiration)
_otp_storage = {
    'otp': None,
    'received_at': None,
    'expires_at': None,
    'expiration_seconds': 300  # OTP expires after 5 minutes
}


@app.route('/api/otp', methods=['POST'])
def receive_otp():
    """
    Endpoint for Make to send OTP
    
    Expected JSON payload:
    {
        "otp": "123456",
        "source": "make"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        otp = data.get('otp', '').strip()
        
        if not otp:
            return jsonify({'error': 'OTP not provided'}), 400
        
        if not otp.isdigit() or len(otp) != 6:
            return jsonify({'error': 'OTP must be a 6-digit number'}), 400
        
        # Store OTP with expiration
        _otp_storage['otp'] = otp
        _otp_storage['received_at'] = datetime.now()
        _otp_storage['expires_at'] = datetime.now() + timedelta(seconds=_otp_storage['expiration_seconds'])
        
        logger.info(f"✅ OTP received from Make: {otp[:2]}**")
        logger.info(f"OTP expires at: {_otp_storage['expires_at']}")
        
        return jsonify({
            'status': 'success',
            'message': 'OTP received successfully',
            'expires_at': _otp_storage['expires_at'].isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error receiving OTP: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/otp', methods=['GET'])
def get_otp():
    """
    Endpoint for login automation to fetch OTP
    
    Returns:
    {
        "otp": "123456",
        "received_at": "2024-01-01T12:00:00",
        "expires_at": "2024-01-01T12:05:00"
    }
    or
    {
        "otp": null,
        "message": "No OTP available"
    }
    """
    try:
        # Check if OTP exists and is not expired
        if _otp_storage['otp'] is None:
            return jsonify({
                'otp': None,
                'message': 'No OTP available'
            }), 200
        
        # Check expiration
        if _otp_storage['expires_at'] and datetime.now() > _otp_storage['expires_at']:
            # Clear expired OTP
            _otp_storage['otp'] = None
            _otp_storage['received_at'] = None
            _otp_storage['expires_at'] = None
            
            return jsonify({
                'otp': None,
                'message': 'OTP has expired'
            }), 200
        
        # Return OTP
        return jsonify({
            'otp': _otp_storage['otp'],
            'received_at': _otp_storage['received_at'].isoformat() if _otp_storage['received_at'] else None,
            'expires_at': _otp_storage['expires_at'].isoformat() if _otp_storage['expires_at'] else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting OTP: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/otp/clear', methods=['POST'])
def clear_otp():
    """
    Endpoint to clear/consume OTP after use
    """
    _otp_storage['otp'] = None
    _otp_storage['received_at'] = None
    _otp_storage['expires_at'] = None
    
    logger.info("OTP cleared")
    return jsonify({'status': 'success', 'message': 'OTP cleared'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


def start_otp_api_server(host=None, port=None, debug=False):
    """
    Start the OTP API server
    
    Args:
        host: Host to bind to (default: 0.0.0.0 to accept external connections)
        port: Port to bind to (default: from PORT env var or 5055)
        debug: Enable Flask debug mode (default: False)
    """
    # Use config values if not provided
    if host is None or port is None:
        import os
        from .config import OTP_API_HOST, OTP_API_PORT
        if host is None:
            host = OTP_API_HOST
        if port is None:
            port = OTP_API_PORT
    
    logger.info(f"Starting OTP API server on http://{host}:{port}")
    logger.info(f"Server will accept connections from all interfaces (0.0.0.0)")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def start_otp_api_server_thread(host=None, port=None, daemon=True):
    """
    Start OTP API server in a separate thread
    
    Args:
        host: Host to bind to (default: from config, 0.0.0.0 for external access)
        port: Port to bind to (default: from config/PORT env var)
        daemon: Run as daemon thread (default: True)
    """
    server_thread = threading.Thread(
        target=start_otp_api_server,
        args=(host, port, False),
        daemon=daemon
    )
    server_thread.start()
    logger.info(f"OTP API server thread started (host={host or 'from config'}, port={port or 'from config'})")
    return server_thread

