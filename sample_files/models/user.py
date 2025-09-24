"""
User Model - Partial Type Coverage Test

Mix of typed and untyped methods to test violation detection.
"""

from typing import Optional, List
from datetime import datetime
from ..core.base import BaseEntity


class User(BaseEntity):
    """User model with partial type coverage."""
    
    def __init__(self, user_id: str, email: str, username, password=None):
        """Partially typed constructor - missing username and password types."""
        super().__init__(user_id, username)
        self.email = email
        self.username = username
        self.password = password
        self.is_active = True
        self.roles = []
    
    def get_email(self) -> str:
        """Fully typed getter."""
        return self.email
    
    def set_email(self, email):
        """Missing parameter type."""
        self.email = email
    
    def add_role(self, role: str):
        """Missing return type."""
        self.roles.append(role)
    
    def has_role(self, role):
        """No type hints."""
        return role in self.roles
    
    def get_roles(self) -> List[str]:
        """Fully typed."""
        return self.roles.copy()
    
    def activate(self) -> None:
        """Fully typed void return."""
        self.is_active = True
    
    def deactivate(self):
        """Missing return type."""
        self.is_active = False


class UserProfile:
    """User profile with mixed typing patterns."""
    
    def __init__(self, user_id: str, first_name, last_name: str, birth_date=None):
        """Mixed typing - some params typed, others not."""
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.bio = ""
        self.avatar_url = None
    
    def get_full_name(self):
        """No type hints."""
        return f"{self.first_name} {self.last_name}"
    
    def set_bio(self, bio: str) -> None:
        """Fully typed."""
        self.bio = bio
    
    def calculate_age(self, current_date):
        """Missing parameter and return types."""
        if not self.birth_date:
            return None
        return (current_date - self.birth_date).days // 365
