"""
Enhanced Name Resolver Compatibility Layer - Code Atlas

UPDATED: Adds support for testing resolver_reorganized.py safely alongside
the existing original and refactored implementations. Now supports environment
variable control from atlas.py --resolver flag.

This maintains the existing NameResolver import interface while internally
routing to the best available implementation, now including the reorganized
proof-of-concept implementation for testing.
"""

import os
from typing import Dict, List, Any, Optional


def get_resolver_info() -> Dict[str, Any]:
    """Get information about available resolver implementations."""
    implementations = {}
    
    # Check for reorganized implementation (proof of concept)
    try:
        from .resolver_reorganized import NameResolver as ReorganizedNameResolver
        implementations["reorganized"] = True
    except ImportError:
        implementations["reorganized"] = False
    
    # Check for refactored implementation (placeholder)
    try:
        from .resolver_refactored import RefactoredNameResolver
        implementations["refactored"] = True
    except ImportError:
        implementations["refactored"] = False
    
    # Check for original implementation
    try:
        from .resolver_original import NameResolver as OriginalNameResolver
        implementations["original"] = True
    except ImportError:
        implementations["original"] = False
    
    # Determine recommended implementation
    if implementations["reorganized"]:
        recommended = "reorganized"
        version = "3.1-reorganized"
    elif implementations["refactored"]:
        recommended = "refactored"
        version = "3.0-refactored"
    else:
        recommended = "original"
        version = "1.0-original"
    
    return {
        "original_available": implementations["original"],
        "refactored_available": implementations["refactored"],
        "reorganized_available": implementations["reorganized"],
        "recommended": recommended,
        "version": version,
        "all_implementations": implementations
    }


class NameResolver:
    """
    Enhanced compatibility wrapper for name resolution functionality.
    
    Now supports testing the reorganized implementation alongside original
    and refactored versions. Maintains identical API contract.
    
    Supports environment variable control from atlas.py --resolver flag.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        """
        Initialize name resolver with enhanced compatibility layer.
        
        CRITICAL: Maintains exact same signature as original NameResolver
        to ensure all existing code continues to work unchanged.
        
        Args:
            recon_data: Reconnaissance data from previous pass
        """
        self.recon_data = recon_data
        
        # Check for environment variable from atlas.py --resolver flag
        requested_implementation = os.environ.get('ATLAS_RESOLVER_IMPLEMENTATION', 'auto')
        
        if requested_implementation == 'auto':
            # Use normal auto-detection
            info = get_resolver_info()
            if info["reorganized_available"]:
                implementation_choice = "reorganized"
            elif info["refactored_available"]:
                implementation_choice = "refactored"
            else:
                implementation_choice = "original"
        else:
            # Use explicitly requested implementation
            implementation_choice = requested_implementation
        
        self._implementation = self._initialize_implementation(implementation_choice)
    
    def _initialize_implementation(self, choice: str) -> str:
        """Initialize the selected implementation with fallback logic."""
        
        # Try reorganized implementation
        if choice == "reorganized":
            try:
                from .resolver_reorganized import NameResolver as ReorganizedNameResolver
                self._resolver = ReorganizedNameResolver(self.recon_data)
                print(f"[RESOLVER_COMPAT] Using reorganized resolver implementation")
                return "reorganized"
            except (ImportError, Exception) as e:
                print(f"[RESOLVER_COMPAT] Warning: Reorganized implementation failed ({e}), falling back")
                return self._initialize_implementation("refactored")
        
        # Try refactored implementation
        elif choice == "refactored":
            try:
                from .resolver_refactored import RefactoredNameResolver
                self._resolver = RefactoredNameResolver(self.recon_data)
                print(f"[RESOLVER_COMPAT] Using refactored resolver implementation")
                return "refactored"
            except (ImportError, NotImplementedError) as e:
                print(f"[RESOLVER_COMPAT] Warning: Refactored implementation failed ({e}), falling back to original")
                return self._initialize_implementation("original")
        
        # Fall back to original implementation
        else:
            from .resolver_original import NameResolver as OriginalNameResolver
            self._resolver = OriginalNameResolver(self.recon_data)
            print(f"[RESOLVER_COMPAT] Using original resolver implementation")
            return "original"
    
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
    
    def get_implementation_details(self) -> Dict[str, Any]:
        """Get detailed implementation information for debugging."""
        info = get_resolver_info()
        info["active_implementation"] = self._implementation
        
        # Add implementation-specific details if available
        if hasattr(self._resolver, 'get_statistics'):
            info["resolver_statistics"] = self._resolver.get_statistics()
        
        return info


# Enhanced factory function with explicit implementation control
def create_name_resolver(recon_data: Dict[str, Any], use_implementation: Optional[str] = None) -> NameResolver:
    """
    Enhanced factory function for creating NameResolver instances with explicit implementation control.
    
    Args:
        recon_data: Reconnaissance data from previous pass
        use_implementation: 
            - "reorganized": Force reorganized implementation (for testing)
            - "refactored": Force refactored implementation
            - "original": Force original implementation  
            - None: Auto-detect best available implementation
    """
    # Temporarily set environment variable if specific implementation requested
    old_env = os.environ.get('ATLAS_RESOLVER_IMPLEMENTATION')
    if use_implementation is not None:
        os.environ['ATLAS_RESOLVER_IMPLEMENTATION'] = use_implementation
    
    try:
        resolver = NameResolver(recon_data)
        return resolver
    finally:
        # Restore original environment variable
        if old_env is not None:
            os.environ['ATLAS_RESOLVER_IMPLEMENTATION'] = old_env
        elif 'ATLAS_RESOLVER_IMPLEMENTATION' in os.environ:
            del os.environ['ATLAS_RESOLVER_IMPLEMENTATION']


# Export the compatibility class as the main interface
__all__ = ['NameResolver', 'create_name_resolver', 'get_resolver_info']
