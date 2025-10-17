"""
Subscript Operation Demonstration - Session 49

This module demonstrates GetSubscript element type inference from generic
annotations using REAL classes from the sample_files project.
"""

from typing import List, Dict, Set, Tuple, Optional
from decimal import Decimal
from datetime import datetime

# Import actual classes from sample_files
from models.user import User, UserProfile
from models.product import Product, ProductCategory
from models.order import Order, OrderItem
from services.auth_service import AuthService, TokenManager
from services.email_service import EmailService
from core.exceptions import ValidationError


# =============================================================================
# Test Case 1: List of User Objects - THE REAL TEST
# =============================================================================

users: List[User] = [
    User("user1", "alice@example.com", "alice", "pass123"),
    User("user2", "bob@example.com", "bob", "pass456"),
    User("user3", "charlie@example.com", "charlie", "pass789")
]

first_user = users[0]  # Should infer: sample_files.models.user.User
second_user = users[1]  # Should infer: sample_files.models.user.User

# THE ULTIMATE TEST: Chained subscript + attribute access
first_user_email = users[0].email  # Should infer User, then navigate to email attribute!
second_user_username = users[1].username  # User -> username attribute


# =============================================================================
# Test Case 2: List of Product Objects
# =============================================================================

products: List[Product] = [
    Product("p1", "Laptop", Decimal("999.99"), None, "High-end laptop"),
    Product("p2", "Mouse", Decimal("29.99"), None, "Wireless mouse"),
    Product("p3", "Keyboard", Decimal("79.99"), None, "Mechanical keyboard")
]

first_product = products[0]  # Should infer: sample_files.models.product.Product
second_product_price = products[1].price  # Product -> price attribute (Decimal)
third_product_name = products[2].name  # Product -> name attribute


# =============================================================================
# Test Case 3: Dict Mapping User IDs to Users
# =============================================================================

user_cache: Dict[str, User] = {
    "alice": User("u1", "alice@example.com", "alice", "pass"),
    "bob": User("u2", "bob@example.com", "bob", "pass"),
    "charlie": User("u3", "charlie@example.com", "charlie", "pass")
}

alice = user_cache["alice"]  # Should infer: sample_files.models.user.User
alice_email = user_cache["alice"].email  # Dict[str, User] -> User -> email
bob_username = user_cache["bob"].username  # Chained dict access + attribute


# =============================================================================
# Test Case 4: Dict Mapping Product IDs to Prices
# =============================================================================

product_prices: Dict[str, Decimal] = {
    "laptop": Decimal("999.99"),
    "mouse": Decimal("29.99"),
    "keyboard": Decimal("79.99")
}

laptop_price = product_prices["laptop"]  # Should infer: Decimal
mouse_price = product_prices["mouse"]  # Should infer: Decimal


# =============================================================================
# Test Case 5: Nested Structure - User Profiles by User ID
# =============================================================================

user_profiles: Dict[str, UserProfile] = {
    "alice": UserProfile("u1", "Alice", "Smith", datetime.now()),
    "bob": UserProfile("u2", "Bob", "Jones", datetime.now())
}

alice_profile = user_profiles["alice"]  # Should infer: sample_files.models.user.UserProfile
alice_full_name = user_profiles["alice"].get_full_name()  # Profile -> method call -> return type


# =============================================================================
# Test Case 6: List of Orders
# =============================================================================

orders: List[Order] = [
    Order("order1", "user1", datetime.now()),
    Order("order2", "user2", datetime.now()),
    Order("order3", "user3", datetime.now())
]

first_order = orders[0]  # Should infer: sample_files.models.order.Order
second_order_user = orders[1]  # Should infer: Order


# =============================================================================
# Test Case 7: Complex Nested - Dict of User to List of Orders
# =============================================================================

user_orders: Dict[str, List[Order]] = {
    "alice": [
        Order("o1", "alice", datetime.now()),
        Order("o2", "alice", datetime.now())
    ],
    "bob": [
        Order("o3", "bob", datetime.now())
    ]
}

alice_orders = user_orders["alice"]  # Should infer: List[Order]
alice_first_order = user_orders["alice"][0]  # CHAINED: Dict -> List -> Order!


