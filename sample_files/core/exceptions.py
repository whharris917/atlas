"""
Custom Exceptions - Fully Typed Test

All functions and methods have complete type annotations.
Should produce zero type hint violations.
"""

from typing import Optional, Dict, Any


class ValidationError(ValueError):
    """Custom validation error with full type coverage."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Fully typed constructor."""
        super().__init__(message)
        self.field = field
        self.details = details or {}
    
    def get_field(self) -> Optional[str]:
        """Fully typed getter."""
        return self.field
    
    def get_details(self) -> Dict[str, Any]:
        """Fully typed details getter."""
        return self.details
    
    def add_detail(self, key: str, value: Any) -> None:
        """Fully typed method with void return."""
        self.details[key] = value


class AuthenticationError(Exception):
    """Authentication error with full type coverage."""
    
    def __init__(self, message: str, error_code: int = 401) -> None:
        """Fully typed constructor."""
        super().__init__(message)
        self.error_code = error_code
    
    def get_error_code(self) -> int:
        """Fully typed getter."""
        return self.error_code
    
    def is_unauthorized(self) -> bool:
        """Fully typed predicate."""
        return self.error_code == 401
    
    def is_forbidden(self) -> bool:
        """Fully typed predicate."""
        return self.error_code == 403


def validate_email(email: str) -> bool:
    """Fully typed module-level function."""
    return '@' in email and '.' in email.split('@')[1]


def create_validation_error(message: str, field: Optional[str] = None) -> ValidationError:
    """Fully typed factory function."""
    return ValidationError(message, field)
