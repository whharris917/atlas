"""
Core Package - Mixed Type Coverage

Exports core functionality with varying type annotation completeness.
"""

from .base import BaseEntity, ConfigurableEntity
from .exceptions import ValidationError, AuthenticationError
from .utils import format_timestamp, calculate_hash
