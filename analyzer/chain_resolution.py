"""
Chain resolution functions for complex attribute chain walking.

Handles resolving multi-part names like obj.method.attr by walking each step.
"""

from typing import Dict, Any, Optional, List, Callable
from .logger import LogLevel, get_logger
from .utils import get_source
from .attribute_resolution import resolve_attribute


def _log_trace(message: str, extra: Optional[Dict[str, Any]] = None):
    """Internal logging helper for chain resolution."""
    get_logger().trace(message, get_source(), extra)


def resolve_chain(name_parts: List[str], resolve_simple_func: Callable, 
                 recon_data: Dict[str, Any], current_module: str, 
                 type_inference=None) -> Optional[str]:
    """
    Resolve complex attribute chains with enhanced attribute support.
    
    Args:
        name_parts: List of name parts to resolve (e.g., ['obj', 'method', 'attr'])
        resolve_simple_func: Function to resolve the base name
        recon_data: Reconnaissance data for resolution
        current_module: Current module context
        type_inference: Type inference engine (optional)
        
    Returns:
        Resolved FQN of the complete chain, or None if resolution fails
    """
    # Resolve base
    base_name = name_parts[0]
    _log_trace(f"Resolving chain base: {base_name}",
               {'chain_step': 'base', 'base_name': base_name, 'full_chain': name_parts})
    
    # Use the provided resolve_simple function to get base FQN
    base_fqn = resolve_simple_func(base_name)
    if not base_fqn:
        _log_trace(f"Chain resolution failed: could not resolve base {base_name}",
                   {'chain_failure': 'base_resolution', 'base_name': base_name})
        return None
    
    _log_trace(f"Chain base resolved: {base_name} -> {base_fqn}",
               {'base_name': base_name, 'base_fqn': base_fqn})
    
    # Walk the chain
    current_fqn = base_fqn
    for i, attr in enumerate(name_parts[1:], 1):
        _log_trace(f"Chain step {i}: Resolving {current_fqn}.{attr}",
                   {'chain_step': i, 'current_fqn': current_fqn, 'attr': attr})
        current_fqn = resolve_attribute(current_fqn, attr, recon_data, current_module, type_inference)
        if not current_fqn:
            _log_trace(f"Chain resolution failed at step {i}: .{attr}",
                       {'chain_failure': 'attribute_resolution', 'step': i, 'attr': attr})
            return None
        _log_trace(f"Chain step {i} resolved: {current_fqn}",
                   {'chain_step': i, 'resolved_fqn': current_fqn})
    
    return current_fqn