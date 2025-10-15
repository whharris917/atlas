"""
Inheritance Pattern Examples

Comprehensive test cases for class inheritance extraction including
multiple inheritance, qualified names, mixins, ABC patterns, and more.

This module provides Atlas with diverse inheritance patterns for testing
base class extraction and future MRO analysis capabilities.
"""

from abc import ABC, abstractmethod
from typing import Protocol
import collections.abc


# =============================================================================
# ABSTRACT BASE CLASSES
# =============================================================================

class DataStore(ABC):
    """Abstract base class using abc.ABC."""
    
    @abstractmethod
    def save(self, data):
        """Abstract method to be implemented by subclasses."""
        pass
    
    @abstractmethod
    def load(self, key):
        """Abstract method to be implemented by subclasses."""
        pass
    
    def clear(self):
        """Concrete method available to all subclasses."""
        print("Clearing data store")


class RepositoryBase(ABC):
    """Another abstract base demonstrating ABC pattern."""
    
    @abstractmethod
    def find_by_id(self, entity_id):
        """Find entity by ID."""
        pass
    
    @abstractmethod
    def find_all(self):
        """Find all entities."""
        pass


# =============================================================================
# MIXIN PATTERNS
# =============================================================================

class LoggingMixin:
    """Mixin providing logging capabilities."""
    
    def log_info(self, message):
        """Log info message."""
        print(f"INFO: {message}")
    
    def log_error(self, message):
        """Log error message."""
        print(f"ERROR: {message}")
    
    def log_debug(self, message):
        """Log debug message."""
        print(f"DEBUG: {message}")


class TimestampMixin:
    """Mixin providing timestamp tracking."""
    
    def __init__(self):
        """Initialize timestamps."""
        from datetime import datetime
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def touch(self):
        """Update the updated_at timestamp."""
        from datetime import datetime
        self.updated_at = datetime.now()


class ValidationMixin:
    """Mixin providing validation capabilities."""
    
    def validate(self):
        """Validate the object state."""
        return True
    
    def is_valid(self):
        """Check if object is valid."""
        return self.validate()


# =============================================================================
# MULTIPLE INHERITANCE
# =============================================================================

class AuditedDataStore(DataStore, LoggingMixin, TimestampMixin):
    """Multiple inheritance: ABC + two mixins.
    
    Demonstrates:
    - Inheriting from abstract base class
    - Multiple mixin composition
    - MRO with three base classes
    """
    
    def __init__(self):
        """Initialize with timestamp tracking."""
        TimestampMixin.__init__(self)
        self.data = {}
    
    def save(self, data):
        """Implement abstract save method with logging."""
        self.log_info(f"Saving data: {data}")
        self.data.update(data)
        self.touch()
    
    def load(self, key):
        """Implement abstract load method with logging."""
        self.log_info(f"Loading key: {key}")
        return self.data.get(key)


class ValidatedRepository(RepositoryBase, ValidationMixin, LoggingMixin):
    """Another multiple inheritance example.
    
    Demonstrates:
    - Different ABC base
    - Different mixin combination
    - Three base classes in different order
    """
    
    def __init__(self):
        """Initialize repository."""
        self.entities = {}
    
    def find_by_id(self, entity_id):
        """Find entity with validation."""
        if self.is_valid():
            self.log_debug(f"Finding entity: {entity_id}")
            return self.entities.get(entity_id)
        return None
    
    def find_all(self):
        """Find all entities."""
        if self.is_valid():
            return list(self.entities.values())
        return []


# =============================================================================
# QUALIFIED BASE CLASS NAMES
# =============================================================================

class CustomMapping(collections.abc.Mapping):
    """Inherits from qualified name: collections.abc.Mapping.
    
    Tests extraction of base classes with dot notation.
    """
    
    def __init__(self, data):
        """Initialize with data dict."""
        self._data = data
    
    def __getitem__(self, key):
        """Get item by key."""
        return self._data[key]
    
    def __iter__(self):
        """Iterate over keys."""
        return iter(self._data)
    
    def __len__(self):
        """Return number of items."""
        return len(self._data)


