"""
Base service class providing common functionality and error handling patterns.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseService:
    """Base class for all services with common functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def success_response(self, data: Any = None, message: str = None) -> Dict:
        """Create standardized success response."""
        response = {'success': True}
        if data:
            response['data'] = data
        if message:
            response['message'] = message
        return response
    
    def error_response(self, message: str, error_code: str = None) -> Dict:
        """Create standardized error response."""
        response = {
            'success': False,
            'error': message
        }
        if error_code:
            response['error_code'] = error_code
        
        self.logger.error(f"Service error: {message}")
        return response
    
    def validate_session(self, session_id: str) -> bool:
        """Validate session ID format."""
        return session_id and len(session_id) > 0
    
    def log_operation(self, operation: str, details: Dict = None):
        """Log service operations for debugging."""
        log_msg = f"Operation: {operation}"
        if details:
            log_msg += f" | Details: {details}"
        self.logger.info(log_msg)