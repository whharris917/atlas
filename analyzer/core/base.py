"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with refined hierarchy.
BaseNode provides shared functionality, RootNode for parentless nodes,
TreeNode for entities requiring parents, ContainerNode for AST artifacts.
UPDATED: Enhanced with ReturnNode universal API support.
"""

import ast
from typing import Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..nodes import (
        PackageNode, ModuleNode, ClassNode, FunctionNode, StateNode, 
        AliasNode, ArgumentNode, AttributeNode, StateContainerNode,
        ImportNode, ImportFromNode, ReturnNode
    )


class BaseNode:
    """Foundation for all Atlas nodes with shared functionality."""
    
    def __init__(self, ast_node: Optional[ast.AST] = None):
        self.ast_node = ast_node
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
        return 0
    
    def __repr__(self) -> str:
        """Nice string representation showing node type."""
        node_type = self.__class__.__name__.replace('Node', '')
        if hasattr(self, 'name'):
            return f"{node_type}({self.name})"
        return f"{node_type}()"
    
    # ===============================================
    # UNIFIED NAVIGATION API - Project/Package Level
    # ===============================================
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a package by name - works on any node that contains packages."""
        packages = getattr(self, '_packages', [])
        for package in packages:
            if package.name == name:
                return package
        raise KeyError(f"Package '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name - works on any node that contains modules."""
        modules = getattr(self, '_modules', [])
        for module in modules:
            if module.name == name:
                return module
        raise KeyError(f"Module '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def list_packages(self) -> List['PackageNode']:
        """List all packages - returns empty list if node doesn't contain packages."""
        return getattr(self, '_packages', [])
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules - returns empty list if node doesn't contain modules."""
        return getattr(self, '_modules', [])
    
    # ===============================================
    # UNIFIED NAVIGATION API - Code Entity Level
    # ===============================================
    
    def get_class(self, name: str) -> 'ClassNode':
        """Get a class by name - works on any node that contains classes."""
        classes = getattr(self, '_classes', [])
        for cls in classes:
            if cls.name == name:
                return cls
        raise KeyError(f"Class '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get a function by name - works on any node that contains functions."""
        functions = getattr(self, '_functions', [])
        for func in functions:
            if func.name == name:
                return func
        raise KeyError(f"Function '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get a method by name - works on any node that contains methods."""
        methods = getattr(self, '_methods', [])
        for method in methods:
            if method.name == name:
                return method
        raise KeyError(f"Method '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_state(self, name: str) -> 'StateNode':
        """Get a state variable by name - works on any node that contains state."""
        state_vars = self.list_state()
        for state in state_vars:
            if state.name == name:
                return state
        raise KeyError(f"State variable '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_attribute(self, name: str) -> 'AttributeNode':
        """Get an attribute by name - works on any node that contains attributes."""
        attributes = getattr(self, '_attributes', [])
        for attr in attributes:
            if attr.name == name:
                return attr
        raise KeyError(f"Attribute '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_argument(self, name: str) -> 'ArgumentNode':
        """Get an argument by name - works on any node that contains arguments."""
        arguments = getattr(self, '_arguments', [])
        for arg in arguments:
            if arg.name == name:
                return arg
        raise KeyError(f"Argument '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_alias(self, name: str) -> 'AliasNode':
        """Get an alias by name - works on any node that contains aliases."""
        aliases = getattr(self, '_aliases', [])
        for alias in aliases:
            if alias.name == name:
                return alias
        raise KeyError(f"Alias '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_return(self, name: str = "return") -> 'ReturnNode':
        """Get return node by name (always 'return' for consistency)."""
        returns = self.list_returns()
        for ret in returns:
            if ret.name == name:
                return ret
        raise KeyError(f"Return '{name}' not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    # ===============================================
    # UNIFIED NAVIGATION API - List Methods
    # ===============================================
    
    def list_classes(self) -> List['ClassNode']:
        """List all classes - returns empty list if node doesn't contain classes."""
        return getattr(self, '_classes', [])
    
    def list_functions(self) -> List['FunctionNode']:
        """List all functions - returns empty list if node doesn't contain functions."""
        return getattr(self, '_functions', [])
    
    def list_methods(self) -> List['FunctionNode']:
        """List all methods - returns empty list if node doesn't contain methods."""
        return getattr(self, '_methods', [])
    
    def list_state(self) -> List['StateNode']:
        """List all state variables from state containers - returns empty list if none."""
        state_vars = []
        state_containers = getattr(self, '_state_containers', [])
        for container in state_containers:
            # Access state variables directly from container's attribute
            if hasattr(container, '_state_variables'):
                state_vars.extend(container._state_variables)
        return state_vars
    
    def list_attributes(self) -> List['AttributeNode']:
        """List all attributes - returns empty list if node doesn't contain attributes."""
        return getattr(self, '_attributes', [])
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List all arguments - returns empty list if node doesn't contain arguments."""
        return getattr(self, '_arguments', [])
    
    def list_aliases(self) -> List['AliasNode']:
        """List all aliases - returns empty list if node doesn't contain aliases."""
        return getattr(self, '_aliases', [])
    
    def list_returns(self) -> List['ReturnNode']:
        """List all return nodes in this subtree."""
        returns = []
        
        # Check if this node has returns (direct _return attribute)
        if hasattr(self, '_return') and self._return:
            returns.append(self._return)
        
        # Recursively collect from child collections using existing BaseNode pattern
        # Check all known child collections following existing BaseNode universal API pattern
        child_collections = [
            '_packages', '_modules', '_classes', '_functions', '_methods', 
            '_arguments', '_attributes', '_state', '_state_containers',
            '_imports', '_aliases'
        ]
        
        for collection_name in child_collections:
            if hasattr(self, collection_name):
                collection = getattr(self, collection_name)
                if collection:
                    for child in collection:
                        # Check if child has returns
                        if hasattr(child, '_return') and child._return:
                            returns.append(child._return)
                        # Recurse into child
                        returns.extend(child.list_returns())
        
        return returns
    
    # ===============================================
    # UNIFIED NAVIGATION API - Container Methods
    # ===============================================
    
    def list_state_containers(self) -> List['StateContainerNode']:
        """List all state containers - returns empty list if node doesn't contain containers."""
        return getattr(self, '_state_containers', [])
    
    def list_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """List all import containers - returns empty list if node doesn't contain imports."""
        return getattr(self, '_imports', [])
    
    # ===============================================
    # UNIFIED NAVIGATION API - Comprehensive View
    # ===============================================
    
    def list_all(self) -> dict:
        """
        Get comprehensive structure of this node.
        Dynamically discovers what collections exist and reports their contents.
        """
        result = {}
        
        # Check all possible collection attributes
        collections = {
            'packages': self.list_packages(),
            'modules': self.list_modules(), 
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'methods': self.list_methods(),
            'state': self.list_state(),
            'attributes': self.list_attributes(),
            'arguments': self.list_arguments(),
            'returns': self.list_returns(),
            'aliases': self.list_aliases(),
            'state_containers': self.list_state_containers(),
            'imports': self.list_imports()
        }
        
        # Include only non-empty collections
        for collection_name, items in collections.items():
            if items:
                if collection_name in ['imports', 'state_containers']:
                    # Special handling for containers
                    result[collection_name] = len(items)
                else:
                    # Named entities - show names
                    result[collection_name] = [item.name if hasattr(item, 'name') else str(item) for item in items]
        
        return result


class RootNode(BaseNode):
    """Base for nodes that can exist without parents (project roots)."""
    
    def __init__(self, name: str, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        
        super().__init__(ast_node)
        self.name = name
        self.parent = None
        
        # Automatic child creation
        self._create_children()
    
    def _create_children(self):
        """Subclasses implement child creation logic. Base does nothing."""
        pass  # Default implementation does nothing
    
    @property
    def fqn(self) -> str:
        """Root nodes have FQN equal to their name."""
        return self.name


class TreeNode(BaseNode):
    """Base class for named entities with mandatory parent relationships."""
    
    def __init__(self, name: str, parent: BaseNode, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        if not parent:
            raise ValueError(f"{self.__class__.__name__} requires parent")
        
        super().__init__(ast_node)
        self.name = name
        self.parent = parent
        
        # Automatic child creation
        self._create_children()
    
    def _create_children(self):
        """Subclasses implement child creation logic. Base does nothing."""
        pass  # Default implementation does nothing (for leaf nodes)
    
    @property
    def fqn(self) -> str:
        """Generate FQN by walking up the tree, skipping ContainerNodes."""
        parts = [self.name]
        current = self.parent
        
        # Walk up the hierarchy, skipping ContainerNodes (they don't contribute to FQN)
        while current and not isinstance(current, RootNode):
            # Only include nodes with names in FQN, skip ContainerNodes
            if hasattr(current, 'name') and current.name:
                parts.append(current.name)
            current = getattr(current, 'parent', None)
        
        # Add root name if it exists
        if current and hasattr(current, 'name'):
            parts.append(current.name)
        
        return ".".join(reversed(parts))
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and FQN."""
        node_type = self.__class__.__name__.replace('Node', '')
        return f"{node_type}({self.fqn})"


class ContainerNode(BaseNode):
    """Base for nodes that exist solely to contain and create children."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.AST):
        if not parent:
            raise ValueError(f"{self.__class__.__name__} requires parent")
        if not ast_node:
            raise ValueError(f"{self.__class__.__name__} requires valid AST node")
        
        super().__init__(ast_node)
        self.parent = parent
        self._create_children()  # Always create children immediately
    
    def _create_children(self):
        """Subclasses implement child creation logic."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement _create_children()")