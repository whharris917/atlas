"""
Resolver Compatibility Layer - Phase 3 Progressive Migration

Provides seamless switching between original and refactored resolver implementations
while maintaining 100% backward compatibility during the transition.

This follows the proven pattern from Phases 1-2 for zero-disruption migration.
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Try to import refactored resolver components
REFACTORED_AVAILABLE = False
RefactoredNameResolver = None

def _try_import_refactored():
    """Lazy import of refactored resolver to avoid circular imports."""
    global REFACTORED_AVAILABLE, RefactoredNameResolver
    
    if RefactoredNameResolver is not None:
        return RefactoredNameResolver
    
    try:
        from .visitors.resolver_refactored import RefactoredNameResolver
        REFACTORED_AVAILABLE = True
        return RefactoredNameResolver
    except ImportError as e:
        # Debug the import error
        print(f"[RESOLVER_COMPAT] Import error: {e}")
        REFACTORED_AVAILABLE = False
        return None

# Import original resolver
from .resolver import NameResolver as OriginalNameResolver


class CompatibilityNameResolver:
    """
    Compatibility wrapper that can use either original or refactored resolver.
    
    Provides the exact same interface as the original NameResolver while
    allowing progressive migration to the refactored implementation.
    """
    
    def __init__(self, recon_data: Dict[str, Any], use_refactored: Optional[bool] = None):
        """
        Initialize resolver with automatic or manual implementation selection.
        
        Args:
            recon_data: Reconnaissance data for name resolution
            use_refactored: True=use refactored, False=use original, None=auto-select
        """
        self.recon_data = recon_data
        
        # Determine which implementation to use
        if use_refactored is None:
            # Auto-select: use refactored if available, otherwise original
            RefactoredNameResolver = _try_import_refactored()
            self.use_refactored = RefactoredNameResolver is not None
        else:
            # Manual selection
            RefactoredNameResolver = _try_import_refactored() if use_refactored else None
            self.use_refactored = use_refactored and RefactoredNameResolver is not None
        
        # Initialize the selected implementation
        if self.use_refactored and RefactoredNameResolver is not None:
            self.resolver = RefactoredNameResolver(recon_data)
            self.implementation_name = "refactored"
        else:
            self.resolver = OriginalNameResolver(recon_data)
            self.implementation_name = "original"
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name using the selected implementation.
        
        Args:
            name_parts: List of name parts to resolve (e.g., ['obj', 'method'])
            context: Resolution context with symbol tables, current class, etc.
            
        Returns:
            Resolved fully qualified name or None
        """
        return self.resolver.resolve_name(name_parts, context)
    
    def extract_name_parts(self, node):
        """
        Extract name parts from AST node.
        
        This method is required by the analysis visitor and delegates to the underlying resolver.
        """
        # Delegate to the underlying resolver's extract_name_parts method
        if hasattr(self.resolver, 'extract_name_parts'):
            return self.resolver.extract_name_parts(node)
        else:
            # Fallback implementation for compatibility
            return self._extract_name_parts_fallback(node)
    
    def _extract_name_parts_fallback(self, node):
        """Fallback name extraction for compatibility."""
        import ast
        
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
                return parts
        return None
    
    def get_implementation_info(self) -> Dict[str, Any]:
        """
        Get information about the current resolver implementation.
        
        Returns:
            Dictionary with implementation details
        """
        # Check current availability
        RefactoredNameResolver = _try_import_refactored()
        available = RefactoredNameResolver is not None
        
        info = {
            "implementation": self.implementation_name,
            "refactored_available": available,
            "version": "resolver_compat_v1.0"
        }
        
        # Add specific implementation info if available
        if hasattr(self.resolver, 'get_stats'):
            info["resolver_stats"] = self.resolver.get_stats()
        
        return info


def create_name_resolver(recon_data: Dict[str, Any], use_refactored: Optional[bool] = None) -> CompatibilityNameResolver:
    """
    Factory function to create a name resolver with progressive migration support.
    
    Args:
        recon_data: Reconnaissance data for name resolution
        use_refactored: Implementation preference (None=auto, True=refactored, False=original)
        
    Returns:
        CompatibilityNameResolver instance
    """
    return CompatibilityNameResolver(recon_data, use_refactored)


def get_resolver_info() -> Dict[str, Any]:
    """
    Get information about available resolver implementations.
    
    Returns:
        Dictionary with resolver availability and configuration
    """
    # Try to determine availability dynamically
    RefactoredNameResolver = _try_import_refactored()
    available = RefactoredNameResolver is not None
    
    return {
        "refactored_available": available,
        "original_available": True,  # Always available
        "recommended": "refactored" if available else "original",
        "progressive_migration": True,
        "compatibility_version": "1.0"
    }


# Backward compatibility function
def get_name_resolver(recon_data: Dict[str, Any]) -> CompatibilityNameResolver:
    """
    Backward compatibility function that maintains the original interface.
    
    Args:
        recon_data: Reconnaissance data
        
    Returns:
        Name resolver using the best available implementation
    """
    return create_name_resolver(recon_data, use_refactored=None)


if __name__ == "__main__":
    # Simple test of the compatibility layer
    print("=== Resolver Compatibility Layer Test ===")
    
    # Mock recon data for testing
    mock_recon_data = {
        "classes": {},
        "functions": {},
        "external_classes": {},
        "external_functions": {}
    }
    
    # Test resolver creation
    resolver = create_name_resolver(mock_recon_data)
    info = resolver.get_implementation_info()
    
    print(f"Implementation: {info['implementation']}")
    print(f"Refactored Available: {info['refactored_available']}")
    print(f"Version: {info['version']}")
    
    # Test resolver info
    resolver_info = get_resolver_info()
    print(f"Recommended: {resolver_info['recommended']}")
    print(f"Progressive Migration: {resolver_info['progressive_migration']}")
    
    print("✅ Compatibility layer working correctly!")
