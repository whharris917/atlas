"""
Model Tests - Fully Typed Test

All test functions have complete type annotations.
Should generate zero violations for testing Atlas precision.
"""

from typing import Any, List
from decimal import Decimal
from datetime import datetime
from ..models.user import User, UserProfile
from ..models.product import Product, ProductCategory
from ..core.exceptions import ValidationError


class TestUser:
    """User model tests with complete type coverage."""
    
    def setup_method(self) -> None:
        """Fully typed test setup."""
        self.user = User("test_id", "test@example.com", "testuser", "password123")
    
    def test_user_creation(self) -> None:
        """Fully typed test method."""
        assert self.user.get_id() == "test_id"
        assert self.user.get_email() == "test@example.com"
        assert self.user.name == "testuser"
    
    def test_role_management(self) -> None:
        """Fully typed role testing."""
        self.user.add_role("admin")
        self.user.add_role("moderator")
        
        roles = self.user.get_roles()
        assert "admin" in roles
        assert "moderator" in roles
        assert len(roles) == 2
    
    def test_user_activation(self) -> None:
        """Fully typed activation testing."""
        self.user.deactivate()
        assert not self.user.is_active
        
        self.user.activate()
        assert self.user.is_active


class TestProduct:
    """Product model tests with full type coverage."""
    
    def setup_method(self) -> None:
        """Fully typed test setup."""
        self.category = ProductCategory("electronics", "Electronics", "Electronic devices")
        self.product = Product(
            "laptop_001", 
            "Gaming Laptop", 
            Decimal("1299.99"), 
            self.category,
            "High-performance gaming laptop"
        )
    
    def test_product_creation(self) -> None:
        """Fully typed product creation test."""
        assert self.product.get_id() == "laptop_001"
        assert self.product.name == "Gaming Laptop"
        assert self.product.get_price() == Decimal("1299.99")
        assert self.product.category == self.category
    
    def test_tag_management(self) -> None:
        """Fully typed tag management test."""
        self.product.add_tag("gaming")
        self.product.add_tag("laptop")
        self.product.add_tag("high-performance")
        
        tags = self.product.get_tags()
        assert len(tags) == 3
        assert "gaming" in tags
        
        removed = self.product.remove_tag("laptop")
        assert removed is True
        assert "laptop" not in self.product.get_tags()
    
    def test_stock_management(self) -> None:
        """Fully typed stock testing."""
        assert not self.product.is_in_stock()
        
        self.product.update_stock(10)
        assert self.product.is_in_stock()
        assert self.product.stock_quantity == 10
    
    def test_price_calculations(self) -> None:
        """Fully typed price calculation test."""
        original_price = self.product.get_price()
        discounted_price = self.product.calculate_discounted_price(10.0)
        
        expected_discount = original_price * Decimal("0.10")
        expected_price = original_price - expected_discount
        assert discounted_price == expected_price


def validate_test_data(data: List[Any]) -> bool:
    """Fully typed validation function."""
    return all(item is not None for item in data)


def create_test_user(user_id: str, email: str, username: str) -> User:
    """Fully typed user factory."""
    return User(user_id, email, username, "test_password")


def assert_validation_error(error: ValidationError, expected_field: str) -> None:
    """Fully typed assertion helper."""
    assert error.get_field() == expected_field
    assert len(error.get_details()) >= 0
