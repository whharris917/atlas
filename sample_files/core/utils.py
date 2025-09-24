"""
Utility Functions - No Type Hints Test

All functions deliberately have NO type annotations.
Should produce maximum type hint violations for testing.
"""

import hashlib
from datetime import datetime


def format_timestamp(timestamp):
    """No type hints - should generate violations."""
    if isinstance(timestamp, datetime):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return str(timestamp)


def calculate_hash(data):
    """No type hints - should generate violations."""
    if isinstance(data, str):
        return hashlib.md5(data.encode()).hexdigest()
    return hashlib.md5(str(data).encode()).hexdigest()


def merge_dictionaries(dict1, dict2):
    """No type hints - should generate violations."""
    result = dict1.copy()
    result.update(dict2)
    return result


def flatten_list(nested_list):
    """No type hints - should generate violations."""
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened


def safe_divide(numerator, denominator, default_value):
    """No type hints - should generate violations."""
    if denominator == 0:
        return default_value
    return numerator / denominator


class UtilityHelper:
    """Utility class with no type hints."""
    
    def __init__(self, name):
        """No type hints."""
        self.name = name
    
    def process_data(self, data, options):
        """No type hints."""
        return f"Processing {data} with {options}"
    
    def get_name(self):
        """No type hints."""
        return self.name
