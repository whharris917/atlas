"""
Local Variable Resolver Visitor - Phase 3 First Implementation

Specialized visitor for resolving names from local variable symbol tables.
This is the first of four specialized resolver visitors to replace the monolithic resolver.

Part of the Atlas Phase 3 refactoring to modularize the name resolution system.
"""

from typing import Dict, List, Optional, Any
from ...utils.logger import get_logger


class LocalVariableResolverVisitor:
    """
    Specialized resolver for local variable symbol table resolution.
    
    Handles resolution of names that exist in the current function's symbol table,
    typically variables declared within the current function scope.
    """
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.resolution_count = 0
        
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """
        Check if this resolver can handle the given name.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing symbol_manager and other info
            
        Returns:
            True if this resolver can handle the name, False otherwise
        """
        symbol_manager = context.get('symbol_manager')
        can_resolve = symbol_manager and symbol_manager.get_variable_type(base_name) is not None
        
        if self.logger and hasattr(self.logger, 'log_level') and getattr(self.logger, 'log_level', 0) >= 3:
            if hasattr(self.logger, 'debug'):
                self.logger.debug(f"      [LOCAL_RESOLVER] can_resolve({base_name}): {can_resolve}")
            else:
                print(f"      [LOCAL_RESOLVER] can_resolve({base_name}): {can_resolve}")
        
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a name using local variable symbol tables.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing symbol_manager
            
        Returns:
            Resolved fully qualified name or None if resolution fails
        """
        symbol_manager = context.get('symbol_manager')
        if not symbol_manager:
            if self.logger:
                # Use print fallback if logger doesn't have warning method
                if hasattr(self.logger, 'warning'):
                    self.logger.warning(f"[LOCAL_RESOLVER] No symbol manager in context for {base_name}")
                else:
                    print(f"[LOCAL_RESOLVER] No symbol manager in context for {base_name}")
            return None
        
        try:
            result = symbol_manager.get_variable_type(base_name)
            
            if result:
                self.resolution_count += 1
                
                if self.logger and hasattr(self.logger, 'log_level') and getattr(self.logger, 'log_level', 0) >= 3:
                    if hasattr(self.logger, 'debug'):
                        self.logger.debug(f"      [LOCAL_RESOLVER] resolve({base_name}): {result}")
                    else:
                        print(f"      [LOCAL_RESOLVER] resolve({base_name}): {result}")
                
                return result
            else:
                if self.logger and hasattr(self.logger, 'log_level') and getattr(self.logger, 'log_level', 0) >= 3:
                    if hasattr(self.logger, 'debug'):
                        self.logger.debug(f"      [LOCAL_RESOLVER] resolve({base_name}): None (not in symbol table)")
                    else:
                        print(f"      [LOCAL_RESOLVER] resolve({base_name}): None (not in symbol table)")
                
                return None
                
        except Exception as e:
            if self.logger:
                # Use print fallback if logger doesn't have error method
                if hasattr(self.logger, 'error'):
                    self.logger.error(f"[LOCAL_RESOLVER] Error resolving {base_name}: {e}")
                else:
                    print(f"[LOCAL_RESOLVER] Error resolving {base_name}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about this resolver's usage.
        
        Returns:
            Dictionary containing resolution statistics
        """
        return {
            "resolver_type": "LocalVariableResolver",
            "resolutions_performed": self.resolution_count,
            "description": "Resolves names from local variable symbol tables"
        }
    
    def reset_stats(self):
        """Reset resolution statistics."""
        self.resolution_count = 0
