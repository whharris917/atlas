"""
Authentication Service - Mixed Type Coverage

Strategically mixed type hints to test Atlas detection accuracy.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..core.exceptions import AuthenticationError
from ..models.user import User


class TokenManager:
    """Token manager with mixed typing."""
    
    def __init__(self, secret_key: str, expiry_hours=24):
        """Partially typed - missing expiry_hours type."""
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
        self.active_tokens = {}
    
    def generate_token(self, user_id: str) -> str:
        """Fully typed method."""
        token = f"token_{user_id}_{datetime.now().timestamp()}"
        expiry = datetime.now() + timedelta(hours=self.expiry_hours)
        self.active_tokens[token] = {
            'user_id': user_id,
            'expires_at': expiry
        }
        return token
    
    def validate_token(self, token):
        """Missing parameter and return types."""
        if token not in self.active_tokens:
            return False
        
        token_data = self.active_tokens[token]
        if datetime.now() > token_data['expires_at']:
            del self.active_tokens[token]
            return False
        
        return True
    
    def get_user_id_from_token(self, token: str):
        """Missing return type."""
        if self.validate_token(token):
            return self.active_tokens[token]['user_id']
        return None
    
    def revoke_token(self, token):
        """No type hints."""
        if token in self.active_tokens:
            del self.active_tokens[token]


class AuthService:
    """Authentication service with strategic type mixing."""
    
    def __init__(self, token_manager: TokenManager):
        """Fully typed constructor."""
        self.token_manager = token_manager
        self.login_attempts = {}
    
    def authenticate(self, username: str, password):
        """Partially typed - missing password type."""
        # Simulate authentication logic
        if username == "admin" and password == "secret":
            return User("admin_id", "admin@example.com", username)
        return None
    
    def login(self, username, password):
        """No type hints."""
        user = self.authenticate(username, password)
        if not user:
            self.record_failed_attempt(username)
            raise AuthenticationError("Invalid credentials")
        
        token = self.token_manager.generate_token(user.get_id())
        return {
            'user': user,
            'token': token,
            'expires_at': datetime.now() + timedelta(hours=24)
        }
    
    def logout(self, token: str) -> None:
        """Fully typed logout."""
        self.token_manager.revoke_token(token)
    
    def record_failed_attempt(self, username: str):
        """Missing return type."""
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        self.login_attempts[username].append(datetime.now())
    
    def is_account_locked(self, username):
        """No type hints."""
        if username not in self.login_attempts:
            return False
        
        recent_attempts = [
            attempt for attempt in self.login_attempts[username]
            if datetime.now() - attempt < timedelta(minutes=15)
        ]
        
        return len(recent_attempts) >= 3
