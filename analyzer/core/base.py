"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with refined hierarchy.
BaseNode provides shared functionality with enhanced query-based navigation system.
RootNode for parentless nodes, TreeNode for entities requiring parents, 
ContainerNode for AST artifacts.
UPDATED: Enhanced with query-based navigation system resolving API consistency.
"""

import ast
from typing import Optional, List, Union, TYPE_CHECKING, Any, Dict, Callable
from enum import Enum

if TYPE_CHECKING:
    from ..nodes import (
        PackageNode, ModuleNode, ClassNode, FunctionNode, StateNode, 
        AliasNode, ArgumentNode, AttributeNode, StateContainerNode,
        ImportNode, ImportFromNode, ReturnNode
    )

class TraversalScope(Enum):
    """Enumeration of traversal scopes for navigation queries."""
    DIRECT = "direct"           # Only immediate children
    CASCADE = "cascade"         # Full recursive subtree traversal
    CONTEXT = "context"         # Context-sensitive (structural vs entity)

class NavigationQuery:
    """Internal query structure for navigation requests."""
    def __init__(self, 
                 entity_type: str, 
                 scope: TraversalScope, 
                 filter_func: Optional[Callable] = None,
                 max_depth: Optional[int] = None):
        self.entity_type = entity_type
        self.scope = scope
        self.filter_func = filter_func
        self.max_depth = max_depth

class BaseNode:
    """Foundation for all Atlas nodes with enhanced query-based navigation system."""
    
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
    # PRIVATE QUERY ENGINE - Core Navigation System
    # ===============================================
    
    def _execute_navigation_query(self, query: NavigationQuery) -> List[Any]:
        """
        Private workhorse function for all navigation requests.
        Handles scope determination, traversal, and filtering.
        """
        collection_attr = f"_{query.entity_type}"
        results = []
        
        if query.scope == TraversalScope.DIRECT:
            # Direct children only
            collection = getattr(self, collection_attr, [])
            results = list(collection) if collection else []
            
            # Handle special case for single return node
            if query.entity_type == 'returns':
                if hasattr(self, '_return') and self._return:
                    results = [self._return]
                    
        elif query.scope == TraversalScope.CASCADE:
            # Full recursive traversal
            results = self._cascade_collect(query.entity_type, query.max_depth or 999)
            
        elif query.scope == TraversalScope.CONTEXT:
            # Context-sensitive traversal
            if self._is_structural_navigation(query.entity_type):
                results = self._execute_navigation_query(
                    NavigationQuery(query.entity_type, TraversalScope.DIRECT)
                )
            else:
                results = self._execute_navigation_query(
                    NavigationQuery(query.entity_type, TraversalScope.CASCADE)
                )
        
        # Apply filters if specified
        if query.filter_func:
            results = [item for item in results if query.filter_func(item)]
        
        return results
    
    def _cascade_collect(self, entity_type: str, max_depth: int, current_depth: int = 0) -> List[Any]:
        """Recursively collect entities throughout subtree."""
        if current_depth >= max_depth:
            return []
        
        results = []
        collection_attr = f"_{entity_type}"
        
        # Collect direct children of this type
        direct_collection = getattr(self, collection_attr, [])
        if direct_collection:
            results.extend(direct_collection)
        
        # Handle special case for single return node
        if entity_type == 'returns':
            if hasattr(self, '_return') and self._return:
                results.append(self._return)
        
        # Recurse through all child collections
        child_collections = [
            '_packages', '_modules', '_classes', '_functions', '_methods', 
            '_arguments', '_attributes', '_state', '_state_containers',
            '_imports', '_aliases'
        ]
        
        for collection_name in child_collections:
            collection = getattr(self, collection_name, [])
            if collection:
                for child in collection:
                    child_results = child._cascade_collect(
                        entity_type, max_depth, current_depth + 1
                    )
                    results.extend(child_results)
        
        return results
    
    def _is_structural_navigation(self, entity_type: str) -> bool:
        """Determine if entity type represents structural vs entity navigation."""
        # Structural types represent hierarchy organization
        structural_types = {'packages', 'modules'}
        return entity_type in structural_types
    
    def _find_entity_by_name(self, results: List[Any], name: str) -> Any:
        """Find entity by name in results list."""
        for entity in results:
            if hasattr(entity, 'name') and entity.name == name:
                return entity
        return None
    
    # ===============================================
    # PUBLIC API - Direct Children Navigation
    # ===============================================
    
    def get_child_package(self, name: str) -> 'PackageNode':
        """Get direct child package by name."""
        query = NavigationQuery('packages', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Package '{name}' not found in direct children of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_child_module(self, name: str) -> 'ModuleNode':
        """Get direct child module by name."""
        query = NavigationQuery('modules', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Module '{name}' not found in direct children of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_child_class(self, name: str) -> 'ClassNode':
        """Get direct child class by name."""
        query = NavigationQuery('classes', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Class '{name}' not found in direct children of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_child_function(self, name: str) -> 'FunctionNode':
        """Get direct child function by name."""
        query = NavigationQuery('functions', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Function '{name}' not found in direct children of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_child_method(self, name: str) -> 'FunctionNode':
        """Get direct child method by name."""
        query = NavigationQuery('methods', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Method '{name}' not found in direct children of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def list_child_packages(self) -> List['PackageNode']:
        """List direct child packages only."""
        query = NavigationQuery('packages', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_modules(self) -> List['ModuleNode']:
        """List direct child modules only."""
        query = NavigationQuery('modules', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_classes(self) -> List['ClassNode']:
        """List direct child classes only."""
        query = NavigationQuery('classes', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_functions(self) -> List['FunctionNode']:
        """List direct child functions only."""
        query = NavigationQuery('functions', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_methods(self) -> List['FunctionNode']:
        """List direct child methods only."""
        query = NavigationQuery('methods', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_arguments(self) -> List['ArgumentNode']:
        """List direct child arguments only."""
        query = NavigationQuery('arguments', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_attributes(self) -> List['AttributeNode']:
        """List direct child attributes only."""
        query = NavigationQuery('attributes', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_state(self) -> List['StateNode']:
        """List direct child state variables only."""
        query = NavigationQuery('state', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_aliases(self) -> List['AliasNode']:
        """List direct child aliases only."""
        query = NavigationQuery('aliases', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_returns(self) -> List['ReturnNode']:
        """List direct child returns only."""
        query = NavigationQuery('returns', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # PUBLIC API - Recursive/All Navigation
    # ===============================================
    
    def get_all_package(self, name: str) -> 'PackageNode':
        """Get package by name from anywhere in subtree."""
        query = NavigationQuery('packages', TraversalScope.CASCADE)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Package '{name}' not found in subtree of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_all_module(self, name: str) -> 'ModuleNode':
        """Get module by name from anywhere in subtree."""
        query = NavigationQuery('modules', TraversalScope.CASCADE)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Module '{name}' not found in subtree of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_all_class(self, name: str) -> 'ClassNode':
        """Get class by name from anywhere in subtree."""
        query = NavigationQuery('classes', TraversalScope.CASCADE)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Class '{name}' not found in subtree of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_all_function(self, name: str) -> 'FunctionNode':
        """Get function by name from anywhere in subtree."""
        query = NavigationQuery('functions', TraversalScope.CASCADE)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Function '{name}' not found in subtree of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_all_method(self, name: str) -> 'FunctionNode':
        """Get method by name from anywhere in subtree."""
        query = NavigationQuery('methods', TraversalScope.CASCADE)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        raise KeyError(f"Method '{name}' not found in subtree of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def list_all_packages(self) -> List['PackageNode']:
        """List all packages recursively throughout subtree."""
        query = NavigationQuery('packages', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_modules(self) -> List['ModuleNode']:
        """List all modules recursively throughout subtree."""
        query = NavigationQuery('modules', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_classes(self) -> List['ClassNode']:
        """List all classes recursively throughout subtree."""
        query = NavigationQuery('classes', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_functions(self) -> List['FunctionNode']:
        """List all functions recursively throughout subtree."""
        query = NavigationQuery('functions', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_methods(self) -> List['FunctionNode']:
        """List all methods recursively throughout subtree."""
        query = NavigationQuery('methods', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_arguments(self) -> List['ArgumentNode']:
        """List all arguments recursively throughout subtree."""
        query = NavigationQuery('arguments', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_attributes(self) -> List['AttributeNode']:
        """List all attributes recursively throughout subtree."""
        query = NavigationQuery('attributes', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_state(self) -> List['StateNode']:
        """List all state variables recursively throughout subtree."""
        query = NavigationQuery('state', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_aliases(self) -> List['AliasNode']:
        """List all aliases recursively throughout subtree."""
        query = NavigationQuery('aliases', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_returns(self) -> List['ReturnNode']:
        """List all return nodes recursively throughout subtree."""
        query = NavigationQuery('returns', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # PUBLIC API - Context-Sensitive Navigation  
    # ===============================================
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get package using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('packages', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('packages') else "subtree"
        raise KeyError(f"Package '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get module using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('modules', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('modules') else "subtree"
        raise KeyError(f"Module '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_class(self, name: str) -> 'ClassNode':
        """Get class using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('classes', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('classes') else "subtree"
        raise KeyError(f"Class '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get function using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('functions', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('functions') else "subtree"
        raise KeyError(f"Function '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get method using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('methods', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('methods') else "subtree"
        raise KeyError(f"Method '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_state(self, name: str) -> 'StateNode':
        """Get state variable using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('state', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('state') else "subtree"
        raise KeyError(f"State variable '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_attribute(self, name: str) -> 'AttributeNode':
        """Get attribute using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('attributes', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('attributes') else "subtree"
        raise KeyError(f"Attribute '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_argument(self, name: str) -> 'ArgumentNode':
        """Get argument using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('arguments', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('arguments') else "subtree"
        raise KeyError(f"Argument '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_alias(self, name: str) -> 'AliasNode':
        """Get alias using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('aliases', TraversalScope.CONTEXT)
        results = self._execute_navigation_query(query)
        entity = self._find_entity_by_name(results, name)
        if entity:
            return entity
        scope_desc = "direct children" if self._is_structural_navigation('aliases') else "subtree"
        raise KeyError(f"Alias '{name}' not found in {scope_desc} of {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def get_return(self, name: str = "return") -> 'ReturnNode':
        """Get return node using direct scope (returns are per-function entities)."""
        query = NavigationQuery('returns', TraversalScope.DIRECT)
        results = self._execute_navigation_query(query)
        if results:
            return results[0]  # Return the first (and typically only) return
        raise KeyError(f"Return node not found in {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'")
    
    def list_packages(self) -> List['PackageNode']:
        """List packages using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('packages', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_modules(self) -> List['ModuleNode']:
        """List modules using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('modules', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_classes(self) -> List['ClassNode']:
        """List classes using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('classes', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_functions(self) -> List['FunctionNode']:
        """List functions using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('functions', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_methods(self) -> List['FunctionNode']:
        """List methods using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('methods', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_state(self) -> List['StateNode']:
        """List state variables using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('state', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_attributes(self) -> List['AttributeNode']:
        """List attributes using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('attributes', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List arguments using direct scope (arguments are per-function entities)."""
        query = NavigationQuery('arguments', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_aliases(self) -> List['AliasNode']:
        """List aliases using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('aliases', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_returns(self) -> List['ReturnNode']:
        """List return nodes using direct scope (returns are per-function entities)."""
        query = NavigationQuery('returns', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_state_containers(self) -> List['StateContainerNode']:
        """List state containers using direct scope."""
        query = NavigationQuery('state_containers', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """List import containers using direct scope."""
        query = NavigationQuery('imports', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # ADVANCED API - Future SQL-like Query Support
    # ===============================================
    
    def query(self, entity_type: str, 
              scope: TraversalScope = TraversalScope.CONTEXT,
              filter_func: Optional[Callable] = None,
              max_depth: Optional[int] = None) -> List[Any]:
        """
        Advanced query interface for future SQL-like capabilities.
        
        Examples:
          node.query('classes', TraversalScope.CASCADE, lambda c: c.name.startswith('Test'))
          node.query('functions', TraversalScope.DIRECT, max_depth=2)
        """
        query = NavigationQuery(entity_type, scope, filter_func, max_depth)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # UNIFIED NAVIGATION API - Comprehensive View
    # ===============================================
    
    def list_all(self) -> dict:
        """
        Get comprehensive structure using context-sensitive navigation.
        Dynamically discovers what collections exist and reports their contents.
        """
        result = {}
        
        # Check all possible collection attributes using context-sensitive defaults
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