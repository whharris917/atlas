"""
Alias Node - Atlas Rewrite

Node representing a single import alias.
This is where the actual import information lives.
"""

import ast
from ..core import TreeNode


class AliasNode(TreeNode):
    """Node representing a single import alias."""
    
    def __init__(self, alias: ast.alias, import_type: str, from_module: str = ""):
        if not alias:
            raise ValueError("AliasNode requires valid ast.alias")
        if import_type not in ["import", "from_import"]:
            raise ValueError("import_type must be 'import' or 'from_import'")
        
        # Extract local name (what it's called in the importing module)
        local_name = alias.asname if alias.asname else alias.name
        super().__init__(local_name, alias)
        
        # Store import details
        self.import_type = import_type
        self.imported_name = alias.name  # What's actually being imported
        self.from_module = from_module   # For from_import: the module being imported from
        
        # Calculate full module path
        if import_type == "import":
            self.module_name = alias.name
        else:  # from_import
            if from_module:
                self.module_name = f"{from_module}.{alias.name}"
            else:
                self.module_name = alias.name