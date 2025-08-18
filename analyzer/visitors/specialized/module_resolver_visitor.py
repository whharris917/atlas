"""
Module Resolver Visitor - Phase 3 Fourth Implementation

Specialized visitor for module-level fallback resolution.
This is the final fallback resolver that assumes names belong to the current module.

Part of the Atlas Phase 3 refactoring to modularize the name resolution system.
"""

from typing import Dict, List, Optional, Any
from ...utils import LOG_LEVEL


class ModuleResolverVisitor:
    """
    Specialized resolver for module-level fallback resolution.
    
    This is the final fallback resolver that constructs FQNs by assuming
    names belong to the current module when no other resolver can handle them.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.resolution_count = 0
        
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """
        Check if this resolver can handle the given name.
        
        This is a fallback resolver, so it can always attempt resolution
        if we have a current module context.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing current_module
            
        Returns:
            True if we have a current module (always tries as fallback)
        """
        current_module = context.get('current_module')
        can_resolve = current_module is not None
        
        if LOG_LEVEL >= 3:
            print(f"      [MODULE_RESOLVER] can_resolve({base_name}): {can_resolve} (fallback, module: {current_module})")
        
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a name by assuming it belongs to the current module.
        
        This is a fallback resolution that constructs an FQN by combining
        the current module with the base name.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing current_module
            
        Returns:
            Module-qualified name (module.name) or None if no current module
        """
        current_module = context.get('current_module')
        if not current_module:
            if LOG_LEVEL >= 3:
                print(f"      [MODULE_RESOLVER] resolve({base_name}): None (no current module)")
            return None
        
        try:
            # Construct module-qualified name
            if current_module:
                result = f"{current_module}.{base_name}"
            else:
                result = base_name
            
            self.resolution_count += 1
            
            if LOG_LEVEL >= 3:
                print(f"      [MODULE_RESOLVER] resolve({base_name}): {result}")
            
            return result
            
        except Exception as e:
            if LOG_LEVEL >= 1:
                print(f"[MODULE_RESOLVER] Error resolving {base_name}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about this resolver's usage.
        
        Returns:
            Dictionary containing resolution statistics
        """
        return {
            "resolver_type": "ModuleResolver",
            "resolutions_performed": self.resolution_count,
            "description": "Fallback resolver for current module names"
        }
    
    def reset_stats(self):
        """Reset resolution statistics."""
        self.resolution_count = 0
