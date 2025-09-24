"""
Product Endpoints - Mixed Type Coverage

REST endpoints with various type annotation patterns.
"""

from typing import List, Dict, Any
from decimal import Decimal
from ...models.product import Product, ProductCategory


class ProductEndpoints:
    """Product API endpoints with mixed type coverage."""
    
    def __init__(self):
        """No type hints in constructor."""
        self.products = {}
        self.categories = {}
        self.search_cache = {}
    
    def create_category(self, name: str, description):
        """Partially typed - missing description type."""
        category_id = f"cat_{len(self.categories) + 1}"
        category = ProductCategory(category_id, name, description)
        self.categories[category_id] = category
        return {
            'status': 'success',
            'category_id': category_id,
            'message': 'Category created successfully'
        }
    
    def get_category(self, category_id):
        """Missing parameter and return types."""
        if category_id in self.categories:
            category = self.categories[category_id]
            return {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'subcategory_count': len(category.get_subcategories())
            }
        return {'error': 'Category not found'}
    
    def create_product(self, 
                      name: str, 
                      price: Decimal, 
                      category_id: str,
                      description=None) -> Dict[str, Any]:
        """Mixed typing - missing description type but return type present."""
        if category_id not in self.categories:
            return {'error': 'Invalid category'}
        
        product_id = f"prod_{len(self.products) + 1}"
        category = self.categories[category_id]
        product = Product(product_id, name, price, category, description)
        self.products[product_id] = product
        
        return {
            'status': 'success',
            'product_id': product_id,
            'message': 'Product created successfully'
        }
    
    def get_product(self, product_id):
        """No type hints."""
        if product_id in self.products:
            product = self.products[product_id]
            return {
                'id': product.get_id(),
                'name': product.name,
                'price': str(product.get_price()),
                'category': product.category.name,
                'in_stock': product.is_in_stock(),
                'tags': product.get_tags()
            }
        return {'error': 'Product not found'}
    
    def update_product_price(self, product_id: str, new_price: Decimal) -> bool:
        """Fully typed method."""
        if product_id in self.products:
            product = self.products[product_id]
            product.set_price(new_price)
            # Clear search cache since price changed
            self.search_cache.clear()
            return True
        return False
    
    def search_products(self, query, max_results):
        """No type hints."""
        # Check cache first
        cache_key = f"{query}:{max_results}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Simple search implementation
        results = []
        for product in self.products.values():
            if query.lower() in product.name.lower() or any(query.lower() in tag.lower() for tag in product.get_tags()):
                results.append({
                    'id': product.get_id(),
                    'name': product.name,
                    'price': str(product.get_price())
                })
                if len(results) >= max_results:
                    break
        
        # Cache results
        self.search_cache[cache_key] = results
        return results
    
    def add_product_tag(self, product_id: str, tag):
        """Missing tag parameter type."""
        if product_id in self.products:
            product = self.products[product_id]
            product.add_tag(tag)
            return {'status': 'success', 'message': 'Tag added'}
        return {'error': 'Product not found'}
