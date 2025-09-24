"""
Base Classes - Mixed Type Coverage Test

Tests Atlas with base classes having different type annotation patterns.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class BaseEntity:
    """Base entity with mixed type coverage."""
    
    def __init__(self, entity_id: str, name: str, metadata=None):
        """Constructor with partial typing - missing metadata type."""
        self.id = entity_id
        self.name = name
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def get_id(self) -> str:
        """Fully typed getter."""
        return self.id
    
    def get_name(self):
        """Missing return type hint."""
        return self.name
    
    def update_metadata(self, key: str, value):
        """Partially typed - missing value type."""
        self.metadata[key] = value
    
    def has_metadata(self, key):
        """No type hints at all."""
        return key in self.metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Fully typed method."""
        return {
            'id': self.id,
            'name': self.name,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class ConfigurableEntity(BaseEntity):
    """Inherits from BaseEntity with its own type patterns."""
    
    def __init__(self, entity_id: str, name: str, config: Dict[str, Any]):
        """Fully typed constructor."""
        super().__init__(entity_id, name)
        self.config = config
    
    def get_config_value(self, key: str, default=None):
        """Partially typed - missing default type."""
        return self.config.get(key, default)
    
    def set_config_value(self, key, value):
        """No type hints."""
        self.config[key] = value
    
    def merge_config(self, other_config: Dict[str, Any]) -> None:
        """Fully typed with void return."""
        self.config.update(other_config)
