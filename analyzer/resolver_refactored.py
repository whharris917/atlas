"""
Refactored Name Resolver - Code Atlas

Main name resolution orchestrator that coordinates specialized resolution visitors.
This replaces the monolithic NameResolver with a modular approach.
"""

from typing import Dict, List, Any, Optional

# Import core components - handle both relative and absolute imports
try:
    from .utils import LOG_LEVEL
except ImportError:
    try:
        from utils import LOG_LEVEL
    except ImportError:
        # Fallback if utils not available
        LOG_LEVEL = 1

# Import specialized resolution visitors - handle import errors gracefully
try:
    from .visitors.specialized.simple_resolution_visitor import SimpleResolutionVisitor
    from .visitors.specialized.chain_resolution_visitor import ChainResolutionVisitor
    from .visitors.specialized.inheritance_resolution_visitor import InheritanceResolutionVisitor
    from .visitors.specialized.external_resolution_visitor import ExternalResolutionVisitor
except ImportError:
    try:
        from visitors.specialized.simple_resolution_visitor import SimpleResolutionVisitor
        from visitors.specialized.chain_resolution_visitor import ChainResolutionVisitor
        from visitors.specialized.inheritance_resolution_visitor import InheritanceResolutionVisitor
        from visitors.specialized.external_resolution_visitor import ExternalResolutionVisitor
    except ImportError as e:
        print(f"Warning: Could not import specialized visitors: {e}")
        # We'll handle this in the class initialization


class RefactoredNameResolver:
    """
    Refactored name resolution engine that orchestrates specialized resolution visitors.
    
    This replaces the monolithic NameResolver with a clean, modular approach
    while preserving all existing functionality.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
        
        # Initialize specialized resolution visitors
        try:
            self.simple_resolver = SimpleResolutionVisitor(recon_data)
            self.chain_resolver = ChainResolutionVisitor(recon_data)
            self.inheritance_resolver = InheritanceResolutionVisitor(recon_data)
            self.external_resolver = ExternalResolutionVisitor(recon_data)
        except NameError:
            # Fallback if specialized visitors couldn't be imported
            raise ImportError("Specialized resolution visitors are not available. Please ensure all visitor files are properly placed in the visitors/specialized/ directory.")
        
        # Resolution cache for performance
        self.resolution_cache = {}
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Main entry point for name resolution using specialized visitors.
        
        Args:
            name_parts: List of name components (e.g., ['self', 'method'])
            context: Resolution context with current module, class, imports, etc.
            
        Returns:
            Fully qualified name (FQN) if resolved, None otherwise
        """
        if not name_parts:
            if LOG_LEVEL >= 1:
                print("    [RESOLVE] FAILED No name parts provided")
            return None
        
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVE] Attempting to resolve: {name_parts}")
        
        # Cache check for performance
        cache_key = tuple(name_parts)
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if LOG_LEVEL >= 2:
                print(f"    [CACHE] {'.'.join(name_parts)} -> {cached_result} (cached)")
            return cached_result
        
        # Determine resolution strategy based on name complexity
        if len(name_parts) == 1:
            # Simple name resolution
            result = self.simple_resolver.resolve(name_parts[0], context)
        else:
            # Complex chain resolution
            result = self.chain_resolver.resolve(name_parts, context)
        
        # Cache the result
        self.resolution_cache[cache_key] = result
        
        if result:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVE] RESOLVED to: {result}")
        else:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVE] FAILED to resolve: {'.'.join(name_parts)}")
        
        return result
    
    def resolve_inheritance(self, class_fqn: str, attr_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve attributes through inheritance chains.
        
        Delegates to the specialized inheritance resolution visitor.
        """
        return self.inheritance_resolver.resolve_inherited_attribute(class_fqn, attr_name, context)
    
    def resolve_external(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve names from external libraries.
        
        Delegates to the specialized external resolution visitor.
        """
        return self.external_resolver.resolve_external_name(name, context)
    
    def validate_resolution(self, fqn: str) -> bool:
        """
        Validate that a resolved FQN exists in the reconnaissance data.
        
        This method provides a central point for validation logic.
        """
        if not fqn:
            return False
        
        # Check if FQN exists in any of the reconnaissance data structures
        if fqn in self.recon_data.get("functions", {}):
            return True
        
        if fqn in self.recon_data.get("classes", {}):
            return True
        
        if fqn in self.recon_data.get("state", {}):
            return True
        
        if fqn in self.recon_data.get("external_classes", {}):
            return True
        
        if fqn in self.recon_data.get("external_functions", {}):
            return True
        
        # Allow module-level names (fallback validation)
        if "." in fqn:
            module_part = fqn.rsplit(".", 1)[0]
            return module_part in self.recon_data.get("imports", {}).values()
        
        return False
    
    def clear_cache(self):
        """Clear the resolution cache - useful for testing or memory management."""
        self.resolution_cache.clear()
