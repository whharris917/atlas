"""
Tree Node Classes - Atlas Rewrite

All concrete node types for the project tree structure.
"""

import ast
from typing import Dict, List, Optional
from .base import TreeNode


class ProjectNode(TreeNode):
    """Root node representing the entire project."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}  # Direct modules (no package)
    
    def create_package(self, name: str, init_ast: Optional[ast.Module] = None) -> 'PackageNode':
        """Create and hook a new package."""
        package = PackageNode(name, init_ast=init_ast)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None) -> 'ModuleNode':
        """Create and hook a new module directly under project."""
        module = ModuleNode(name, path, ast_node)
        module.parent = self
        self._modules[name] = module
        return module
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a package by name."""
        if name not in self._packages:
            raise KeyError(f"Package '{name}' not found")
        return self._packages[name]
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a direct module by name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found")
        return self._modules[name]
    
    def list_packages(self) -> List['PackageNode']:
        """List all packages in the project."""
        return list(self._packages.values())
    
    def list_modules(self) -> List['ModuleNode']:
        """List all direct modules in the project."""
        return list(self._modules.values())


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None):
        super().__init__(name, init_ast)  # Store init AST as the package's AST node
        self.path = path
        self.init_ast = init_ast  # Also keep separate reference for clarity
        self._packages: Dict[str, 'PackageNode'] = {}  # Nested packages
        self._modules: Dict[str, 'ModuleNode'] = {}
    
    def create_package(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None) -> 'PackageNode':
        """Create and hook a new nested package."""
        package = PackageNode(name, path, init_ast)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None) -> 'ModuleNode':
        """Create and hook a new module in this package."""
        module = ModuleNode(name, path, ast_node)
        module.parent = self
        self._modules[name] = module
        return module
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a nested package by name."""
        if name not in self._packages:
            raise KeyError(f"Package '{name}' not found in package '{self.name}'")
        return self._packages[name]
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found in package '{self.name}'")
        return self._modules[name]
    
    def list_packages(self) -> List['PackageNode']:
        """List all nested packages in this package."""
        return list(self._packages.values())
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules in this package."""
        return list(self._modules.values())


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None):
        super().__init__(name, ast_node)
        self.path = path
        self._classes: Dict[str, 'ClassNode'] = {}
        self._functions: Dict[str, 'FunctionNode'] = {}
        self._state: Dict[str, 'StateNode'] = {}
        self._imports: Dict[str, 'ImportNode'] = {}
    
    def create_class(self, name: str, line_number: int = 0, ast_node: Optional[ast.ClassDef] = None) -> 'ClassNode':
        """Create and hook a new class."""
        class_node = ClassNode(name, line_number, ast_node)
        class_node.parent = self
        self._classes[name] = class_node
        return class_node
    
    def create_function(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None) -> 'FunctionNode':
        """Create and hook a new function."""
        function_node = FunctionNode(name, line_number, ast_node)
        function_node.parent = self
        self._functions[name] = function_node
        return function_node
    
    def create_state(self, name: str, line_number: int = 0, ast_node: Optional[ast.AST] = None) -> 'StateNode':
        """Create and hook a new state variable."""
        state_node = StateNode(name, line_number, ast_node)
        state_node.parent = self
        self._state[name] = state_node
        return state_node
    
    def create_import(self, name: str, module_name: str = "", ast_node: Optional[ast.AST] = None) -> 'ImportNode':
        """Create and hook a new import."""
        import_node = ImportNode(name, module_name, ast_node)
        import_node.parent = self
        self._imports[name] = import_node
        return import_node
    
    def get_class(self, name: str) -> 'ClassNode':
        """Get a class by name."""
        if name not in self._classes:
            raise KeyError(f"Class '{name}' not found in module '{self.name}'")
        return self._classes[name]
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get a function by name."""
        if name not in self._functions:
            raise KeyError(f"Function '{name}' not found in module '{self.name}'")
        return self._functions[name]
    
    def list_classes(self) -> List['ClassNode']:
        """List all classes in this module."""
        return list(self._classes.values())
    
    def list_functions(self) -> List['FunctionNode']:
        """List all functions in this module."""
        return list(self._functions.values())
    
    def list_state(self) -> List['StateNode']:
        """List all state variables in this module."""
        return list(self._state.values())
    
    def list_imports(self) -> List['ImportNode']:
        """List all imports in this module."""
        return list(self._imports.values())
    
    def list_all(self) -> Dict[str, List]:
        """List everything contained in this module."""
        return {
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'state': self.list_state(),
            'imports': self.list_imports()
        }


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.ClassDef] = None):
        super().__init__(name, ast_node)
        self.line_number = line_number
        self._methods: Dict[str, 'FunctionNode'] = {}
        self._attributes: Dict[str, 'AttributeNode'] = {}
    
    def create_method(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None) -> 'FunctionNode':
        """Create and hook a new method."""
        method_node = FunctionNode(name, line_number, ast_node, is_method=True)
        method_node.parent = self
        self._methods[name] = method_node
        return method_node
    
    def create_attribute(self, name: str, attribute_type: str = "", ast_node: Optional[ast.AST] = None) -> 'AttributeNode':
        """Create and hook a new attribute."""
        attr_node = AttributeNode(name, attribute_type, ast_node)
        attr_node.parent = self
        self._attributes[name] = attr_node
        return attr_node
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get a method by name."""
        if name not in self._methods:
            raise KeyError(f"Method '{name}' not found in class '{self.name}'")
        return self._methods[name]
    
    def list_methods(self) -> List['FunctionNode']:
        """List all methods in this class."""
        return list(self._methods.values())
    
    def list_attributes(self) -> List['AttributeNode']:
        """List all attributes in this class."""
        return list(self._attributes.values())


class FunctionNode(TreeNode):
    """Node representing a Python function or method."""
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None, is_method: bool = False):
        super().__init__(name, ast_node)
        self.line_number = line_number
        self.is_method = is_method
        self._arguments: Dict[str, 'ArgumentNode'] = {}
    
    def create_argument(self, name: str, arg_type: str = "", ast_node: Optional[ast.arg] = None) -> 'ArgumentNode':
        """Create and hook a new argument."""
        arg_node = ArgumentNode(name, arg_type, ast_node)
        arg_node.parent = self
        self._arguments[name] = arg_node
        return arg_node
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List all arguments for this function."""
        return list(self._arguments.values())


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.AST] = None):
        super().__init__(name, ast_node)
        self.line_number = line_number


class ImportNode(TreeNode):
    """Node representing an import statement."""
    
    def __init__(self, name: str, module_name: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(name, ast_node)
        self.module_name = module_name


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, name: str, arg_type: str = "", ast_node: Optional[ast.arg] = None):
        super().__init__(name, ast_node)
        self.arg_type = arg_type


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, name: str, attribute_type: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(name, ast_node)
        self.attribute_type = attribute_type