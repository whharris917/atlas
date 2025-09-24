"""
API Middleware - No Type Hints Test

Middleware components with no type annotations.
Tests Atlas violation detection in web framework context.
"""

from datetime import datetime
import json


class AuthMiddleware:
    """Authentication middleware with no type hints."""
    
    def __init__(self, token_manager):
        """No type hints."""
        self.token_manager = token_manager
        self.excluded_paths = ['/login', '/register', '/health']
    
    def process_request(self, request):
        """No type hints."""
        if request.path in self.excluded_paths:
            return True
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header.split(' ')[1]
        return self.token_manager.validate_token(token)
    
    def extract_user_id(self, request):
        """No type hints."""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            return self.token_manager.get_user_id_from_token(token)
        return None
    
    def add_excluded_path(self, path):
        """No type hints."""
        self.excluded_paths.append(path)


class LoggingMiddleware:
    """Logging middleware with no type hints."""
    
    def __init__(self, log_file_path):
        """No type hints."""
        self.log_file_path = log_file_path
        self.request_count = 0
    
    def log_request(self, request, response):
        """No type hints."""
        self.request_count += 1
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'request_count': self.request_count
        }
        
        # Simulate writing to log file
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_request_count(self):
        """No type hints."""
        return self.request_count
    
    def reset_count(self):
        """No type hints."""
        self.request_count = 0
