"""
Resolver Compatibility Layer - Code Atlas

Progressive migration compatibility layer for the name resolver.
Provides seamless switching between original and refactored implementations.
"""

from typing import Dict, List, Any, Optional
import importlib.util
import sys
import os

from .utils import LOG_LEVEL


def create_name_resolver_compat(recon_data: Dict[str, Any], use_refactored: Optional[bool] = None) -> Any:
    """
    Create a name resolver using progressive migration pattern.
    
    Args:
        recon_data: Reconnaissance data for resolution
        use_refactored: None = auto-detect, True = force refactored, False = force original
        
    Returns:
        NameResolver instance (original or refactored)
    """
    if use_refactored is None:
        # Auto-detect best available implementation
        use_refactored = _is_refactored_available()
    
    if use_refactored:
        try:
            if LOG_LEVEL >= 1:
                print("    [RESOLVER] Using refactored implementation")
            from .resolver_refactored import RefactoredNameResolver
            return RefactoredNameResolver(recon_data)
        except ImportError as e:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVER] Refactored implementation unavailable: {e}")
                print("    [RESOLVER] Falling back to original implementation")
            return _create_original_resolver(recon_data)
    else:
        if LOG_LEVEL >= 1:
            print("    [RESOLVER] Using original implementation")
        return _create_original_resolver(recon_data)


def _is_refactored_available() -> bool:
    """
    Check if the refactored resolver implementation is available.
    
    Returns:
        True if refactored implementation can be imported, False otherwise
    """
    try:
        # Try to find the refactored module
        current_dir = os.path.dirname(__file__)
        refactored_path = os.path.join(current_dir, "resolver_refactored.py")
        
        if not os.path.exists(refactored_path):
            return False
        
        # Try to import the specialized visitors
        from .visitors.specialized.simple_resolution_visitor import SimpleResolutionVisitor
        from .visitors.specialized.chain_resolution_visitor import ChainResolutionVisitor
        from .visitors.specialized.inheritance_resolution_visitor import InheritanceResolutionVisitor
        from .visitors.specialized.external_resolution_visitor import ExternalResolutionVisitor
        
        return True
    except ImportError:
        return False


def _create_original_resolver(recon_data: Dict[str, Any]) -> Any:
    """
    Create the original NameResolver implementation.
    
    Args:
        recon_data: Reconnaissance data for resolution
        
    Returns:
        Original NameResolver instance
    """
    from .resolver import NameResolver
    return NameResolver(recon_data)


class NameResolverCompatibilityWrapper:
    """
    Compatibility wrapper that provides a unified interface for both implementations.
    
    This wrapper ensures that both original and refactored resolvers can be used
    interchangeably without breaking existing code.
    """
    
    def __init__(self, recon_data: Dict[str, Any], use_refactored: Optional[bool] = None):
        self.resolver = create_name_resolver_compat(recon_data, use_refactored)
        self.implementation_type = "refactored" if hasattr(self.resolver, 'simple_resolver') else "original"
        
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVER] Created {self.implementation_type} resolver")
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name using the wrapped resolver.
        
        Args:
            name_parts: List of name components
            context: Resolution context
            
        Returns:
            Fully qualified name if resolved, None otherwise
        """
        return self.resolver.resolve_name(name_parts, context)
    
    def get_implementation_info(self) -> Dict[str, Any]:
        """
        Get information about the current resolver implementation.
        
        Returns:
            Dictionary with implementation details
        """
        info = {
            "type": self.implementation_type,
            "class": self.resolver.__class__.__name__,
            "module": self.resolver.__class__.__module__,
            "available_methods": [method for method in dir(self.resolver) if not method.startswith('_')]
        }
        
        # Add refactored-specific info
        if self.implementation_type == "refactored":
            info["specialized_visitors"] = {
                "simple_resolver": hasattr(self.resolver, 'simple_resolver'),
                "chain_resolver": hasattr(self.resolver, 'chain_resolver'),
                "inheritance_resolver": hasattr(self.resolver, 'inheritance_resolver'),
                "external_resolver": hasattr(self.resolver, 'external_resolver')
            }
        
        return info
    
    def clear_cache(self):
        """Clear resolver cache if available."""
        if hasattr(self.resolver, 'clear_cache'):
            self.resolver.clear_cache()
        elif hasattr(self.resolver, 'resolution_cache'):
            # For original implementation, clear the cache directly
            self.resolver.resolution_cache = {}
    
    def validate_resolution(self, fqn: str) -> bool:
        """
        Validate a resolved FQN.
        
        Args:
            fqn: Fully qualified name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if hasattr(self.resolver, 'validate_resolution'):
            return self.resolver.validate_resolution(fqn)
        elif hasattr(self.resolver, '_validate_resolution'):
            return self.resolver._validate_resolution(fqn)
        else:
            # Fallback validation
            return fqn is not None and len(fqn) > 0
    
    def __getattr__(self, name):
        """
        Delegate unknown attribute access to the wrapped resolver.
        
        This ensures compatibility with any resolver-specific methods.
        """
        return getattr(self.resolver, name)


def get_resolver_implementation_status() -> Dict[str, Any]:
    """
    Get the status of resolver implementations.
    
    Returns:
        Dictionary with implementation availability and details
    """
    status = {
        "original_available": True,  # Always available
        "refactored_available": _is_refactored_available(),
        "recommended": "refactored" if _is_refactored_available() else "original"
    }
    
    # Try to get more details about refactored implementation
    if status["refactored_available"]:
        try:
            from .resolver_refactored import RefactoredNameResolver
            status["refactored_class"] = RefactoredNameResolver.__name__
            status["refactored_module"] = RefactoredNameResolver.__module__
        except ImportError:
            status["refactored_available"] = False
    
    return status


# Main interface function for external use
def create_name_resolver(recon_data: Dict[str, Any], use_refactored: Optional[bool] = None) -> NameResolverCompatibilityWrapper:
    """
    Create a name resolver with compatibility wrapper.
    
    This is the main interface function that external code should use.
    
    Args:
        recon_data: Reconnaissance data for resolution
        use_refactored: None = auto-detect, True = force refactored, False = force original
        
    Returns:
        NameResolverCompatibilityWrapper instance
    """
    return NameResolverCompatibilityWrapper(recon_data, use_refactored)


# Legacy compatibility - maintain the original interface
NameResolver = NameResolverCompatibilityWrapper
