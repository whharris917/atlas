"""
Atlas Note System - Unified hierarchy for all analysis artifacts.

All notes are simple ornamental data classes that attach to nodes.
They represent discoveries, violations, warnings, and limitations found during analysis.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import BaseNode


# =============================================================================
# Base Classes
# =============================================================================

class Note:
    """
    Base class for all notes attached to nodes.
    
    Notes are lightweight ornamental objects that record information
    discovered during reconnaissance and analysis phases. They contain
    only essential data and have no complex logic.
    """
    
    def __init__(self, parent: 'BaseNode'):
        """
        Create a note attached to a parent node.
        
        Args:
            parent: The node this note is attached to
        """
        if not parent:
            raise ValueError("Note requires parent node")
        
        self.parent = parent
    
    def __repr__(self) -> str:
        """Simple string representation for debugging."""
        return f"{self.__class__.__name__}({self.parent.__class__.__name__})"


# =============================================================================
# Code Standard Violations
# =============================================================================

class CodeStandardViolation(Note):
    """
    Violations of Python coding standards (style/convention issues).
    
    These represent missing type hints or other style violations that
    don't necessarily indicate bugs but violate best practices.
    """
    pass


class MissingArgumentTypeHint(CodeStandardViolation):
    """Function argument is missing a type hint."""
    pass


class MissingReturnTypeHint(CodeStandardViolation):
    """Function is missing a return type hint."""
    pass


class MissingClassAttributeTypeHint(CodeStandardViolation):
    """Class attribute is missing a type hint."""
    pass


class MissingInstanceAttributeTypeHint(CodeStandardViolation):
    """Instance attribute is missing a type hint."""
    pass


class MultipleTargetAttributeAssignment(CodeStandardViolation):
    """Assignment with multiple targets (e.g., x = y = value)."""
    pass


# =============================================================================
# Warnings (Actual Mistakes)
# =============================================================================

class Warning(Note):
    """
    Potential errors in the code.
    
    These represent likely mistakes in the code, such as type mismatches
    between annotations and inferred types.
    """
    pass


class IncorrectTypeAnnotation(Warning):
    """
    Type annotation doesn't match the inferred runtime type.
    
    Example:
        user: User = "not a user"  # Annotation says User, value is str
        count: int = 3.14          # Annotation says int, value is float
    
    The annotation (type hint) doesn't match what the value actually is.
    This helps catch bugs where type hints are incorrect or misleading.
    """
    
    def __init__(self, parent: 'BaseNode', variable_name: str, annotation: str, inferred: str, line_number: int):
        """
        Create an incorrect type annotation warning.
        
        Args:
            parent: The node where the mismatch occurred
            variable_name: Name of the variable with incorrect annotation
            annotation: The declared type annotation
            inferred: The inferred runtime type
            line_number: Line number where the mismatch appears
        """
        super().__init__(parent)
        self.variable_name = variable_name
        self.annotation = annotation
        self.inferred = inferred
        self.line_number = line_number
    
    def __repr__(self) -> str:
        """Enhanced representation with variable name and annotation details."""
        return (f"IncorrectTypeAnnotation({self.variable_name}: "
                f"annotation={self.annotation}, inferred={self.inferred}, "
                f"line={self.line_number})")


# =============================================================================
# Atlas Limitations
# =============================================================================

class AtlasLimitation(Note):
    """
    Features that Atlas cannot yet analyze.
    
    These represent gaps in Atlas's current implementation rather than
    issues with the code being analyzed.
    """
    pass


class UnsupportedExpressionType(AtlasLimitation):
    """
    Expression type that cannot be linearized for type inference.
    
    The linearization engine converts nested expressions into a Linear Operation Queue (LOQ)
    for type propagation. When it encounters an AST node type that isn't yet implemented,
    it creates this note to indicate that type inference will be incomplete.
    
    Examples of currently unsupported expressions:
        - Binary operations: user.age + 10, x * y
        - Boolean operations: user.is_active and user.is_verified
        - Comparison operations: user.age > 18
        - Unary operations: -balance, not is_active
        - Conditional expressions: "admin" if is_admin else "user"
        - Comprehensions: [x.name for x in users]
        - Lambda expressions: lambda x: x.name
        - Await expressions: await fetch_data()
    """
    
    def __init__(self, parent: 'BaseNode', expression_type: str, line_number: int):
        """
        Create an unsupported expression type note.
        
        Args:
            parent: The node where type inference was attempted
            expression_type: The AST node class name (e.g., "BinOp", "Compare")
            line_number: Line number where the unsupported expression appears
        """
        super().__init__(parent)
        self.expression_type = expression_type
        self.line_number = line_number
    
    def __repr__(self) -> str:
        """Enhanced representation including expression type and line number."""
        return (f"UnsupportedExpressionType(type={self.expression_type}, "
                f"line={self.line_number})")


# =============================================================================
# Analysis Results
# =============================================================================

class AnalysisResult(Note):
    """
    Information discovered during the analysis phase.
    
    These notes record what Atlas learned while analyzing the code,
    including successful discoveries and failed attempts.
    """
    pass


class AnalysisSuccess(AnalysisResult):
    """Successful analysis discoveries."""
    pass


class AnalysisFailure(AnalysisResult):
    """Failed analysis attempts."""
    pass


# =============================================================================
# Analysis Success Notes
# =============================================================================

class ScopeAddition(AnalysisSuccess):
    """
    Entity added to scope during analysis.
    
    Records when a class, function, or import is added to the current scope,
    making it available for type resolution.
    """
    
    def __init__(self, parent: 'BaseNode', entity_name: str, entity_fqn: str, entity_type: str):
        """
        Create a scope addition note.
        
        Args:
            parent: The node where the entity was added to scope
            entity_name: Simple name of the entity (e.g., "User")
            entity_fqn: Fully qualified name (e.g., "sample_files.models.user.User")
            entity_type: Type of entity ("class", "function", "import")
        """
        super().__init__(parent)
        self.entity_name = entity_name
        self.entity_fqn = entity_fqn
        self.entity_type = entity_type
    
    def __repr__(self) -> str:
        return f"ScopeAddition({self.entity_type}: {self.entity_name} → {self.entity_fqn})"


class BaseClassResolution(AnalysisSuccess):
    """
    Base class name resolved to its fully qualified name.
    
    Records when a base class reference (e.g., "BaseEntity") is successfully
    resolved to its FQN (e.g., "sample_files.core.base.BaseEntity").
    """
    
    def __init__(self, parent: 'BaseNode', base_name: str, base_fqn: str):
        """
        Create a base class resolution note.
        
        Args:
            parent: The class node where base class was resolved
            base_name: Simple name as it appears in source (e.g., "BaseEntity")
            base_fqn: Resolved fully qualified name
        """
        super().__init__(parent)
        self.base_name = base_name
        self.base_fqn = base_fqn
    
    def __repr__(self) -> str:
        return f"BaseClassResolution({self.base_name} → {self.base_fqn})"


class TypeInference(AnalysisSuccess):
    """
    Variable type successfully inferred.
    
    Records when Atlas successfully determines the type of a variable
    from its value or annotation.
    """
    
    def __init__(self, parent: 'BaseNode', variable_name: str, inferred_type: str, line_number: int):
        """
        Create a type inference note.
        
        Args:
            parent: The node where type inference occurred
            variable_name: Name of the variable
            inferred_type: The inferred type (FQN or builtin)
            line_number: Line number where inference occurred
        """
        super().__init__(parent)
        self.variable_name = variable_name
        self.inferred_type = inferred_type
        self.line_number = line_number
    
    def __repr__(self) -> str:
        return f"TypeInference({self.variable_name}: {self.inferred_type} at line {self.line_number})"


class ParameterDiscovery(AnalysisSuccess):
    """
    Function parameter added to scope.
    
    Records when a function parameter is discovered and added to the
    function's scope, making it available for type inference within
    the function body.
    """
    
    def __init__(self, parent: 'BaseNode', parameter_name: str):
        """
        Create a parameter discovery note.
        
        Args:
            parent: The function node where parameter was discovered
            parameter_name: Name of the parameter
        """
        super().__init__(parent)
        self.parameter_name = parameter_name
    
    def __repr__(self) -> str:
        return f"ParameterDiscovery({self.parameter_name})"


# =============================================================================
# Analysis Failure Notes
# =============================================================================

class TypeInferenceFailure(AnalysisFailure):
    """
    Could not determine the type of a variable.
    
    Records when type inference fails for a variable, either because
    the value is too complex or because Atlas doesn't support the
    expression type.
    """
    
    def __init__(self, parent: 'BaseNode', variable_name: str, line_number: int):
        """
        Create a type inference failure note.
        
        Args:
            parent: The node where type inference failed
            variable_name: Name of the variable
            line_number: Line number where failure occurred
        """
        super().__init__(parent)
        self.variable_name = variable_name
        self.line_number = line_number
    
    def __repr__(self) -> str:
        return f"TypeInferenceFailure({self.variable_name} at line {self.line_number})"


# =============================================================================
# Public API Exports
# =============================================================================

__all__ = [
    # Base classes
    'Note',
    'CodeStandardViolation',
    'Warning',
    'AtlasLimitation',
    'AnalysisResult',
    'AnalysisSuccess',
    'AnalysisFailure',
    
    # Code standard violations
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint',
    'MissingClassAttributeTypeHint',
    'MissingInstanceAttributeTypeHint',
    'MultipleTargetAttributeAssignment',
    
    # Warnings
    'IncorrectTypeAnnotation',
    
    # Atlas limitations
    'UnsupportedExpressionType',
    
    # Analysis successes
    'ScopeAddition',
    'BaseClassResolution',
    'TypeInference',
    'ParameterDiscovery',
    
    # Analysis failures
    'TypeInferenceFailure',
]