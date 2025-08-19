"""
Naming Utilities - Code Atlas

Centralized utilities for FQN (Fully Qualified Name) generation and manipulation.
"""

from typing import Optional


def generate_fqn(module_name: str, class_name: Optional[str], item_name: str) -> str:
    """
    Generate a fully qualified name for a code item.
    
    Args:
        module_name: The module containing the item
        class_name: The class containing the item (if any)
        item_name: The name of the item itself
        
    Returns:
        Fully qualified name string
    """
    if class_name:
        return f"{module_name}.{class_name}.{item_name}"
    return f"{module_name}.{item_name}"


def generate_class_fqn(module_name: str, class_name: str) -> str:
    """Generate FQN for a class."""
    return f"{module_name}.{class_name}"


def generate_function_fqn(module_name: str, class_name: Optional[str], function_name: str) -> str:
    """Generate FQN for a function or method."""
    return generate_fqn(module_name, class_name, function_name)


def generate_state_fqn(module_name: str, variable_name: str) -> str:
    """Generate FQN for a module-level state variable."""
    return f"{module_name}.{variable_name}"


def extract_module_from_fqn(fqn: str) -> str:
    """Extract module name from FQN."""
    return fqn.split('.')[0]


def extract_class_from_fqn(fqn: str) -> Optional[str]:
    """Extract class name from FQN if present."""
    parts = fqn.split('.')
    if len(parts) >= 3:  # module.class.item
        return parts[1]
    return None


def extract_item_name_from_fqn(fqn: str) -> str:
    """Extract the item name (last part) from FQN."""
    return fqn.split('.')[-1]


def is_method_fqn(fqn: str) -> bool:
    """Check if FQN represents a method (has 3+ parts)."""
    return len(fqn.split('.')) >= 3


def is_class_fqn(fqn: str, classes_registry: set) -> bool:
    """Check if FQN represents a class."""
    return fqn in classes_registry


def split_fqn(fqn: str) -> tuple:
    """
    Split FQN into its components.
    
    Returns:
        tuple: (module, class_or_none, item_name)
    """
    parts = fqn.split('.')
    if len(parts) == 2:
        return parts[0], None, parts[1]
    elif len(parts) >= 3:
        return parts[0], parts[1], '.'.join(parts[2:])
    else:
        return '', None, fqn


def join_fqn_parts(*parts) -> str:
    """Join FQN parts, filtering out None values."""
    return '.'.join(str(part) for part in parts if part is not None)


def normalize_fqn(fqn: str) -> str:
    """Normalize FQN by removing extra spaces and standardizing format."""
    return '.'.join(part.strip() for part in fqn.split('.') if part.strip())


def get_parent_fqn(fqn: str) -> Optional[str]:
    """Get the parent FQN (remove last component)."""
    parts = fqn.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


def is_child_of(child_fqn: str, parent_fqn: str) -> bool:
    """Check if child_fqn is a child of parent_fqn."""
    return child_fqn.startswith(parent_fqn + '.')


def get_relative_name(fqn: str, base_module: str) -> str:
    """Get relative name within a module context."""
    if fqn.startswith(base_module + '.'):
        return fqn[len(base_module) + 1:]
    return fqn
