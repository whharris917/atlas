"""
Module Node - Atlas Rewrite

Node representing a Python module with self-discovery capabilities.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..base import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .class_node import ClassNode
    from .function import FunctionNode
    from .state import StateNode
    from .import_node import ImportNode


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None):
        super().__init__(name, ast_node)
        self.path = path
        self._classes: Dict[str, ClassNode] = {}
        self._functions: Dict[str, FunctionNode] = {}
        self._state: Dict[str, StateNode] = {}
        self._imports: Dict[str, ImportNode] = {}
        self._children_discovered = False
    
    def discover_children(self):
        """Discover and create child nodes from AST without full population."""
        if self._children_discovered or not self.ast_node:
            return
        
        print(f"  Discovering children in: {self.fqn}")
        
        # Walk AST and create child nodes with their AST nodes
        for node in ast.walk(self.ast_node):
            if isinstance(node, ast.ClassDef):
                self._discover_class(node)
        
        # Extract module-level functions (not inside classes)
        for node in self.ast_node.body:
            if isinstance(node, ast.FunctionDef):
                self._discover_function(node)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                self._discover_state(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._discover_import(node)
        
        self._children_discovered = True
    
    def _discover_class(self, class_ast: ast.ClassDef):
        """Create ClassNode with AST, let it handle its own method discovery."""
        if class_ast.name not in self._classes:
            from .class_node import ClassNode
            class_node = ClassNode(class_ast.name, getattr(class_ast, 'lineno', 0), class_ast)
            class_node.parent = self
            self._classes[class_ast.name] = class_node
            print(f"    Found class: {class_node.fqn}")
    
    def _discover_function(self, func_ast: ast.FunctionDef):
        """Create FunctionNode with AST for later argument discovery."""
        from .function import FunctionNode
        function_node = FunctionNode(func_ast.name, getattr(func_ast, 'lineno', 0), func_ast)
        function_node.parent = self
        self._functions[func_ast.name] = function_node
        print(f"    Found function: {function_node.fqn}")
    
    def _discover_state(self, state_ast: ast.AST):
        """Create StateNode with AST."""
        if isinstance(state_ast, ast.Assign):
            for target in state_ast.targets:
                if isinstance(target, ast.Name):
                    self._create_state_node(target.id, state_ast)
        elif isinstance(state_ast, ast.AnnAssign) and isinstance(state_ast.target, ast.Name):
            self._create_state_node(state_ast.target.id, state_ast)
    
    def _create_state_node(self, name: str, ast_node: ast.AST):
        """Helper to create StateNode."""
        from .state import StateNode
        state_node = StateNode(name, getattr(ast_node, 'lineno', 0), ast_node)
        state_node.parent = self
        self._state[name] = state_node
        print(f"    Found state: {state_node.fqn}")
    
    def _discover_import(self, import_ast: ast.AST):
        """Create ImportNode with AST."""
        from .import_node import ImportNode
        
        if isinstance(import_ast, ast.Import):
            for alias in import_ast.names:
                import_name = alias.asname if alias.asname else alias.name
                import_node = ImportNode(import_name, alias.name, import_ast)
                import_node.parent = self
                self._imports[import_name] = import_node
                print(f"    Found import: {import_node.fqn} -> {alias.name}")
        
        elif isinstance(import_ast, ast.ImportFrom) and import_ast.module:
            for alias in import_ast.names:
                import_name = alias.asname if alias.asname else alias.name
                full_module = f"{import_ast.module}.{alias.name}"
                import_node = ImportNode(import_name, full_module, import_ast)
                import_node.parent = self
                self._imports[import_name] = import_node
                print(f"    Found from-import: {import_node.fqn} -> {full_module}")
    
    def create_class(self, name: str, line_number: int = 0, ast_node: Optional[ast.ClassDef] = None) -> ClassNode:
        """Create and hook a new class."""
        from .class_node import ClassNode
        class_node = ClassNode(name, line_number, ast_node)
        class_node.parent = self
        self._classes[name] = class_node
        return class_node
    
    def create_function(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None) -> FunctionNode:
        """Create and hook a new function."""
        from .function import FunctionNode
        function_node = FunctionNode(name, line_number, ast_node)
        function_node.parent = self
        self._functions[name] = function_node
        return function_node
    
    def create_state(self, name: str, line_number: int = 0, ast_node: Optional[ast.AST] = None) -> StateNode:
        """Create and hook a new state variable."""
        from .state import StateNode
        state_node = StateNode(name, line_number, ast_node)
        state_node.parent = self
        self._state[name] = state_node
        return state_node
    
    def create_import(self, name: str, module_name: str = "", ast_node: Optional[ast.AST] = None) -> ImportNode:
        """Create and hook a new import."""
        from .import_node import ImportNode
        import_node = ImportNode(name, module_name, ast_node)
        import_node.parent = self
        self._imports[name] = import_node
        return import_node
    
    def get_class(self, name: str) -> ClassNode:
        """Get a class by name."""
        self.discover_children()  # Ensure children are discovered
        if name not in self._classes:
            raise KeyError(f"Class '{name}' not found in module '{self.name}'")
        return self._classes[name]
    
    def get_function(self, name: str) -> FunctionNode:
        """Get a function by name."""
        self.discover_children()  # Ensure children are discovered
        if name not in self._functions:
            raise KeyError(f"Function '{name}' not found in module '{self.name}'")
        return self._functions[name]
    
    def list_classes(self) -> List[ClassNode]:
        """List all classes in this module."""
        self.discover_children()  # Ensure children are discovered
        return list(self._classes.values())
    
    def list_functions(self) -> List[FunctionNode]:
        """List all functions in this module."""
        self.discover_children()  # Ensure children are discovered
        return list(self._functions.values())
    
    def list_state(self) -> List[StateNode]:
        """List all state variables in this module."""
        self.discover_children()  # Ensure children are discovered
        return list(self._state.values())
    
    def list_imports(self) -> List[ImportNode]:
        """List all imports in this module."""
        self.discover_children()  # Ensure children are discovered
        return list(self._imports.values())
    
    def list_all(self) -> Dict[str, List]:
        """List everything contained in this module."""
        self.discover_children()  # Ensure children are discovered
        return {
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'state': self.list_state(),
            'imports': self.list_imports()
        }