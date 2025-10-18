"""
Type Inference Engine - Atlas Analysis Phase

Extracted from BaseAnalysisVisitor in Session 55 for better organization.
Handles all type inference and expression linearization logic.
"""

import ast
from typing import List, Optional

from .expression_traversal.operations import Operation, GetName, Dot, CallFunction, GetSubscript
from ..nodes import ClassNode

BUILTIN_CONSTRUCTORS = {
    'list', 'dict', 'set', 'tuple', 'frozenset',
    'str', 'int', 'float', 'bool', 'bytes', 'bytearray',
    'object', 'type', 'range', 'slice',
    'complex', 'memoryview'
}


class TypeInferenceEngine:
    """
    Engine for type inference and expression linearization.
    
    This class was extracted from BaseAnalysisVisitor to separate concerns:
    - BaseAnalysisVisitor: AST traversal, scope population, visitor dispatch
    - TypeInferenceEngine: Expression analysis, type inference
    
    The engine operates on a node (for navigation) and scope (for lookups).
    """
    
    def __init__(self, node, scope):
        """
        Initialize the type inference engine.
        
        Args:
            node: The tree node context (for navigation and FQN resolution)
            scope: The current Scope for variable lookups
        """
        self.node = node
        self.scope = scope
    
    def linearize(self, expr: ast.expr) -> List[Operation]:
        """
        Convert a nested expression into a Linear Operation Queue (LOQ).
        
        This method provides a sequential representation of the operations
        within an expression, which can then be processed left-to-right.
        
        The linearization process is shared by all analysis visitors since
        any visitor may need to analyze expressions (assignments, calls,
        returns, etc.).
        
        CRITICAL: When encountering unsupported AST node types, this method
        creates an UnsupportedExpressionType violation on self.node instead
        of silently failing. This ensures developers are alerted to incomplete
        type inference.
        
        Args:
            expr: AST expression node (Name, Attribute, Call, Subscript, etc.)
            
        Returns:
            List of Operation objects representing the expression in sequence.
            May be incomplete if unsupported node types were encountered.
            
        Example:
            user.profile.email → [GetName('user'), Dot('profile'), Dot('email')]
            obj.method() → [GetName('obj'), Dot('method'), CallFunction()]
            users[0] → [GetName('users'), GetSubscript()]
            [1, 2, 3] → [] (container literals handled directly in _infer_type)
        """
        operations = []
        
        def traverse(node):
            """
            Recursively traverse AST node to build operation queue.
            
            Creates violations for unsupported node types instead of silently
            skipping them, ensuring incomplete type inference is visible.
            
            Supported node types:
            - ast.Name: Variable access (x, user, config)
            - ast.Attribute: Dot access (user.email, obj.method)
            - ast.Call: Function calls (func(), obj.method())
            - ast.Subscript: Index access (list[0], dict["key"])
            - ast.Constant: Literals (5, "hello", True, None)
            - ast.List, ast.Dict, ast.Set, ast.Tuple: Container literals
            
            Examples:
                user.profile.email → Name, Attribute, Attribute
                obj.method() → Name, Attribute, Call
                list[0] → Name, Subscript
                {"key": "value"} → Dict (no operations, handled directly)
            """
            if isinstance(node, ast.Name):
                # Variable name access: x, user, config
                operations.append(GetName(node.id))
            
            elif isinstance(node, ast.Attribute):
                # Attribute access: user.email, obj.method, self.name
                # First process the object being accessed, then the attribute
                traverse(node.value)
                operations.append(Dot(node.attr))
            
            elif isinstance(node, ast.Call):
                # Function/method call: func(), obj.method(), User()
                # First process what's being called, then add the call operation
                traverse(node.func)
                operations.append(CallFunction())
            
            elif isinstance(node, ast.Subscript):
                # Subscript access: list[0], dict["key"], matrix[i][j]
                # First process the container, then add subscript operation
                traverse(node.value)
                operations.append(GetSubscript())
            
            elif isinstance(node, ast.Constant):
                # Literal values: 5, "hello", True, None, 3.14
                # Handled separately in _infer_type() via _infer_literal_type()
                # No operation needed - just skip
                pass
            
            # NEW: Container literals
            elif isinstance(node, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
                # Container literals: [], {}, set(), ()
                # Examples:
                #   [1, 2, 3] → ast.List
                #   {"key": "value"} → ast.Dict
                #   {1, 2, 3} → ast.Set
                #   (1, 2) → ast.Tuple
                #
                # These are terminal expressions (don't chain), so they're
                # handled directly in _infer_type() with no operations needed.
                # They return full generic types: 'List[int]', 'Dict[str, User]', etc.
                pass
            
            else:
                # UNSUPPORTED EXPRESSION TYPE
                # Create note to alert that type inference will be incomplete
                from ..notes import UnsupportedExpressionType
                
                line_number = node.lineno if hasattr(node, 'lineno') else self.node.line_number
                expression_type = node.__class__.__name__
                
                note = UnsupportedExpressionType(
                    parent=self.node,
                    expression_type=expression_type,
                    line_number=line_number
                )
                self.node.add_note(note)
        
        traverse(expr)
        return operations

    def infer_type(self, expr: ast.expr) -> Optional[str]:
        """
        Infer the type of an expression by navigating the tree.
        
        This method handles:
            - Literals (int, str, bool, float, None)
            - Container literals with element type inference (List[User], Dict[str, int])
            - Variable lookups (from scope)
            - Attribute access chains (user.profile.email, self.name)
            - Method calls (obj.method())
            - Subscript operations (list[0], dict["key"])
            
        Uses the tree navigation approach: linearize the expression into
        operations, then navigate the tree directly using .dot() rather
        than interpreting operations.
        
        Special handling for attributes: When navigation encounters an
        InstanceAttributeNode or ClassAttributeNode, it extracts the TYPE
        of that attribute for further navigation, enabling self.name.upper()
        style chains.
        
        Examples:
            5 → 'int'
            "hello" → 'str'
            [1, 2, 3] → 'List[int]'
            [User(), User()] → 'List[sample_files.models.user.User]'
            {"key": "value"} → 'Dict[str, str]'
            user → 'sample_files.models.user.User' (from scope)
            user.email → 'str' (from User's email attribute type)
            User() → 'sample_files.models.user.User' (constructor)
            list() → 'list' (builtin constructor)
            users[0] → 'sample_files.models.user.User' (from List[User] annotation)
        
        Args:
            expr: AST expression node to analyze
            
        Returns:
            Type FQN as string, or None if type cannot be determined
        """
        # Handle simple literals directly (no linearization needed)
        # Examples: 5 → 'int', "hello" → 'str', True → 'bool', None → 'NoneType'
        if isinstance(expr, ast.Constant):
            return self._infer_literal_type(expr.value)
        
        # Handle container literals with element type inference
        # These return full generic types by analyzing their contents
        if isinstance(expr, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
            # Container literals: [], {}, set(), ()
            # Analyze elements to infer full generic type
            # Examples:
            #   [User(), User()] → 'List[sample_files.models.user.User]'
            #   [1, 2, 3] → 'List[int]'
            #   {"key": 1} → 'Dict[str, int]'
            #   {1, 2, 3} → 'Set[int]'
            #   (1, 2) → 'Tuple[int, ...]'
            #
            # Falls back to plain types for heterogeneous or empty containers:
            #   [1, "hello"] → 'list' (heterogeneous)
            #   [] → 'list' (empty)
            return self._infer_container_element_type(expr)
        
        # Linearize expression into operation queue
        # This converts nested expressions into sequential operations
        operations = self.linearize(expr)
        
        # Empty operation queue - cannot infer type
        if not operations:
            return None
        
        # Navigate the tree using the operation queue
        # Process each operation in sequence, where output of one becomes input of next
        current_type = None
        current_node = None
        project = self.node.get_project()
        
        for op in operations:
            if isinstance(op, GetName):
                # Variable lookup in scope
                # Example: 'user' → 'sample_files.models.user.User'
                current_type = self.scope.lookup(op.name)
                if current_type:
                    # Try to get tree node for further navigation
                    current_node = project.get_node_by_fqn(current_type)
                else:
                    # Variable not in scope - cannot continue
                    return None
            
            elif isinstance(op, Dot):
                # Navigate to child via .dot() method
                # Example: user.email → navigate from User node to email attribute
                if current_node:
                    child = current_node.dot(op.attr_name)
                    if child:
                        # Special handling for attribute nodes (InstanceAttributeNode, ClassAttributeNode)
                        # Attributes store LOCATION in their FQN, but we need their TYPE
                        from ..nodes.instance_attribute_node import InstanceAttributeNode
                        from ..nodes.class_attribute_node import ClassAttributeNode
                        
                        if isinstance(child, (InstanceAttributeNode, ClassAttributeNode)):
                            # Extract type from attribute's TypeNode child
                            type_node = child.dot("type")
                            if type_node:
                                # Get the actual type string (e.g., "str", "List[User]")
                                current_type = type_node.type_string
                                
                                # Try to resolve to tree node for further navigation
                                current_node = project.get_node_by_fqn(current_type)
                                # If None (builtin type), we have the type but can't navigate further
                            else:
                                # Attribute has no type annotation
                                return None
                        else:
                            # Standard navigation for methods, classes, etc.
                            current_node = child
                            current_type = child.fqn if hasattr(child, 'fqn') else None
                    else:
                        # Navigation failed - child not found
                        return None
                else:
                    # No node to navigate from - cannot continue
                    return None
            
            elif isinstance(op, CallFunction):
                # Function or method call: func(), obj.method(), User()
                # Three cases: class constructor, builtin constructor, function/method
                
                # CASE 1: Class constructor call
                # Example: User() where current_node is User ClassNode
                if current_node and isinstance(current_node, ClassNode):
                    # Constructor returns instance of the class
                    current_type = current_node.fqn
                    # Keep current_node for potential chaining: User().method()
                
                # CASE 2: Builtin constructor call  
                # Example: list(), dict() where current_type is 'list' or 'dict'
                elif current_type in BUILTIN_CONSTRUCTORS:
                    # Constructor returns instance of the builtin type
                    # current_type is already correct ('list', 'dict', etc.)
                    current_node = None  # No tree node for builtins
                
                # CASE 3: Function or method call
                # Example: get_user() or obj.method()
                elif current_node:
                    # Get return type from function's return annotation
                    return_node = current_node.dot("return")
                    if not return_node:
                        # No return annotation (returns None implicitly or
                        # no annotation or doesn't exist)
                        return None
                    
                    type_node = return_node.dot("type")
                    if not type_node:
                        # Return node exists but no type annotation
                        return None
                    
                    # Extract the return type from TypeNode
                    current_type = ast.unparse(type_node.source_data)
                    
                    # Try to resolve return type to tree node for chaining
                    # Example: get_user().get_email() continues navigation
                    current_node = project.get_node_by_fqn(current_type)
                    
                    if not current_node:
                        # Type exists but no node (builtin or external)
                        # Can't navigate further but have the type
                        return current_type
                
                else:
                    # No current_node and not a builtin - cannot infer
                    # This happens when we have expressions like undefined_var()
                    return None
            
            elif isinstance(op, GetSubscript):
                # Subscript operation: list[0], dict["key"], matrix[i][j]
                # Extract element type from generic annotations
                # Examples:
                #   users: List[User] → users[0] returns User
                #   data: Dict[str, int] → data["key"] returns int
                #   matrix: List[List[int]] → matrix[0] returns List[int]
                
                if not current_type:
                    # No type to subscript
                    return None
                
                # Try to extract element type from generic annotation
                element_type = self._extract_element_type_from_generic(current_type)
                
                if element_type:
                    # Successfully extracted element type
                    # Update current_type for potential chaining: matrix[i][j]
                    current_type = element_type
                    
                    # Try to get tree node for the element type
                    # This enables further navigation: users[0].email
                    current_node = project.get_node_by_fqn(element_type)
                    
                    # If no tree node, keep the type string but clear node
                    # (e.g., for builtins like int, str)
                    if not current_node:
                        current_node = None
                else:
                    # Could not extract element type
                    # This happens for:
                    # 1. Non-generic types (e.g., subscripting a plain 'list' without type param)
                    # 2. Unsupported generic patterns
                    # Return None to indicate we can't infer the element type
                    return None
        
        return current_type
    
    def _infer_literal_type(self, value) -> str:
        """
        Infer type from a literal value.
        
        Args:
            value: The literal value from ast.Constant
            
        Returns:
            Type name as string (e.g., "int", "str", "bool", "NoneType")
        """
        return type(value).__name__
    
    def _infer_container_element_type(self, expr: ast.expr) -> Optional[str]:
        """
        Infer the element type from a container literal by analyzing its contents.
        
        For homogeneous containers, returns the full generic type string.
        For heterogeneous containers, returns the plain container type.
        
        This enables type inference without requiring annotations:
            [User(), User()] → 'List[sample_files.models.user.User]'
            [1, 2, 3] → 'List[int]'
            {"key": User()} → 'Dict[str, sample_files.models.user.User]'
            [1, "hello"] → 'list' (heterogeneous - fall back to plain type)
            [] → 'list' (empty - no type info)
        
        Args:
            expr: ast.List, ast.Dict, ast.Set, or ast.Tuple node
            
        Returns:
            Full generic type string if elements are homogeneous, plain type otherwise
        """
        if isinstance(expr, ast.List):
            if not expr.elts:
                # Empty list - no type information
                return 'list'
            
            # Infer type of first element
            first_type = self.infer_type(expr.elts[0])
            if not first_type:
                return 'list'
            
            # Check if all elements have the same type
            for element in expr.elts[1:]:
                elem_type = self.infer_type(element)
                if elem_type != first_type:
                    # Heterogeneous list - return plain type
                    return 'list'
            
            # Homogeneous list - return generic type
            return f'List[{first_type}]'
        
        elif isinstance(expr, ast.Dict):
            if not expr.keys:
                # Empty dict - no type information
                return 'dict'
            
            # Infer type of first key and value
            first_key_type = self.infer_type(expr.keys[0])
            first_value_type = self.infer_type(expr.values[0])
            
            if not first_key_type or not first_value_type:
                return 'dict'
            
            # Check if all keys and values have consistent types
            for key, value in zip(expr.keys[1:], expr.values[1:]):
                key_type = self.infer_type(key)
                value_type = self.infer_type(value)
                
                if key_type != first_key_type or value_type != first_value_type:
                    # Heterogeneous dict - return plain type
                    return 'dict'
            
            # Homogeneous dict - return generic type
            return f'Dict[{first_key_type}, {first_value_type}]'
        
        elif isinstance(expr, ast.Set):
            if not expr.elts:
                # Empty set - no type information
                return 'set'
            
            # Infer type of first element
            first_type = self.infer_type(expr.elts[0])
            if not first_type:
                return 'set'
            
            # Check if all elements have the same type
            for element in expr.elts[1:]:
                elem_type = self.infer_type(element)
                if elem_type != first_type:
                    # Heterogeneous set - return plain type
                    return 'set'
            
            # Homogeneous set - return generic type
            return f'Set[{first_type}]'
        
        elif isinstance(expr, ast.Tuple):
            if not expr.elts:
                # Empty tuple - no type information
                return 'tuple'
            
            # For tuples, we use homogeneous approach with ellipsis notation
            # Tuple[int, int, int] becomes Tuple[int, ...]
            first_type = self.infer_type(expr.elts[0])
            if not first_type:
                return 'tuple'
            
            # Check if all elements have the same type
            for element in expr.elts[1:]:
                elem_type = self.infer_type(element)
                if elem_type != first_type:
                    # Heterogeneous tuple - return plain type
                    return 'tuple'
            
            # Homogeneous tuple - return generic type with ellipsis notation
            return f'Tuple[{first_type}, ...]'
        
        return None
    
    def extract_type_from_annotation(self, annotation: ast.expr) -> Optional[str]:
        """
        Extract type from a type annotation node.
        
        Handles both simple types (int, str) and complex generic types
        (List[int], Dict[str, User], Optional[str]).
        
        Args:
            annotation: The ast.annotation node from AnnAssign
            
        Returns:
            Type as string, or None if extraction fails
        """
        try:
            return ast.unparse(annotation)
        except Exception:
            return None
    
    def resolve_annotation(self, annotation_str: str) -> str:
        """
        Resolve an annotation string to its FQN.
        
        Takes an annotation like "User" and resolves it to its full FQN
        like "sample_files.models.User" by looking it up in scope.
        
        For simple type names, uses scope lookup.
        For complex types like List[User], recursively resolves inner types.
        For builtins and already-qualified names, returns as-is.
        
        Args:
            annotation_str: The annotation string (e.g., "User", "List[User]")
            
        Returns:
            Resolved FQN or annotation string
        """
        # If it's a simple name (no dots, no brackets), try scope lookup
        if '.' not in annotation_str and '[' not in annotation_str:
            resolved = self.scope.lookup(annotation_str)
            if resolved:
                return resolved
            # If not in scope, return as-is (might be external type)
            return annotation_str
        
        # If it has brackets, it's a generic type like List[User] or Optional[User]
        # For now, return as-is - we can add recursive resolution later
        # TODO: Parse and resolve inner types (e.g., "List[User]" → "List[sample_files.models.User]")
        return annotation_str
    
    def _extract_element_type_from_generic(self, generic_type_str: str) -> Optional[str]:
        """
        Extract element type from a generic type annotation.
        
        Handles common generic container types and extracts their element types:
        - List[User] → User
        - Set[int] → int  
        - Tuple[str, ...] → str
        - Dict[str, User] → User (returns value type)
        - Optional[User] → User
        
        This enables type inference through subscript operations:
            users: List[User] = [...]
            first_user = users[0]  # Infers type: User
        
        Args:
            generic_type_str: Generic type annotation string (e.g., "List[User]", "Dict[str, int]")
            
        Returns:
            Element type as string, or None if extraction fails
            
        Examples:
            _extract_element_type_from_generic("List[User]") → "User"
            _extract_element_type_from_generic("Dict[str, int]") → "int"
            _extract_element_type_from_generic("Set[str]") → "str"
            _extract_element_type_from_generic("User") → None (not generic)
        """
        # Not a generic type if no brackets
        if '[' not in generic_type_str or ']' not in generic_type_str:
            return None
        
        # Extract the container type and inner content
        # Example: "List[User]" → container="List", inner="User"
        try:
            bracket_start = generic_type_str.index('[')
            bracket_end = generic_type_str.rindex(']')
            
            container = generic_type_str[:bracket_start]
            inner = generic_type_str[bracket_start + 1:bracket_end]
            
            # Handle Dict specially - return value type (second type parameter)
            # Dict[str, User] → User
            if container in ('Dict', 'dict'):
                # Split by comma, handling nested generics
                parts = self._split_type_parameters(inner)
                if len(parts) >= 2:
                    element_type = parts[1].strip()
                    # Recursively resolve if the value type is also generic
                    # e.g., Dict[str, Optional[User]] → Optional[User] → User
                    resolved = self.resolve_annotation(element_type)
                    return resolved
                return None
            
            # Handle Optional - unwrap to inner type
            # Optional[User] → User
            elif container == 'Optional':
                element_type = inner.strip()
                resolved = self.resolve_annotation(element_type)
                return resolved
            
            # Handle List, Set, Tuple - return first type parameter
            # List[User] → User
            # Set[int] → int
            # Tuple[str, ...] → str
            elif container in ('List', 'list', 'Set', 'set', 'Tuple', 'tuple'):
                # For Tuple, handle varargs notation: Tuple[str, ...]
                parts = self._split_type_parameters(inner)
                if parts:
                    element_type = parts[0].strip()
                    resolved = self.resolve_annotation(element_type)
                    return resolved
                return None
            
            # Unknown generic type - return None
            return None
            
        except (ValueError, IndexError):
            # Malformed generic type
            return None

    def _split_type_parameters(self, params_str: str) -> list:
        """
        Split type parameters by comma, respecting nested brackets.
        
        Handles cases like:
        - "str, int" → ["str", "int"]
        - "List[int], Dict[str, User]" → ["List[int]", "Dict[str, User]"]
        
        Args:
            params_str: String of comma-separated type parameters
            
        Returns:
            List of parameter strings
        """
        parts = []
        current = []
        depth = 0
        
        for char in params_str:
            if char == '[':
                depth += 1
                current.append(char)
            elif char == ']':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                # Top-level comma - split here
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)
        
        # Add the last part
        if current:
            parts.append(''.join(current))
        
        return parts