class CustomSequence(collections.abc.Sequence):
    """Inherits from qualified name: collections.abc.Sequence.
    
    Another example of qualified base class name.
    """
    
    def __init__(self, items):
        """Initialize with items list."""
        self._items = list(items)
    
    def __getitem__(self, index):
        """Get item by index."""
        return self._items[index]
    
    def __len__(self):
        """Return number of items."""
        return len(self._items)


# =============================================================================
# DEEP INHERITANCE CHAINS
# =============================================================================

class Level1Base:
    """First level in inheritance chain."""
    
    def method_level1(self):
        """Level 1 method."""
        return "level1"
    
    def common_method(self):
        """Method present at all levels."""
        return "base"


class Level2Derived(Level1Base):
    """Second level - inherits from Level1Base."""
    
    def method_level2(self):
        """Level 2 method."""
        return "level2"
    
    def common_method(self):
        """Override common method."""
        return "level2"


class Level3Derived(Level2Derived):
    """Third level - inherits from Level2Derived."""
    
    def method_level3(self):
        """Level 3 method."""
        return "level3"
    
    def common_method(self):
        """Override common method."""
        return "level3"


class Level4Derived(Level3Derived):
    """Fourth level - inherits from Level3Derived.
    
    Tests deep inheritance chains (4 levels).
    """
    
    def method_level4(self):
        """Level 4 method."""
        return "level4"
    
    def common_method(self):
        """Override common method."""
        return "level4"


# =============================================================================
# PROTOCOL (STRUCTURAL SUBTYPING)
# =============================================================================

class Drawable(Protocol):
    """Protocol defining drawable interface.
    
    Tests Protocol as base class (structural subtyping).
    """
    
    def draw(self) -> str:
        """Draw method that must be implemented."""
        ...
    
    def get_bounds(self):
        """Get drawing bounds."""
        ...


class Renderable(Protocol):
    """Another protocol example."""
    
    def render(self) -> str:
        """Render method."""
        ...


# =============================================================================
# DIAMOND INHERITANCE
# =============================================================================

class DiamondBase:
    """Base of diamond pattern."""
    
    def base_method(self):
        """Method defined in base."""
        return "base"
    
    def shared_method(self):
        """Method overridden in branches."""
        return "base_shared"


class DiamondLeft(DiamondBase):
    """Left branch of diamond."""
    
    def left_method(self):
        """Method unique to left branch."""
        return "left"
    
    def shared_method(self):
        """Override shared method."""
        return "left_shared"


class DiamondRight(DiamondBase):
    """Right branch of diamond."""
    
    def right_method(self):
        """Method unique to right branch."""
        return "right"
    
    def shared_method(self):
        """Override shared method."""
        return "right_shared"


class DiamondBottom(DiamondLeft, DiamondRight):
    """Bottom of diamond - multiple inheritance.
    
    Classic diamond problem testing MRO resolution.
    Left comes before Right in MRO.
    """
    
    def bottom_method(self):
        """Method unique to bottom."""
        return "bottom"


# =============================================================================
# MIXED PATTERNS
# =============================================================================

class ComplexInheritance(Level2Derived, LoggingMixin, TimestampMixin):
    """Complex multiple inheritance mixing different patterns.
    
    Demonstrates:
    - Inheriting from middle of chain (Level2Derived)
    - Multiple mixins
    - Complex MRO calculation
    """
    
    def __init__(self):
        """Initialize complex object."""
        TimestampMixin.__init__(self)
        self.state = "initialized"
    
    def do_something(self):
        """Method using inherited functionality."""
        self.log_info("Doing something")
        self.touch()
        return self.method_level2()


class QuadrupleInheritance(DataStore, LoggingMixin, TimestampMixin, ValidationMixin):
    """Four base classes.
    
    Demonstrates maximum complexity with four parent classes.
    """
    
    def __init__(self):
        """Initialize with all mixin functionality."""
        TimestampMixin.__init__(self)
        self.storage = {}
    
    def save(self, data):
        """Save with full auditing."""
        if self.is_valid():
            self.log_info("Validated save operation")
            self.storage.update(data)
            self.touch()
    
    def load(self, key):
        """Load with validation."""
        if self.is_valid():
            return self.storage.get(key)
        return None