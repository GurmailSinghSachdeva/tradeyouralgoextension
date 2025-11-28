"""
Logging configuration with IST timezone support
"""
import logging
import sys
from datetime import datetime
import time


class ISTFormatter(logging.Formatter):
    """Custom formatter that converts UTC to IST"""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # IST is UTC+5:30
        self.ist_offset = 5.5 * 3600  # 5 hours 30 minutes in seconds
    
    def formatTime(self, record, datefmt=None):
        # Convert UTC time to IST
        utc_time = time.gmtime(record.created)
        ist_timestamp = record.created + self.ist_offset
        ist_time = time.gmtime(ist_timestamp)
        
        if datefmt:
            return time.strftime(datefmt, ist_time)
        else:
            return time.strftime('%Y-%m-%d %H:%M:%S IST', ist_time)


def setup_logging(level=logging.INFO, use_ist=True):
    """
    Setup logging configuration with IST timezone support
    
    Args:
        level: Logging level (default: INFO)
        use_ist: Use IST timezone instead of UTC (default: True)
    """
    if use_ist:
        # Use custom IST formatter
        formatter = ISTFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S IST'
        )
    else:
        # Use default UTC formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    
    return root_logger

