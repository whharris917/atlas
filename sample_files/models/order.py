"""
Order Model - No Type Hints Test

All methods deliberately have NO type annotations.
Should generate maximum violations for comprehensive testing.
"""

from datetime import datetime
from ..core.base import BaseEntity


class OrderItem:
    """Order item with no type hints."""
    
    def __init__(self, product_id, quantity, unit_price):
        """No type hints."""
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
    
    def get_total_price(self):
        """No type hints."""
        return self.quantity * self.unit_price
    
    def update_quantity(self, new_quantity):
        """No type hints."""
        self.quantity = new_quantity
    
    def get_product_id(self):
        """No type hints."""
        return self.product_id


class Order(BaseEntity):
    """Order model with no type hints."""
    
    def __init__(self, order_id, user_id, order_date):
        """No type hints."""
        super().__init__(order_id, f"Order-{order_id}")
        self.user_id = user_id
        self.order_date = order_date
        self.items = []
        self.status = "pending"
        self.shipping_address = None
    
    def add_item(self, product_id, quantity, unit_price):
        """No type hints."""
        item = OrderItem(product_id, quantity, unit_price)
        self.items.append(item)
    
    def remove_item(self, product_id):
        """No type hints."""
        self.items = [item for item in self.items if item.product_id != product_id]
    
    def get_total_amount(self):
        """No type hints."""
        return sum(item.get_total_price() for item in self.items)
    
    def get_item_count(self):
        """No type hints."""
        return len(self.items)
    
    def update_status(self, new_status):
        """No type hints."""
        self.status = new_status
    
    def set_shipping_address(self, address):
        """No type hints."""
        self.shipping_address = address
    
    def is_completed(self):
        """No type hints."""
        return self.status == "completed"
    
    def cancel_order(self):
        """No type hints."""
        self.status = "cancelled"
