"""
Base Visitor - Code Atlas

Base AST visitor providing common functionality for all specialized visitors.
"""

import ast
from typing import Dict, List, Any, Optional
from ..utils.logger import AnalysisLogger
from ..utils.naming import generate_fqn, generate_class_fqn, generate_function_fqn


class BaseVisitor(ast.NodeVisitor):
    """Base visitor with common functionality for Atlas analysis."""
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str, logger: AnalysisLogger):
        self.recon_data = recon_data
        self.module_name = module_name
        self.logger = logger
        
        # Context tracking
        self.current_class = None
        self.current_function_fqn = None
        self.import_map = {}
        
        # State tracking
        self.in_function = False
        self.in_class = False
        self.function_depth = 0
    
    def enter_class_context(self, class_name: str) -> str:
        """Enter class analysis context."""
        old_class = self.current_class
        self.current_class = generate_class_fqn(self.module_name, class_name)
        self.in_class = True
        self.logger.log(f"[CONTEXT] Entered class: {self.current_class}", 2)
        return old_class
    
    def exit_class_context(self, old_class: Optional[str]) -> None:
        """Exit class analysis context."""
        self.logger.log(f"[CONTEXT] Exited class: {self.current_class}", 2)
        self.current_class = old_class
        self.in_class = old_class is not None
    
    def enter_function_context(self, function_name: str) -> tuple:
        """Enter function analysis context."""
        old_function_fqn = self.current_function_fqn
        old_in_function = self.in_function
        old_depth = self.function_depth
        
        self.current_function_fqn = generate_function_fqn(
            self.module_name, 
            self.current_class.split('.')[-1] if self.current_class else None,
            function_name
        )
        self.in_function = True
        self.function_depth += 1
        
        self.logger.log(f"[CONTEXT] Entered function: {self.current_function_fqn} (depth: {self.function_depth})", 2)
        return old_function_fqn, old_in_function, old_depth
    
    def exit_function_context(self, old_context: tuple) -> None:
        """Exit function analysis context."""
        old_function_fqn, old_in_function, old_depth = old_context
        
        self.logger.log(f"[CONTEXT] Exited function: {self.current_function_fqn}", 2)
        self.current_function_fqn = old_function_fqn
        self.in_function = old_in_function
        self.function_depth = old_depth
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current analysis context."""
        return {
            'current_module': self.module_name,
            'current_class': self.current_class,
            'current_function_fqn': self.current_function_fqn,
            'import_map': self.import_map,
            'in_function': self.in_function,
            'in_class': self.in_class,
            'function_depth': self.function_depth
        }
    
    def process_imports(self, node: ast.Import) -> None:
        """Process import statements and update import map."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            self.logger.log(f"[IMPORT] {key} -> {alias.name}", 2)
    
    def process_from_imports(self, node: ast.ImportFrom) -> None:
        """Process from-import statements and update import map."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                self.logger.log(f"[FROM_IMPORT] {key} -> {node.module}.{alias.name}", 2)
    
    def extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Extract docstring from a node."""
        if (hasattr(node, 'body') and node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            return node.body[0].value.value
        return None
    
    def extract_decorators(self, node: ast.FunctionDef) -> List[str]:
        """Extract decorator strings from function definition."""
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorator_str = f"@{ast.unparse(decorator)}"
                decorators.append(decorator_str)
                self.logger.log(f"[DECORATOR] {decorator_str}", 2)
            except Exception as e:
                self.logger.log(f"[DECORATOR] Failed to extract decorator: {e}", 2)
        return decorators
    
    def is_nested_function(self) -> bool:
        """Check if we're currently in a nested function."""
        return self.function_depth > 1
    
    def is_method(self) -> bool:
        """Check if current function is a method (inside a class)."""
        return self.in_function and self.in_class
    
    def get_function_args(self, node: ast.FunctionDef) -> List[str]:
        """Extract function argument names."""
        return [arg.arg for arg in node.args.args]
    
    def should_process_node(self, node: ast.AST) -> bool:
        """Determine if a node should be processed based on current context."""
        # Skip processing if we're too deep in nested functions
        max_depth = 10  # This could come from config
        if self.function_depth > max_depth:
            self.logger.log(f"[SKIP] Skipping node due to excessive nesting depth: {self.function_depth}", 3)
            return False
        
        return True
    
    def log_node_processing(self, node: ast.AST, action: str) -> None:
        """Log node processing for debugging."""
        node_type = type(node).__name__
        self.logger.log(f"[NODE] {action} {node_type} at depth {self.function_depth}", 4)
    
    def safe_unparse(self, node: ast.AST, fallback: str = "unparseable") -> str:
        """Safely unparse AST node with fallback."""
        try:
            return ast.unparse(node)
        except Exception:
            return fallback
    
    def extract_constant_value(self, node: ast.AST) -> Any:
        """Extract constant value from AST node if possible."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return f"${node.id}"  # Variable reference
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        else:
            return self.safe_unparse(node, "complex_expression")
