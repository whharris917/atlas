"""
Graph Node Classes - Atlas Rewrite

Specialized node classes for different code entities.
"""

import ast
from typing import Dict, Any, Set, List, Optional
from .base import Node


class ProjectNode(Node):
    """Root node representing the entire project."""
    
    def __init__(self, id: str, name: str, ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.metadata["packages"] = set()
        self.metadata["modules"] = set()


class PackageNode(Node):
    """Node representing a Python package."""
    
    def __init__(self, id: str, name: str, path: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.path = path
        self.metadata["modules"] = set()
        self.metadata["path"] = self.path


class ModuleNode(Node):
    """Node representing a Python module."""
    
    def __init__(self, id: str, name: str, path: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.path = path
        self.metadata["classes"] = set()
        self.metadata["functions"] = set()
        self.metadata["imports"] = set()
        self.metadata["state"] = set()
        self.metadata["path"] = self.path


class ClassNode(Node):
    """Node representing a Python class."""
    
    def __init__(self, id: str, name: str, line_number: int = 0, 
                 parents: List[str] = None, ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.line_number = line_number
        self.parents = parents or []
        self.metadata["methods"] = set()
        self.metadata["attributes"] = set()
        self.metadata["line"] = self.line_number
        self.metadata["parents"] = self.parents


class FunctionNode(Node):
    """Node representing a Python function or method."""
    
    def __init__(self, id: str, name: str, line_number: int = 0,
                 arguments: List[str] = None, is_method: bool = False, ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.line_number = line_number
        self.arguments = arguments or []
        self.is_method = is_method
        self.metadata["calls"] = set()
        self.metadata["accessed_state"] = set()
        self.metadata["line"] = self.line_number
        self.metadata["arguments"] = self.arguments
        self.metadata["is_method"] = self.is_method


class ImportNode(Node):
    """Node representing an import statement."""
    
    def __init__(self, id: str, name: str, module_name: str = "", 
                 alias: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.module_name = module_name
        self.alias = alias
        self.metadata["module_name"] = self.module_name
        self.metadata["alias"] = self.alias


class StateNode(Node):
    """Node representing module-level state variable."""
    
    def __init__(self, id: str, name: str, line_number: int = 0, ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.line_number = line_number
        self.metadata["line"] = self.line_number


class ArgumentNode(Node):
    """Node representing a function argument."""
    
    def __init__(self, id: str, name: str, argument_type: str = "", 
                 default_value: Any = None, ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.argument_type = argument_type
        self.default_value = default_value
        self.metadata["type"] = self.argument_type
        self.metadata["default"] = self.default_value


class AttributeNode(Node):
    """Node representing a class attribute."""
    
    def __init__(self, id: str, name: str, attribute_type: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(id, name, ast_node)
        self.attribute_type = attribute_type
        self.metadata["type"] = self.attribute_type
