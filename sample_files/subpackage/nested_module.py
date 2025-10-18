"""
Nested Module - Advanced testing.

Tests:
- Imports from parent package
- Inheritance from imported base class
- Tests nested functions (no nested classes - uncommon in practice)
- Complex type annotations
- Method calls and attribute access
- Type inference chains
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import sys

# Import from parent package
from root_module import BaseEntity, calculate_total


# =============================================================================
# INHERITED CLASS - Test inheritance resolution
# =============================================================================

class Product(BaseEntity):
    """
    Product class inheriting from BaseEntity.
    
    Tests:
    - Inheritance resolution (base_class_fqns)
    - Attribute inheritance (should find 'name' from BaseEntity)
    - Complex type annotations
    - Mix of typed and untyped attributes
    """
    
    def __init__(self, product_id: str, name: str, price: Decimal, tags: Optional[List[str]] = None):
        """Initialize product - tests Optional and List types."""
        super().__init__(product_id, name)
        
        # Typed instance attributes with complex types
        self.price: Decimal = price
        self.tags: List[str] = tags or []
        self.metadata: Dict[str, str] = {}
        
        # Untyped instance attribute (violation)
        self.in_stock = True
    
    def get_price(self) -> Decimal:
        """Get product price."""
        return self.price
    
    def add_tag(self, tag):
        """Add tag - missing argument and return type hints (violations)."""
        self.tags.append(tag)
    
    def calculate_discount(self, rate: float):
        """Calculate discounted price - missing return type (violation)."""
        return self.price * Decimal(str(1 - rate))


# =============================================================================
# INVENTORY CLASS - Test separate class (not nested)
# =============================================================================

class Inventory:
    """
    Inventory management class.
    
    Tests: standard class with complex types (no nesting needed).
    """
    
    def __init__(self):
        """Initialize inventory."""
        self.items: Dict[str, Product] = {}
        self.count = 0  # Untyped (violation)
    
    def add_item(self, product_id: str, product: Product) -> None:
        """Add item to inventory."""
        self.items[product_id] = product
        self.count += 1
    
    def get_item(self, product_id):
        """Get item - missing type hints (violations)."""
        return self.items.get(product_id)


# =============================================================================
# STORE CLASS - Test class with methods
# =============================================================================

class Store:
    """
    Store class with inventory management.
    
    Tests: class using other classes (composition without nesting).
    """
    
    def __init__(self, store_name: str):
        """Initialize store."""
        self.name: str = store_name
        self.inventory: Inventory = Inventory()
        
        # Untyped attribute (violation)
        self.is_open = True


# =============================================================================
# ADDITIONAL FUNCTIONS - Test function calls and type inference
# =============================================================================

def process_order(products: List[Product], tax_rate: float) -> Dict[str, Decimal]:
    """
    Process order function.
    
    Tests:
    - Complex return type (Dict[str, Decimal])
    - Function calls and type inference
    - List comprehensions
    """
    # Type inference tests: should infer types from operations
    prices = [p.price for p in products]
    subtotal = sum(prices)
    total = calculate_total(prices, tax_rate)
    
    return {
        "subtotal": subtotal,
        "total": total
    }


def helper_function(x, y):
    """
    Untyped helper function.
    
    Tests: missing all type hints (violations).
    """
    return (x + y) * 2


# =============================================================================
# TYPE INFERENCE TESTS - Test analysis phase
# =============================================================================

# Simple literal inference
count = 42  # Should infer: int
name = "TestProduct"  # Should infer: str
is_valid = True  # Should infer: bool

# Complex type inference from constructors
product = Product("p1", "Widget", Decimal("19.99"))  # Should infer: Product
store = Store("Main Store")  # Should infer: Store

# Container literal inference
products: List[Product] = [product]
product_dict: Dict[str, Product] = {"p1": product}

# Attribute access type inference (should navigate through inheritance)
product_name = product.name  # Should infer: str (from BaseEntity.name)
product_price = product.price  # Should infer: Decimal
product_id = product.get_id()  # Should infer: str

# Method call type inference
discount_price = product.calculate_discount(0.1)  # Should infer: Decimal

# Subscript type inference
first_product = products[0]  # Should infer: Product
lookup_product = product_dict["p1"]  # Should infer: Product

# Annotation mismatch test (should create IncorrectTypeAnnotation warning)
wrong_type: int = "not an int"  # Annotation says int, value is str


# =============================================================================
# UNSUPPORTED EXPRESSION TESTS - Test Atlas limitations
# =============================================================================

# These should generate UnsupportedExpressionType notes
binary_op = count + 10  # BinOp
comparison = count > 50  # Compare
ternary = "yes" if is_valid else "no"  # IfExp
f_string = f"Product: {name}"  # JoinedStr
