"""
User Endpoints - Partial Type Coverage

REST endpoints with strategic type annotation mixing.
"""

from typing import Dict, Any, Optional
from ...models.user import User, UserProfile
from ...services.auth_service import AuthService


class UserEndpoints:
    """User API endpoints with partial type coverage."""
    
    def __init__(self, auth_service: AuthService):
        """Fully typed constructor."""
        self.auth_service = auth_service
        self.user_cache = {}
    
    def login(self, username: str, password):
        """Partially typed - missing password type."""
        try:
            result = self.auth_service.login(username, password)
            return {
                'status': 'success',
                'token': result['token'],
                'user_id': result['user'].get_id()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def logout(self, token):
        """Missing parameter type."""
        self.auth_service.logout(token)
        return {'status': 'success', 'message': 'Logged out successfully'}
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Fully typed method."""
        if user_id in self.user_cache:
            profile = self.user_cache[user_id]
            return {
                'user_id': profile.user_id,
                'full_name': profile.get_full_name(),
                'bio': profile.bio
            }
        return {'error': 'User profile not found'}
    
    def update_user_profile(self, user_id, profile_data):
        """No type hints."""
        if user_id not in self.user_cache:
            return {'error': 'User not found'}
        
        profile = self.user_cache[user_id]
        if 'bio' in profile_data:
            profile.set_bio(profile_data['bio'])
        
        return {'status': 'success', 'message': 'Profile updated'}
    
    def create_user(self, user_data: Dict[str, Any]):
        """Missing return type."""
        user = User(
            user_data['id'],
            user_data['email'],
            user_data['username'],
            user_data.get('password')
        )
        
        # Cache the user
        self.user_cache[user.get_id()] = UserProfile(
            user.get_id(),
            user_data.get('first_name', ''),
            user_data.get('last_name', ''),
            user_data.get('birth_date')
        )
        
        return {
            'status': 'success',
            'user_id': user.get_id(),
            'message': 'User created successfully'
        }
    
    def delete_user(self, user_id):
        """No type hints."""
        if user_id in self.user_cache:
            del self.user_cache[user_id]
            return {'status': 'success', 'message': 'User deleted'}
        return {'error': 'User not found'}
