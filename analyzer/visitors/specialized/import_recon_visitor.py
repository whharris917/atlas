"""
Import Reconnaissance Visitor - Code Atlas

Specialized visitor for processing import statements and external library detection.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils.logger import AnalysisLogger
from ...utils import EXTERNAL_LIBRARY_ALLOWLIST


class ImportReconVisitor:
    """Specialized visitor for import processing during reconnaissance pass."""
    
    def __init__(self, module_name: str, logger: AnalysisLogger):
        self.module_name = module_name
        self.logger = logger
        
        # External library tracking
        self.external_classes = {}
        self.external_functions = {}
    
    def _is_camel_case(self, name: str) -> bool:
        """Check if a name follows CamelCase convention (likely a class)."""
        return name and name[0].isupper() and '_' not in name and not name.isupper()
    
    def _process_import(self, module_name: str, imported_name: str, alias: Optional[str] = None):
        """Process an import and add to external catalogs if from approved library."""
        if module_name in EXTERNAL_LIBRARY_ALLOWLIST:
            fqn = f"{module_name}.{imported_name}"
            local_name = alias if alias else imported_name
            
            if self._is_camel_case(imported_name):
                # Likely a class
                self.external_classes[fqn] = {
                    "module": module_name,
                    "name": imported_name,
                    "local_alias": local_name
                }
                self.logger.log(f"[EXTERNAL_CLASS] Added: {fqn} (alias: {local_name})", 2)
            else:
                # Likely a function
                self.external_functions[fqn] = {
                    "module": module_name, 
                    "name": imported_name,
                    "local_alias": local_name,
                    "return_type": None  # We don't know external function return types
                }
                self.logger.log(f"[EXTERNAL_FUNCTION] Added: {fqn} (alias: {local_name})", 2)
    
    def process_import(self, node: ast.Import):
        """Process import statements."""
        self.logger.log("[IMPORT] Processing direct imports", 3)
        
        for alias in node.names:
            # Handle direct module imports like: import threading
            if alias.name in EXTERNAL_LIBRARY_ALLOWLIST:
                # For direct module imports, we'll handle them during name resolution
                self.logger.log(f"[EXTERNAL_MODULE] Direct import: {alias.name}", 2)
    
    def process_import_from(self, node: ast.ImportFrom):
        """Process from imports and extract external library items."""
        if node.module and node.module in EXTERNAL_LIBRARY_ALLOWLIST:
            self.logger.log(f"[EXTERNAL_IMPORT] Processing from {node.module}", 2)
            
            for alias in node.names:
                if alias.name == '*':
                    self.logger.log(f"[EXTERNAL_IMPORT] Warning: star import from {node.module} - cannot track individual items", 1)
                    continue
                
                self._process_import(node.module, alias.name, alias.asname)
    
    def get_external_data(self) -> Dict[str, Dict[str, Any]]:
        """Get collected external library data."""
        return {
            "external_classes": self.external_classes.copy(),
            "external_functions": self.external_functions.copy()
        }
