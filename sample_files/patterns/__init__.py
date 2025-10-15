"""
Patterns Package

Comprehensive examples demonstrating various Python design patterns
and language features for Atlas testing.

Modules:
    inheritance_examples: Complete inheritance pattern test cases
"""

from .inheritance_examples import (
    # Abstract Base Classes
    DataStore,
    RepositoryBase,
    
    # Mixins
    LoggingMixin,
    TimestampMixin,
    ValidationMixin,
    
    # Multiple Inheritance Examples
    AuditedDataStore,
    ValidatedRepository,
    
    # Qualified Base Names
    CustomMapping,
    CustomSequence,
    
    # Deep Inheritance Chain
    Level1Base,
    Level2Derived,
    Level3Derived,
    Level4Derived,
    
    # Protocols
    Drawable,
    Renderable,
    
    # Diamond Pattern
    DiamondBase,
    DiamondLeft,
    DiamondRight,
    DiamondBottom,
    
    # Complex Patterns
    ComplexInheritance,
    QuadrupleInheritance
)

__all__ = [
    # Abstract Base Classes
    'DataStore',
    'RepositoryBase',
    
    # Mixins
    'LoggingMixin',
    'TimestampMixin',
    'ValidationMixin',
    
    # Multiple Inheritance
    'AuditedDataStore',
    'ValidatedRepository',
    
    # Qualified Base Names
    'CustomMapping',
    'CustomSequence',
    
    # Inheritance Chain
    'Level1Base',
    'Level2Derived',
    'Level3Derived',
    'Level4Derived',
    
    # Protocols
    'Drawable',
    'Renderable',
    
    # Diamond Pattern
    'DiamondBase',
    'DiamondLeft',
    'DiamondRight',
    'DiamondBottom',
    
    # Complex Patterns
    'ComplexInheritance',
    'QuadrupleInheritance'
]