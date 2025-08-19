"""
Name Resolver Compatibility Layer - Code Atlas

Provides seamless switching between original and refactored resolver implementations.
Part of the Phase 3 refactoring following the progressive migration pattern.

This module maintains the existing NameResolver import interface while internally
routing to the best available implementation.
"""

from typing import Dict, List, Any, Optional


def get_resolver_info() -> Dict[str, Any]:
    """Get information about available resolver implementations."""
    try:
        from .resolver_refactored import RefactoredNameResolver
        refactored_available = True
    except ImportError:
        refactored_available = False
    
    try:
        from .resolver_original import NameResolver as OriginalNameResolver
        original_available = True
    except ImportError:
        original_available = False
    
    return {
        "original_available": original_available,
        "refactored_available": refactored_available,
        "recommended": "refactored" if refactored_available else "original",
        "version": "3.0-resolver-refactored" if refactored_available else "1.0-original"
    }


class NameResolver:
    """
    Compatibility wrapper for name resolution functionality.
    
    Automatically uses the best available implementation while maintaining
    the existing API contract that other modules depend on.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        """
        Initialize name resolver with compatibility layer.
        
        CRITICAL: Maintains exact same signature as original NameResolver
        to ensure all existing code continues to work unchanged.
        
        Args:
            recon_data: Reconnaissance data from previous pass
        """
        self.recon_data = recon_data
        info = get_resolver_info()
        
        # Auto-detect best available implementation
        use_refactored = info["refactored_available"]
        
        # Initialize the selected implementation
        if use_refactored:
            try:
                from .resolver_refactored import RefactoredNameResolver
                self._resolver = RefactoredNameResolver(recon_data)
                self._implementation = "refactored"
            except (ImportError, NotImplementedError):
                # Fallback to original if refactored fails
                from .resolver_original import NameResolver as OriginalNameResolver
                self._resolver = OriginalNameResolver(recon_data)
                self._implementation = "original"
        else:
            from .resolver_original import NameResolver as OriginalNameResolver
            self._resolver = OriginalNameResolver(recon_data)
            self._implementation = "original"
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name using the selected implementation.
        
        Maintains the exact same API contract as the original NameResolver.
        """
        return self._resolver.resolve_name(name_parts, context)
    
    def extract_name_parts(self, node) -> List[str]:
        """
        Extract name parts from AST node using the selected implementation.
        
        Maintains the exact same API contract as the original NameResolver.
        """
        return self._resolver.extract_name_parts(node)
    
    @property
    def implementation_info(self) -> str:
        """Get information about which implementation is currently active."""
        return f"resolver:{self._implementation}"


# For backwards compatibility and direct import scenarios
def create_name_resolver(recon_data: Dict[str, Any], use_refactored: Optional[bool] = None) -> NameResolver:
    """
    Factory function for creating NameResolver instances with implementation control.
    
    This provides an alternative way to get a resolver with explicit implementation choice
    while the main NameResolver class maintains API compatibility.
    
    Args:
        recon_data: Reconnaissance data from previous pass
        use_refactored: 
            - True: Force refactored implementation
            - False: Force original implementation  
            - None: Auto-detect best available implementation
    """
    # Create resolver normally (auto-detects)
    resolver = NameResolver(recon_data)
    
    # If specific implementation requested, override the auto-detection
    if use_refactored is not None:
        info = get_resolver_info()
        
        if use_refactored and info["refactored_available"]:
            try:
                from .resolver_refactored import RefactoredNameResolver
                resolver._resolver = RefactoredNameResolver(recon_data)
                resolver._implementation = "refactored"
            except (ImportError, NotImplementedError):
                print("[RESOLVER_COMPAT] Warning: Refactored implementation requested but failed, keeping original")
        elif not use_refactored and info["original_available"]:
            from .resolver_original import NameResolver as OriginalNameResolver
            resolver._resolver = OriginalNameResolver(recon_data)
            resolver._implementation = "original"
    
    return resolver


# Export the compatibility class as the main interface
__all__ = ['NameResolver', 'create_name_resolver', 'get_resolver_info']
