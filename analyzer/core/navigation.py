"""
Navigation System - Atlas Enhanced Query-Based Navigation

Core navigation infrastructure with three-tier scope control:
- Direct: Only immediate children
- Cascade: Full recursive subtree traversal  
- Context: Context-sensitive (structural vs entity)

Extracted from base.py for focused module organization.
FIXED: Properly lifted and shifted from original working implementation.
"""

import ast
from typing import Optional, List, Union, TYPE_CHECKING, Any, Callable
from enum import Enum

if TYPE_CHECKING:
    from ..nodes import (
        PackageNode, ModuleNode, ClassNode, FunctionNode, StateNode, 
        AliasNode, ArgumentNode, ClassAttributeNode, InstanceAttributeNode, 
        StateContainerNode, ImportNode, ImportFromNode, ReturnNode
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

class NavigationMixin:
    """
    Mixin providing enhanced query-based navigation system.
    
    Implements the three-tier navigation API:
    - Explicit direct children (list_child_*)
    - Explicit recursive (list_all_*)  
    - Context-sensitive defaults (list_*)
    
    LIFTED FROM: Original base.py working implementation
    """
    
    # ===============================================
    # PRIVATE QUERY ENGINE - Core Navigation System
    # ===============================================
    
    def _execute_navigation_query(self, query: NavigationQuery) -> List[Any]:
        """
        Private workhorse function for all navigation requests.
        Handles scope determination, traversal, and filtering.
        """
        # Determine actual scope to use
        actual_scope = query.scope
        if actual_scope == TraversalScope.CONTEXT:
            # Use context-sensitive logic
            if self._is_structural_navigation(query.entity_type):
                actual_scope = TraversalScope.DIRECT
            else:
                actual_scope = TraversalScope.CASCADE
        
        # Get base collection attribute name
        collection_attr = f"_{query.entity_type}"
        
        if actual_scope == TraversalScope.DIRECT:
            # Direct access to immediate children only
            if hasattr(self, collection_attr):
                items = getattr(self, collection_attr, {})
                if isinstance(items, dict):
                    result = list(items.values())
                elif isinstance(items, list):
                    result = items
                else:
                    result = []
            else:
                result = []
        
        elif actual_scope == TraversalScope.CASCADE:
            # Recursive collection from entire subtree
            result = self._cascade_collect(query.entity_type, query.max_depth)
        
        else:
            result = []
        
        # Apply filtering if provided
        if query.filter_func:
            result = [item for item in result if query.filter_func(item)]
        
        return result
    
    def _cascade_collect(self, entity_type: str, max_depth: Optional[int] = None, visited: Optional[set] = None) -> List[Any]:
        """
        Recursively collect entities of specified type from entire subtree.
        Uses visited set to prevent infinite recursion from circular references.
        """
        # Initialize visited set on first call
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion by tracking visited nodes
        node_id = id(self)
        if node_id in visited:
            return []
        visited.add(node_id)
        
        result = []
        
        # Add entities from this node
        collection_attr = f"_{entity_type}"
        if hasattr(self, collection_attr):
            items = getattr(self, collection_attr, {})
            if isinstance(items, dict):
                result.extend(items.values())
            elif isinstance(items, list):
                result.extend(items)
        
        # Recursively collect from children if depth allows
        if max_depth is None or max_depth > 0:
            next_depth = None if max_depth is None else max_depth - 1
            
            # Get all possible child collections, excluding parent references and circular attributes
            for attr_name in dir(self):
                if (attr_name.startswith('_') and 
                    hasattr(self, attr_name) and 
                    attr_name not in {'_create_children', '__class__', '__dict__', '__weakref__'} and
                    attr_name != 'parent'):  # Explicitly avoid parent to prevent cycles
                    
                    collection = getattr(self, attr_name)
                    if isinstance(collection, dict):
                        children = collection.values()
                    elif isinstance(collection, list):
                        children = collection
                    else:
                        continue
                    
                    for child in children:
                        if hasattr(child, '_cascade_collect'):
                            result.extend(child._cascade_collect(entity_type, next_depth, visited))
        
        return result
    
    def _is_structural_navigation(self, entity_type: str) -> bool:
        """
        Determine if entity type represents structural vs entity navigation.
        Structural: packages, modules (hierarchical organization)
        Entity: classes, functions, etc. (comprehensive discovery)
        """
        structural_types = {'packages', 'modules'}
        return entity_type in structural_types
    
    # ===============================================
    # DIRECT CHILDREN API - Explicit Direct Access
    # ===============================================
    
    def list_child_packages(self) -> List['PackageNode']:
        """Get only immediate child packages (explicit direct scope)."""
        query = NavigationQuery('packages', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_modules(self) -> List['ModuleNode']:
        """Get only immediate child modules (explicit direct scope)."""
        query = NavigationQuery('modules', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_classes(self) -> List['ClassNode']:
        """Get only immediate child classes (explicit direct scope)."""
        query = NavigationQuery('classes', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_functions(self) -> List['FunctionNode']:
        """Get only immediate child functions (explicit direct scope)."""
        query = NavigationQuery('functions', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_methods(self) -> List['FunctionNode']:
        """Get only immediate child methods (explicit direct scope)."""
        query = NavigationQuery('methods', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_state(self) -> List['StateNode']:
        """Get only immediate child state (explicit direct scope)."""
        query = NavigationQuery('state', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_class_attributes(self) -> List['ClassAttributeNode']:
        """Get only immediate child class attributes (explicit direct scope)."""
        query = NavigationQuery('class_attributes', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_instance_attributes(self) -> List['InstanceAttributeNode']:
        """Get only immediate child instance attributes (explicit direct scope)."""
        query = NavigationQuery('instance_attributes', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_arguments(self) -> List['ArgumentNode']:
        """Get only immediate child arguments (explicit direct scope)."""
        query = NavigationQuery('arguments', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_returns(self) -> List['ReturnNode']:
        """Get only immediate child returns (explicit direct scope)."""
        query = NavigationQuery('returns', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_aliases(self) -> List['AliasNode']:
        """Get only immediate child aliases (explicit direct scope)."""
        query = NavigationQuery('aliases', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_state_containers(self) -> List['StateContainerNode']:
        """Get only immediate child state containers (explicit direct scope)."""
        query = NavigationQuery('state_containers', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_child_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """Get only immediate child imports (explicit direct scope)."""
        query = NavigationQuery('imports', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # RECURSIVE API - Explicit Cascade Traversal
    # ===============================================
    
    def list_all_packages(self) -> List['PackageNode']:
        """Get all packages in subtree (explicit recursive scope)."""
        query = NavigationQuery('packages', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_modules(self) -> List['ModuleNode']:
        """Get all modules in subtree (explicit recursive scope)."""
        query = NavigationQuery('modules', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_classes(self) -> List['ClassNode']:
        """Get all classes in subtree (explicit recursive scope)."""
        query = NavigationQuery('classes', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_functions(self) -> List['FunctionNode']:
        """Get all functions in subtree (explicit recursive scope)."""
        query = NavigationQuery('functions', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_methods(self) -> List['FunctionNode']:
        """Get all methods in subtree (explicit recursive scope)."""
        query = NavigationQuery('methods', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_state(self) -> List['StateNode']:
        """Get all state in subtree (explicit recursive scope)."""
        query = NavigationQuery('state', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_class_attributes(self) -> List['ClassAttributeNode']:
        """Get all class attributes in subtree (explicit recursive scope)."""
        query = NavigationQuery('class_attributes', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_instance_attributes(self) -> List['InstanceAttributeNode']:
        """Get all instance attributes in subtree (explicit recursive scope)."""
        query = NavigationQuery('instance_attributes', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_arguments(self) -> List['ArgumentNode']:
        """Get all arguments in subtree (explicit recursive scope)."""
        query = NavigationQuery('arguments', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_returns(self) -> List['ReturnNode']:
        """Get all returns in subtree (explicit recursive scope)."""
        query = NavigationQuery('returns', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_aliases(self) -> List['AliasNode']:
        """Get all aliases in subtree (explicit recursive scope)."""
        query = NavigationQuery('aliases', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_state_containers(self) -> List['StateContainerNode']:
        """Get all state containers in subtree (explicit recursive scope)."""
        query = NavigationQuery('state_containers', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    def list_all_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """Get all imports in subtree (explicit recursive scope)."""
        query = NavigationQuery('imports', TraversalScope.CASCADE)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # CONTEXT-SENSITIVE API - Intelligent Defaults
    # ===============================================
    
    def list_packages(self) -> List['PackageNode']:
        """Get packages using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('packages', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_modules(self) -> List['ModuleNode']:
        """Get modules using context-sensitive scope (structural = direct)."""
        query = NavigationQuery('modules', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_classes(self) -> List['ClassNode']:
        """Get classes using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('classes', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_functions(self) -> List['FunctionNode']:
        """Get functions using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('functions', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_methods(self) -> List['FunctionNode']:
        """Get methods using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('methods', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_state(self) -> List['StateNode']:
        """Get state using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('state', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_class_attributes(self) -> List['ClassAttributeNode']:
        """Get class-level attributes using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('class_attributes', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_instance_attributes(self) -> List['InstanceAttributeNode']:
        """Get instance attributes using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('instance_attributes', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_arguments(self) -> List['ArgumentNode']:
        """Get arguments using context-sensitive scope (per-function entities = direct)."""
        query = NavigationQuery('arguments', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_returns(self) -> List['ReturnNode']:
        """Get returns using context-sensitive scope (per-function entities = direct)."""
        query = NavigationQuery('returns', TraversalScope.DIRECT)
        return self._execute_navigation_query(query)
    
    def list_aliases(self) -> List['AliasNode']:
        """Get aliases using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('aliases', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_state_containers(self) -> List['StateContainerNode']:
        """Get state containers using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('state_containers', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    def list_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """Get imports using context-sensitive scope (entity = cascade)."""
        query = NavigationQuery('imports', TraversalScope.CONTEXT)
        return self._execute_navigation_query(query)
    
    # ===============================================
    # NAVIGATION LOOKUP METHODS - Get by Name
    # ===============================================
    
    def get_package(self, name: str) -> Optional['PackageNode']:
        """Get specific package by name."""
        if hasattr(self, '_packages'):
            for package in self._packages:
                if package.name == name:
                    return package
        return None
    
    def get_module(self, name: str) -> Optional['ModuleNode']:
        """Get specific module by name."""
        if hasattr(self, '_modules'):
            for module in self._modules:
                if module.name == name:
                    return module
        return None
    
    def get_class(self, name: str) -> Optional['ClassNode']:
        """Get specific class by name."""
        if hasattr(self, '_classes'):
            for cls in self._classes:
                if cls.name == name:
                    return cls
        return None
    
    def get_function(self, name: str) -> Optional['FunctionNode']:
        """Get specific function by name."""
        if hasattr(self, '_functions'):
            for func in self._functions:
                if func.name == name:
                    return func
        return None
    
    def get_method(self, name: str) -> Optional['FunctionNode']:
        """Get specific method by name."""
        if hasattr(self, '_methods'):
            for method in self._methods:
                if method.name == name:
                    return method
        return None
    
    def get_state(self, name: str) -> Optional['StateNode']:
        """Get specific state by name."""
        if hasattr(self, '_state'):
            for state in self._state:
                if state.name == name:
                    return state
        return None
    
    def get_class_attribute(self, name: str) -> Optional['ClassAttributeNode']:
        """Get specific class attribute by name."""
        if hasattr(self, '_class_attributes'):
            for attr in self._class_attributes:
                if attr.name == name:
                    return attr
        return None
    
    def get_instance_attribute(self, name: str) -> Optional['InstanceAttributeNode']:
        """Get specific instance attribute by name."""
        if hasattr(self, '_instance_attributes'):
            for attr in self._instance_attributes:
                if attr.name == name:
                    return attr
        return None
    
    def get_argument(self, name: str) -> Optional['ArgumentNode']:
        """Get specific argument by name."""
        if hasattr(self, '_arguments'):
            for arg in self._arguments:
                if arg.name == name:
                    return arg
        return None
    
    def get_alias(self, name: str) -> Optional['AliasNode']:
        """Get specific alias by name."""
        if hasattr(self, '_aliases'):
            for alias in self._aliases:
                if hasattr(alias, 'local_name') and alias.local_name == name:
                    return alias
        return None
    
    def get_return(self, name: str = "return") -> Optional['ReturnNode']:
        """Get return node."""
        if hasattr(self, '_return'):
            return self._return
        return None
    
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
            'class_attributes': self.list_class_attributes(),
            'instance_attributes': self.list_instance_attributes(),
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
    
    def _get_direct_children(self) -> List[Any]:
        """
        Get all direct children of this node across all collections.
        
        Used by analyze() to cascade analysis to all children without
        needing to know which specific collection attributes exist.
        
        Returns:
            List of all child nodes from all collections (_packages, _modules, etc.)
        """
        children = []
        
        # Iterate over all attributes to find collection attributes
        for attr_name in dir(self):
            # Look for collection attributes (start with _ but not __)
            if (attr_name.startswith('_') and 
                not attr_name.startswith('__') and
                attr_name not in {'_create_children', '_notes', '_violations'} and  # Exclude methods, notes, and violations
                attr_name != 'parent'):  # Explicitly avoid parent
                
                attr_value = getattr(self, attr_name, None)
                
                # Handle list collections
                if isinstance(attr_value, list):
                    # Only include items that have analyze() method (i.e., are nodes)
                    children.extend([item for item in attr_value if hasattr(item, 'analyze')])
                # Handle dict collections
                elif isinstance(attr_value, dict):
                    # Only include items that have analyze() method
                    children.extend([item for item in attr_value.values() if hasattr(item, 'analyze')])
                # Handle single child (like _return or _type)
                elif attr_value is not None and hasattr(attr_value, 'analyze'):
                    children.append(attr_value)
        
        return children