"""
Root Module - Base classes and utilities.

Tests:
- Module-level imports
- Base class definition
- Instance attributes with/without type hints
- Class attributes
- Methods with/without type hints
- Module-level state variables
"""

from typing import List, Dict, Optional
from decimal import Decimal


# =============================================================================
# IMPORTS - Test import statement handling
# =============================================================================

import sys
import os
from datetime import datetime


# =============================================================================
# MODULE-LEVEL STATE - Test state variable detection
# =============================================================================

# With type annotation
VERSION: str = "1.0.0"
MAX_ITEMS: int = 100

# Without type annotation (should infer from literal)
debug_mode = True
default_timeout = 30.0


# =============================================================================
# BASE CLASS - Test inheritance foundation
# =============================================================================

class BaseEntity:
    """
    Base class for all entities.
    
    Tests:
    - Instance attributes (with and without type hints)
    - Method with full type hints
    - Method without return type hint (violation)
    """
    
    def __init__(self, entity_id: str, name: str):
        """Initialize base entity."""
        # Instance attributes with type hints
        self.entity_id: str = entity_id
        self.name: str = name
        
        # Instance attribute without type hint (violation)
        self.created_at = datetime.now()
    
    def get_id(self) -> str:
        """Get entity ID - fully typed."""
        return self.entity_id
    
    def validate(self):
        """Validate entity - missing return type hint (violation)."""
        return len(self.name) > 0


# =============================================================================
# UTILITY FUNCTIONS - Test module-level functions
# =============================================================================

def calculate_total(items: List[Decimal], tax_rate: float) -> Decimal:
    """
    Calculate total with tax - fully typed.
    
    Tests: complex types (List[Decimal]), proper annotations.
    """
    subtotal = sum(items)
    return subtotal * (1 + Decimal(str(tax_rate)))


def format_name(first, last):
    """
    Format full name - no type hints (violations).
    
    Tests: missing argument and return type hints.
    """
    return f"{first} {last}"


# =============================================================================
# CLASS WITH CLASS ATTRIBUTES - Test class-level variables
# =============================================================================

class Config:
    """
    Configuration class.
    
    Tests: class attributes with and without type hints.
    """
    
    # Class attribute with type hint
    MAX_CONNECTIONS: int = 10
    
    # Class attribute without type hint (violation)
    DEFAULT_HOST = "localhost"
    
    def __init__(self):
        """Initialize config."""
        self.port: int = 8080