# =============================================================================
# Test Case 8: List of OrderItems
# =============================================================================

order_items: List[OrderItem] = [
    OrderItem("product1", 2, Decimal("29.99")),
    OrderItem("product2", 1, Decimal("99.99")),
    OrderItem("product3", 5, Decimal("9.99"))
]

first_item = order_items[0]  # Should infer: sample_files.models.order.OrderItem
second_item_price = order_items[1].get_total_price()  # OrderItem -> method -> return type


# =============================================================================
# Test Case 9: Tuple of Services
# =============================================================================

services: Tuple[AuthService, EmailService] = (
    AuthService(TokenManager("secret", 24)),
    EmailService("smtp.example.com", 587, "user", "pass")
)

auth_service = services[0]  # Should infer: sample_files.services.auth_service.AuthService
email_service = services[1]  # Should infer: sample_files.services.email_service.EmailService


# =============================================================================
# Test Case 10: Matrix of Products (3D structure)
# =============================================================================

product_grid: List[List[Product]] = [
    [
        Product("p1", "Item1", Decimal("10.00"), None, ""),
        Product("p2", "Item2", Decimal("20.00"), None, "")
    ],
    [
        Product("p3", "Item3", Decimal("30.00"), None, ""),
        Product("p4", "Item4", Decimal("40.00"), None, "")
    ]
]

first_row = product_grid[0]  # Should infer: List[Product]
first_product_from_grid = product_grid[0][0]  # CHAINED: List -> Product
first_product_price_from_grid = product_grid[0][0].price  # List -> Product -> price!


# =============================================================================
# Test Case 11: Optional List Access
# =============================================================================

optional_users: Optional[List[User]] = [
    User("u1", "test@example.com", "test", "pass")
]

# Note: Would need Optional unwrapping first, but we can test the annotation parsing


# =============================================================================
# Test Case 12: Dict of Product Categories to Products
# =============================================================================

products_by_category: Dict[str, List[Product]] = {
    "electronics": [
        Product("e1", "Laptop", Decimal("999.99"), None, ""),
        Product("e2", "Phone", Decimal("699.99"), None, "")
    ],
    "accessories": [
        Product("a1", "Case", Decimal("29.99"), None, "")
    ]
}

electronics = products_by_category["electronics"]  # Should infer: List[Product]
first_electronic = products_by_category["electronics"][0]  # Dict -> List -> Product!
first_electronic_name = products_by_category["electronics"][0].name  # -> name attribute!


# =============================================================================
# Test Case 13: List of Exceptions
# =============================================================================

validation_errors: List[ValidationError] = [
    ValidationError("Invalid email", "email", {}),
    ValidationError("Invalid password", "password", {})
]

first_error = validation_errors[0]  # Should infer: sample_files.core.exceptions.ValidationError
first_error_field = validation_errors[0].get_field()  # -> method call


# =============================================================================
# Test Case 14: Simple Types with Subscripts (baseline)
# =============================================================================

numbers: List[int] = [1, 2, 3, 4, 5]
first_number = numbers[0]  # Should infer: int

strings: List[str] = ["hello", "world"]
first_string = strings[0]  # Should infer: str

decimals: List[Decimal] = [Decimal("1.5"), Decimal("2.5")]
first_decimal = decimals[0]  # Should infer: Decimal


# =============================================================================
# Test Case 15: Dict of String to Int (simple baseline)
# =============================================================================

scores: Dict[str, int] = {"alice": 100, "bob": 95}
alice_score = scores["alice"]  # Should infer: int


# =============================================================================
# Summary Statistics
# =============================================================================

print("=" * 80)
print("SUBSCRIPT DEMO MODULE - Session 49")
print("=" * 80)
print("\nTest Cases Loaded:")
print("  - List[User] subscripts: 2")
print("  - List[Product] subscripts: 3")
print("  - Dict[str, User] subscripts: 3")
print("  - List[Order] subscripts: 2")
print("  - Nested structures: 5+")
print("  - Chained operations: 8+")
print("\nTotal subscript operations: 25+")
print("Using REAL classes from sample_files!")
print("=" * 80)