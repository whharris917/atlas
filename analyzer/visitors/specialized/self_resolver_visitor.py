"""
Self Resolver Visitor - Phase 3 Second Implementation

Specialized visitor for resolving 'self' references to the current class.
Handles the specific case where 'self' refers to the class context.

Part of the Atlas Phase 3 refactoring to modularize the name resolution system.
"""

from typing import Dict, List, Optional, Any
from ...utils import LOG_LEVEL


class SelfResolverVisitor:
    """
    Specialized resolver for 'self' reference resolution.
    
    Handles the specific case where the name 'self' should resolve
    to the current class context within method definitions.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.resolution_count = 0
        
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """
        Check if this resolver can handle the given name.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing current_class and other info
            
        Returns:
            True if this resolver can handle the name (base_name == 'self' and we have a current class)
        """
        can_resolve = base_name == "self" and context.get('current_class') is not None
        
        if LOG_LEVEL >= 3:
            current_class = context.get('current_class', 'None')
            print(f"      [SELF_RESOLVER] can_resolve({base_name}): {can_resolve} (current_class: {current_class})")
        
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve 'self' to the current class.
        
        Args:
            base_name: The name to resolve (should be 'self')
            context: Resolution context containing current_class
            
        Returns:
            Current class FQN or None if no current class
        """
        if base_name != "self":
            if LOG_LEVEL >= 2:
                print(f"[SELF_RESOLVER] Called with non-self name: {base_name}")
            return None
        
        current_class = context.get('current_class')
        if not current_class:
            if LOG_LEVEL >= 3:
                print(f"      [SELF_RESOLVER] resolve({base_name}): None (no current class)")
            return None
        
        try:
            self.resolution_count += 1
            
            if LOG_LEVEL >= 3:
                print(f"      [SELF_RESOLVER] resolve({base_name}): {current_class}")
            
            return current_class
            
        except Exception as e:
            if LOG_LEVEL >= 1:
                print(f"[SELF_RESOLVER] Error resolving {base_name}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about this resolver's usage.
        
        Returns:
            Dictionary containing resolution statistics
        """
        return {
            "resolver_type": "SelfResolver",
            "resolutions_performed": self.resolution_count,
            "description": "Resolves 'self' references to current class"
        }
    
    def reset_stats(self):
        """Reset resolution statistics."""
        self.resolution_count = 0
