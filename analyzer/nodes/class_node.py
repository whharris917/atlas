"""
Class Node - Atlas Rewrite

Node representing a Python class with automatic child creation.
Enhanced with comprehensive attribute discovery for both class-level and instance attributes.
Enhanced with base class extraction following self-extraction pattern.
Enhanced with base_class_fqns for Analysis Phase inheritance resolution.
"""

import ast
from typing import List, Union, Optional, Dict, TYPE_CHECKING
from ..core import TreeNode, BaseNode
from ..reconnaissance.visitors import ClassReconnaissanceVisitor
from .function_node import FunctionNode
from ..violations import MultipleTargetAttributeAssignment

if TYPE_CHECKING:
    from .class_attribute_node import ClassAttributeNode
    from .instance_attribute_node import InstanceAttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class with comprehensive attribute discovery."""
    
    def __init__(self, parent: BaseNode, source_data: ast.ClassDef):
        if not isinstance(source_data, ast.ClassDef):
            raise TypeError("ClassNode requires ast.ClassDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._methods: List[FunctionNode] = []
        self._class_attributes: List['ClassAttributeNode'] = []
        self._instance_attributes: List['InstanceAttributeNode'] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
        
        # Extract base class names during initialization (self-extraction pattern)
        self._base_classes: List[str] = self._extract_base_classes()
        
        # Analysis Phase will populate this with resolved FQNs
        # Starts empty, filled by ClassAnalysisVisitor during analyze()
        self.base_class_fqns: List[str] = []
    
    def _extract_name(self) -> str:
        """Extract class name from ast.ClassDef node."""
        return self.source_data.name
    
    def _extract_base_classes(self) -> List[str]:
        """
        Extract base class names from ast.ClassDef.bases.
        
        Returns raw base class names exactly as they appear in source code.
        This is pure Reconnaissance Phase work - just extracting what's present
        in the AST without any resolution or semantic analysis.
        
        Resolution of these names to actual FQNs happens during Analysis Phase
        using scope lookup, similar to how any other identifier is resolved.
        
        Examples:
            class Child(Parent): → ["Parent"]
            class User(BaseModel, JSONMixin): → ["BaseModel", "JSONMixin"]
            class Handler(http.BaseHandler): → ["http.BaseHandler"]
            class Foo: → [] (no explicit bases)
        
        Returns:
            List of base class names as strings. Empty list if no bases.
        """
        bases = []
        for base in self.source_data.bases:
            # Use ast.unparse to handle both simple names (ast.Name)
            # and qualified names (ast.Attribute)
            bases.append(ast.unparse(base))
        return bases
    
    def _create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        # Use specialized visitor for class-level discovery
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.source_data)

    def analyze(self, parent_scope=None):
        """
        Analyze this class by running ClassAnalysisVisitor.
        
        Creates a ClassAnalysisVisitor for this node and runs it to perform
        type inference and scope building for class-level code. The visitor
        pushes a new scope frame in its __init__, which we pop after analysis.
        
        Child nodes (methods, nested classes) will be analyzed via their own
        analyze() methods when the visitor encounters them.
        
        Args:
            parent_scope: Scope from parent visitor (ModuleAnalysisVisitor)
        """
        from ..analysis.visitors import ClassAnalysisVisitor
        
        print(f"   Analyzing class: {self.name}")
        visitor = ClassAnalysisVisitor(self, parent_scope)
        
        try:
            # Visit the class BODY, not the ClassDef itself
            # This prevents the visitor from seeing the class definition again
            for item in self.source_data.body:
                visitor.visit(item)
        finally:
            # Pop the frame that ClassAnalysisVisitor pushed in __init__
            if parent_scope:
                parent_scope.pop_frame()
        
        print(f"   Class analysis complete: {self.name}")

    def create_method(self, method_ast: ast.FunctionDef) -> FunctionNode:
        """Create and hook a new method from AST node."""
        method_node = FunctionNode(parent=self, source_data=method_ast)
        self._methods.append(method_node)
        return method_node
    
    def create_class_attribute(self, attr_ast: Union[ast.AnnAssign, ast.Assign]) -> 'ClassAttributeNode':
        """
        Create and hook a new class-level attribute from AST node.
        
        Called by ClassReconnaissanceVisitor when discovering class-level
        attribute assignments in the class body.
        
        Args:
            attr_ast: Either ast.AnnAssign (annotated) or ast.Assign (unannotated)
                     for class-level attribute definition
        
        Returns:
            The created ClassAttributeNode
        """
        # Import here to avoid circular imports
        from .class_attribute_node import ClassAttributeNode
        
        attr_node = ClassAttributeNode(parent=self, source_data=attr_ast)
        self._class_attributes.append(attr_node)
        return attr_node
    
    def create_instance_attribute(self, attr_ast: Union[ast.AnnAssign, ast.Assign]) -> 'InstanceAttributeNode':
        """
        Create and hook a new instance attribute from AST node.
        
        Called by ClassReconnaissanceVisitor when discovering instance
        attribute assignments in __init__ method body.
        
        Args:
            attr_ast: Either ast.AnnAssign (annotated) or ast.Assign (unannotated)
                      for instance attribute assignment
        
        Returns:
            The created InstanceAttributeNode
        """
        # Import here to avoid circular imports
        from .instance_attribute_node import InstanceAttributeNode
        
        attr_node = InstanceAttributeNode(parent=self, source_data=attr_ast)
        self._instance_attributes.append(attr_node)
        return attr_node
    
    def create_multiple_target_attribute_violation(self, target_names: List[str], assignment_context: str):
        """
        Create MultipleTargetAttributeAssignment violation ornament.
        
        Called by ClassReconnaissanceVisitor when encountering attribute
        assignments with multiple targets that cannot be properly represented
        as individual attribute nodes.
        
        Args:
            target_names: List of target names in the multi-target assignment
            assignment_context: Context description ("class-level" or "instance-level")
        
        Returns:
            The created MultipleTargetAttributeAssignment
        """
        violation = MultipleTargetAttributeAssignment(self)
        self.add_violation(violation)
        return violation
    
    @property
    def base_classes(self) -> List[str]:
        """
        Base class names as they appear in the source code.
        
        These are unresolved names extracted during Reconnaissance Phase.
        They represent what was written in the class definition, not what
        they reference. Resolution to FQNs happens during Analysis Phase
        using scope lookup, similar to any other identifier resolution.
        
        Examples:
            class Child(Parent): → ["Parent"]
            class User(BaseModel, JSONMixin): → ["BaseModel", "JSONMixin"]
            class Handler(http.BaseHandler): → ["http.BaseHandler"]
            class Foo: → [] (no explicit bases, implicitly inherits from object)
        
        Note:
            Empty list means no explicit base classes were specified.
            Python's implicit object inheritance is not included.
        
        Returns:
            List of base class names as strings. Empty if no bases.
        """
        return self._base_classes[:]