"""
Import Resolver Visitor - Phase 3 Third Implementation

Specialized visitor for resolving names from import aliases and external libraries.
Handles both direct import map resolution and external library resolution.

Part of the Atlas Phase 3 refactoring to modularize the name resolution system.
"""

from typing import Dict, List, Optional, Any
from ...utils import LOG_LEVEL


class ImportResolverVisitor:
    """
    Specialized resolver for import aliases and external library resolution.
    
    Handles resolution of names that come from:
    1. Direct import statements (import_map)
    2. External library classes and functions
    """
    
    def __init__(self, recon_data: Dict[str, Any], logger=None):
        self.recon_data = recon_data
        self.logger = logger
        self.resolution_count = 0
        self.import_resolutions = 0
        self.external_resolutions = 0
        
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """
        Check if this resolver can handle the given name.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing import_map and other info
            
        Returns:
            True if this resolver can handle the name via imports or external libraries
        """
        import_map = context.get('import_map', {})
        can_resolve_import = base_name in import_map
        can_resolve_external = self._can_resolve_external(base_name)
        can_resolve = can_resolve_import or can_resolve_external
        
        if LOG_LEVEL >= 3:
            print(f"      [IMPORT_RESOLVER] can_resolve({base_name}): {can_resolve} (import: {can_resolve_import}, external: {can_resolve_external})")
        
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a name using import maps and external libraries.
        
        Args:
            base_name: The name to resolve
            context: Resolution context containing import_map
            
        Returns:
            Resolved fully qualified name or None if resolution fails
        """
        import_map = context.get('import_map', {})
        
        try:
            # First try direct import map
            if base_name in import_map:
                result = import_map[base_name]
                if result:
                    self.resolution_count += 1
                    self.import_resolutions += 1
                    
                    if LOG_LEVEL >= 3:
                        print(f"      [IMPORT_RESOLVER] resolve({base_name}): {result} (from import map)")
                    
                    return result
            
            # Then try external library resolution
            external_result = self._resolve_external(base_name)
            if external_result:
                self.resolution_count += 1
                self.external_resolutions += 1
                
                if LOG_LEVEL >= 3:
                    print(f"      [IMPORT_RESOLVER] resolve({base_name}): {external_result} (external)")
                
                return external_result
            
            # Resolution failed
            if LOG_LEVEL >= 3:
                print(f"      [IMPORT_RESOLVER] resolve({base_name}): None (not found)")
            
            return None
            
        except Exception as e:
            if LOG_LEVEL >= 1:
                print(f"[IMPORT_RESOLVER] Error resolving {base_name}: {e}")
            return None
    
    def _can_resolve_external(self, name: str) -> bool:
        """
        Check if name can be resolved from external libraries.
        
        Args:
            name: Name to check
            
        Returns:
            True if name exists in external classes or functions
        """
        try:
            # Check if it's a direct external class or function alias
            for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
                if ext_info.get("local_alias") == name:
                    return True
            
            for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
                if ext_info.get("local_alias") == name:
                    return True
            
            return False
            
        except Exception as e:
            if LOG_LEVEL >= 1:
                print(f"[IMPORT_RESOLVER] Error checking external resolution for {name}: {e}")
            return False
    
    def _resolve_external(self, name: str) -> Optional[str]:
        """
        Resolve name from external library imports.
        
        Args:
            name: Name to resolve
            
        Returns:
            Resolved FQN or None if not found
        """
        try:
            # Check external classes
            for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
                if ext_info.get("local_alias") == name:
                    return ext_class_fqn
            
            # Check external functions
            for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
                if ext_info.get("local_alias") == name:
                    return ext_func_fqn
            
            return None
            
        except Exception as e:
            if LOG_LEVEL >= 1:
                print(f"[IMPORT_RESOLVER] Error resolving external {name}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about this resolver's usage.
        
        Returns:
            Dictionary containing resolution statistics
        """
        return {
            "resolver_type": "ImportResolver",
            "resolutions_performed": self.resolution_count,
            "import_resolutions": self.import_resolutions,
            "external_resolutions": self.external_resolutions,
            "description": "Resolves names from import aliases and external libraries"
        }
    
    def reset_stats(self):
        """Reset resolution statistics."""
        self.resolution_count = 0
        self.import_resolutions = 0
        self.external_resolutions = 0
