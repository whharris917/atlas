"""
Product Model - Fully Typed Test

All methods and functions have complete type annotations.
Should produce zero violations - tests Atlas accuracy.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from ..core.base import BaseEntity


class ProductCategory:
    """Product category with full type coverage."""
    
    def __init__(self, category_id: str, name: str, description: Optional[str] = None) -> None:
        """Fully typed constructor."""
        self.id = category_id
        self.name = name
        self.description = description
        self.parent_id: Optional[str] = None
        self.subcategories: List['ProductCategory'] = []
    
    def add_subcategory(self, subcategory: 'ProductCategory') -> None:
        """Fully typed method."""
        subcategory.parent_id = self.id
        self.subcategories.append(subcategory)
    
    def get_subcategories(self) -> List['ProductCategory']:
        """Fully typed getter."""
        return self.subcategories.copy()
    
    def is_root_category(self) -> bool:
        """Fully typed predicate."""
        return self.parent_id is None


class Product(BaseEntity):
    """Product model with complete type coverage."""
    
    def __init__(self, 
                 product_id: str, 
                 name: str, 
                 price: Decimal, 
                 category: ProductCategory,
                 description: Optional[str] = None) -> None:
        """Fully typed constructor with complex types."""
        super().__init__(product_id, name)
        self.price = price
        self.category = category
        self.description = description
        self.stock_quantity: int = 0
        self.tags: List[str] = []
        self.attributes: Dict[str, Any] = {}
    
    def get_price(self) -> Decimal:
        """Fully typed getter."""
        return self.price
    
    def set_price(self, new_price: Decimal) -> None:
        """Fully typed setter."""
        self.price = new_price
    
    def add_tag(self, tag: str) -> None:
        """Fully typed method."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> bool:
        """Fully typed method with bool return."""
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def get_tags(self) -> List[str]:
        """Fully typed getter."""
        return self.tags.copy()
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Fully typed method with Any type."""
        self.attributes[key] = value
    
    def get_attribute(self, key: str, default: Optional[Any] = None) -> Any:
        """Fully typed getter with optional parameter."""
        return self.attributes.get(key, default)
    
    def update_stock(self, quantity: int) -> None:
        """Fully typed stock management."""
        self.stock_quantity = max(0, quantity)
    
    def is_in_stock(self) -> bool:
        """Fully typed stock check."""
        return self.stock_quantity > 0
    
    def calculate_discounted_price(self, discount_percentage: float) -> Decimal:
        """Fully typed calculation method."""
        discount_amount = self.price * Decimal(discount_percentage / 100)
        return self.price - discount_amount
