"""
Refactored Name Resolver - Phase 3 Orchestrating Implementation

Main resolver that orchestrates specialized resolver visitors for different concerns.
This replaces the monolithic NameResolver with a modular approach while maintaining
identical functionality and interfaces.

Part of the Atlas Phase 3 refactoring to modularize the name resolution system.
"""

from typing import Dict, List, Optional, Any
from .specialized.local_resolver_visitor import LocalVariableResolverVisitor
from .specialized.self_resolver_visitor import SelfResolverVisitor
from .specialized.import_resolver_visitor import ImportResolverVisitor
from .specialized.module_resolver_visitor import ModuleResolverVisitor
from ..utils.logger import get_logger
from ..utils import LOG_LEVEL


class RefactoredNameResolver:
    """
    Refactored name resolver that orchestrates specialized resolver visitors.
    
    This replaces the monolithic NameResolver with a clean, modular approach
    while preserving all existing functionality and maintaining the same interface.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        """
        Initialize the refactored resolver with specialized visitors.
        
        Args:
            recon_data: Reconnaissance data containing classes, functions, imports, etc.
        """
        self.recon_data = recon_data
        self.logger = get_logger()
        
        # Initialize specialized resolver visitors in order of precedence
        # This order matches the original resolver's strategy order
        self.resolvers = [
            LocalVariableResolverVisitor(self.logger),
            SelfResolverVisitor(self.logger),
            ImportResolverVisitor(recon_data, self.logger),
            ModuleResolverVisitor(self.logger)  # Fallback resolver (always last)
        ]
        
        # Statistics tracking
        self.total_resolutions = 0
        self.failed_resolutions = 0
        self.cache_hits = 0
        
        # Simple resolution cache for performance
        self.resolution_cache = {}
        
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name using layered resolver strategy with comprehensive logging.
        
        This maintains the exact same interface and behavior as the original resolver
        while using the new modular architecture internally.
        
        Args:
            name_parts: List of name parts to resolve (e.g., ['obj', 'method'])
            context: Resolution context with symbol tables, current class, etc.
            
        Returns:
            Resolved fully qualified name or None if resolution fails
        """
        if not name_parts:
            if LOG_LEVEL >= 1:
                print("    [RESOLVE] FAILED No name parts provided")
            self.failed_resolutions += 1
            return None
        
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVE] Attempting to resolve: {name_parts}")
        
        # Layer 1: Simple resolution for single names
        if len(name_parts) == 1:
            result = self._resolve_simple(name_parts[0], context)
            if result:
                if LOG_LEVEL >= 1:
                    print(f"    [RESOLVE] RESOLVED to: {result}")
                self.total_resolutions += 1
                return result
            else:
                if LOG_LEVEL >= 1:
                    print(f"    [RESOLVE] FAILED to resolve: {name_parts[0]}")
                self.failed_resolutions += 1
                return None
        
        # Layer 2: Complex chain resolution
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVE] Chain resolution needed for: {name_parts}")
        result = self._resolve_chain(name_parts, context)
        if result:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVE] RESOLVED to: {result}")
            self.total_resolutions += 1
            return result
        else:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVE] FAILED to resolve chain: {'.'.join(name_parts)}")
            self.failed_resolutions += 1
            return None
    
    def _resolve_simple(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve simple single name using specialized resolver visitors.
        
        Args:
            name: Single name to resolve
            context: Resolution context
            
        Returns:
            Resolved FQN or None
        """
        if LOG_LEVEL >= 3:
            print(f"      [RESOLVE_SIMPLE] Resolving base: {name}")
        
        # Check cache first
        cache_key = f"simple:{name}:{context.get('current_module', '')}:{context.get('current_class', '')}"
        if cache_key in self.resolution_cache:
            result = self.resolution_cache[cache_key]
            self.cache_hits += 1
            if LOG_LEVEL >= 3:
                print(f"      [CACHE] Hit for {name}: {result}")
            return result
        
        # Try each specialized resolver in order
        for i, resolver in enumerate(self.resolvers):
            resolver_name = resolver.__class__.__name__
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] Trying resolver {i+1}: {resolver_name}")
            
            try:
                if resolver.can_resolve(name, context):
                    result = resolver.resolve(name, context)
                    if result and self._validate_resolution(result):
                        if LOG_LEVEL >= 3:
                            print(f"      [STRATEGY] SUCCESS {resolver_name} succeeded: {name} -> {result}")
                            print(f"      [VALIDATION] PASS Resolution validated")
                        
                        # Cache successful resolution
                        self.resolution_cache[cache_key] = result
                        return result
                    else:
                        if LOG_LEVEL >= 3:
                            print(f"      [STRATEGY] FAIL {resolver_name} failed validation")
                else:
                    if LOG_LEVEL >= 3:
                        print(f"      [STRATEGY] SKIP {resolver_name} cannot resolve")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[RESOLVER] Error in {resolver_name}: {e}")
                if LOG_LEVEL >= 3:
                    print(f"      [STRATEGY] ERROR {resolver_name} threw exception: {e}")
        
        if LOG_LEVEL >= 3:
            print(f"      [RESOLVE_SIMPLE] FAILED All resolvers failed for: {name}")
        
        # Cache failed resolution to avoid repeated work
        self.resolution_cache[cache_key] = None
        return None
    
    def _resolve_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve complex attribute chains with enhanced attribute support.
        
        Args:
            name_parts: List of name parts for the chain
            context: Resolution context
            
        Returns:
            Resolved FQN or None
        """
        # Resolve base
        base_name = name_parts[0]
        if LOG_LEVEL >= 3:
            print(f"      [CHAIN] Resolving base: {base_name}")
        
        base_fqn = self._resolve_simple(base_name, context)
        if not base_fqn:
            if LOG_LEVEL >= 3:
                print(f"      [CHAIN] FAILED to resolve base: {base_name}")
            return None
        
        if LOG_LEVEL >= 3:
            print(f"      [CHAIN] Base resolved: {base_name} -> {base_fqn}")
        
        # Walk the chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            if LOG_LEVEL >= 3:
                print(f"      [CHAIN] Step {i}: Resolving {current_fqn}.{attr}")
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                if LOG_LEVEL >= 3:
                    print(f"      [CHAIN] FAILED at step {i}: .{attr}")
                return None
            if LOG_LEVEL >= 3:
                print(f"      [CHAIN] Step {i} resolved: {current_fqn}")
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve attribute in context of given FQN with inheritance, attribute support, and external library support.
        
        This method maintains the same complex attribute resolution logic as the original resolver.
        
        Args:
            context_fqn: The FQN context for attribute resolution
            attr: The attribute name to resolve
            context: Resolution context
            
        Returns:
            Resolved attribute FQN or None
        """
        candidate = f"{context_fqn}.{attr}"
        if LOG_LEVEL >= 3:
            print(f"        [ATTRIBUTE] Resolving attribute: {context_fqn}.{attr}")
        
        # Check if candidate exists directly
        if self._validate_resolution(candidate):
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] Direct match found: {candidate}")
            return candidate
        
        # Try inheritance-aware resolution for class contexts
        if context_fqn in self.recon_data.get('classes', {}):
            inheritance_result = self._resolve_through_inheritance(context_fqn, attr)
            if inheritance_result:
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] Inheritance resolution: {inheritance_result}")
                return inheritance_result
        
        # Try external library attribute resolution
        external_result = self._resolve_external_attribute(context_fqn, attr)
        if external_result:
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] External attribute: {external_result}")
            return external_result
        
        if LOG_LEVEL >= 3:
            print(f"        [ATTRIBUTE] FAILED to resolve: {context_fqn}.{attr}")
        return None
    
    def _resolve_through_inheritance(self, class_fqn: str, attr: str) -> Optional[str]:
        """
        Resolve attribute through class inheritance hierarchy.
        
        Args:
            class_fqn: Class FQN to search
            attr: Attribute to find
            
        Returns:
            Resolved attribute FQN or None
        """
        class_info = self.recon_data.get('classes', {}).get(class_fqn)
        if not class_info:
            return None
        
        # Check parent classes
        for parent in class_info.get('inherits_from', []):
            candidate = f"{parent}.{attr}"
            if self._validate_resolution(candidate):
                return candidate
            
            # Recursive inheritance check
            inherited = self._resolve_through_inheritance(parent, attr)
            if inherited:
                return inherited
        
        return None
    
    def _resolve_external_attribute(self, context_fqn: str, attr: str) -> Optional[str]:
        """
        Resolve external library attributes.
        
        Args:
            context_fqn: Context FQN
            attr: Attribute name
            
        Returns:
            Resolved external attribute or None
        """
        # Check if context is an external class
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_class_fqn == context_fqn or ext_info.get("local_alias") == context_fqn.split('.')[-1]:
                # Assume external attribute exists
                return f"{ext_class_fqn}.{attr}"
        
        return None
    
    def _validate_resolution(self, fqn: str) -> bool:
        """
        Validate that a resolved FQN is legitimate.
        
        Args:
            fqn: Fully qualified name to validate
            
        Returns:
            True if FQN appears to be valid
        """
        if not fqn:
            return False
        
        # Check against known entities in recon data
        if fqn in self.recon_data.get('classes', {}):
            return True
        if fqn in self.recon_data.get('functions', {}):
            return True
        if fqn in self.recon_data.get('state', {}):
            return True
        
        # Check external entities
        if fqn in self.recon_data.get('external_classes', {}):
            return True
        if fqn in self.recon_data.get('external_functions', {}):
            return True
        
        # For now, assume other FQNs are valid (matches original behavior)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about resolver usage.
        
        Returns:
            Dictionary containing resolution statistics
        """
        resolver_stats = {}
        for resolver in self.resolvers:
            resolver_type = resolver.__class__.__name__
            resolver_stats[resolver_type] = resolver.get_stats()
        
        return {
            "resolver_type": "RefactoredNameResolver",
            "total_resolutions": self.total_resolutions,
            "failed_resolutions": self.failed_resolutions,
            "cache_hits": self.cache_hits,
            "cache_size": len(self.resolution_cache),
            "specialized_resolvers": resolver_stats,
            "description": "Modular name resolver with specialized visitor components"
        }
    
    def reset_stats(self):
        """Reset all statistics."""
        self.total_resolutions = 0
        self.failed_resolutions = 0
        self.cache_hits = 0
        self.resolution_cache.clear()
        
        for resolver in self.resolvers:
            resolver.reset_stats()
