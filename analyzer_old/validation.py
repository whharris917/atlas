"""
Pure validation functions for name resolution.

These functions validate resolution results against reconnaissance data
without side effects or complex dependencies.
"""

from typing import Dict, Any
from .logger import LogLevel, get_logger
from .utils import get_source


def validate_resolution(fqn: str, recon_data: Dict[str, Any]) -> bool:
    """
    Validate that resolved FQN exists in reconnaissance data.
    
    Args:
        fqn: Fully qualified name to validate
        recon_data: Reconnaissance data containing classes, functions, state, etc.
        
    Returns:
        True if FQN exists in any reconnaissance data section, False otherwise
    """
    exists = (fqn in recon_data["classes"] or 
             fqn in recon_data["functions"] or 
             fqn in recon_data["state"] or
             fqn in recon_data.get("external_classes", {}) or
             fqn in recon_data.get("external_functions", {}))
    
    # Log validation result
    getattr(get_logger(), LogLevel.TRACE.name.lower())(
        f"Validation check: {fqn} {'EXISTS' if exists else 'NOT_FOUND'}",
        get_source(),
        {'fqn': fqn, 'exists': exists}
    )
    
    return exists


def is_known_external_method(class_fqn: str, method_name: str) -> bool:
    """
    Check if method is a known method of an external class.
    
    Args:
        class_fqn: Fully qualified name of the external class
        method_name: Name of the method to check
        
    Returns:
        True if this is a recognized external library method, False otherwise
    """
    # SocketIO specific methods
    if 'SocketIO' in class_fqn and method_name in ['emit', 'on', 'send', 'disconnect']:
        return True
    
    # Threading specific methods  
    if 'threading' in class_fqn and method_name in ['start', 'join', 'acquire', 'release']:
        return True
    
    # Common object methods
    if method_name in ['__init__', '__str__', '__repr__', '__call__']:
        return True
    
    return False
