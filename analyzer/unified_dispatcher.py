import ast
from typing import Dict, Any, List, Optional

# Forward declarations for type hinting complex inter-dependencies
class NameResolver:
    pass

class TypeInferenceEngine:
    pass

from .logger import get_logger, LogLevel
from .utils import get_source

# --- Abstract Resolution Operations ---

class ResolutionOperation:
    """Base class for a quantum of analysis."""
    def __init__(self, node: ast.AST):
        self.node = node

class NameOperation(ResolutionOperation):
    """Represents resolving a simple name."""
    pass

class AttributeOperation(ResolutionOperation):
    """Represents accessing an attribute (e.g., .foo)."""
    pass

class CallOperation(ResolutionOperation):
    """Represents a function or method call (e.g., ())."""
    pass

# --- The Unified Dispatcher ---

class UnifiedResolutionDispatcher:
    """
    The computational core of the Atlas engine. It models name resolution
    as a state transition process, operating on a linear sequence of
    abstract operations.
    """

    def __init__(self, recon_data: Dict[str, Any], name_resolver: NameResolver, type_inference: TypeInferenceEngine):
        self.recon_data = recon_data
        self.name_resolver = name_resolver
        self.type_inference = type_inference
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str):
        getattr(self.logger, level.name.lower())(message, get_source())

    def resolve_node_type(self, node: ast.expr, context: Dict[str, Any]) -> Optional[str]:
        """
        Primary public method. Resolves the final type of any expression node.
        """
        self._log(LogLevel.TRACE, f"Unified Dispatcher initiated for node: {ast.unparse(node)}")
        try:
            operations = self._linearize_operations(node)
            final_fqn = self._execute_resolution_chain(operations, context)
            self._log(LogLevel.DEBUG, f"Unified Dispatcher resolved {ast.unparse(node)} -> {final_fqn}")
            return final_fqn
        except Exception as e:
            self._log(LogLevel.ERROR, f"Unified Dispatcher failed for {ast.unparse(node)}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}", get_source())
            return None

    def _linearize_operations(self, node: ast.expr) -> List[ResolutionOperation]:
        """
        Translates a complex, nested AST node into a simple, linear sequence
        of abstract semantic operations.
        """
        operations = []
        current_node = node
        while True:
            if isinstance(current_node, ast.Call):
                operations.append(CallOperation(current_node))
                current_node = current_node.func
            elif isinstance(current_node, ast.Attribute):
                operations.append(AttributeOperation(current_node))
                current_node = current_node.value
            elif isinstance(current_node, ast.Name):
                operations.append(NameOperation(current_node))
                break
            else:
                self._log(LogLevel.WARNING, f"Unsupported node type in linearization: {type(current_node)}")
                break
        return list(reversed(operations))

    def _execute_resolution_chain(self, operations: List[ResolutionOperation], context: Dict[str, Any]) -> Optional[str]:
        """
        Executes the sequence of operations as a state machine.
        The 'state' at each step is the FQN of the type resolved so far.
        """
        current_type_fqn: Optional[str] = None

        for i, op in enumerate(operations):
            if isinstance(op, NameOperation):
                current_type_fqn = self._handle_name(op, context)
            elif isinstance(op, AttributeOperation):
                if not current_type_fqn:
                    self._log(LogLevel.WARNING, f"Cannot resolve attribute '{op.node.attr}' without a base type.")
                    return None
                current_type_fqn = self._handle_attribute(op, current_type_fqn, context)
            elif isinstance(op, CallOperation):
                if not current_type_fqn:
                    self._log(LogLevel.WARNING, f"Cannot perform call on an unresolved type.")
                    return None
                current_type_fqn = self._handle_call(op, current_type_fqn, context)

            if not current_type_fqn and i < len(operations) - 1:
                self._log(LogLevel.DEBUG, f"Resolution chain broken at operation {i+1} ({type(op).__name__})")
                return None

        return current_type_fqn

    def _handle_name(self, op: NameOperation, context: Dict[str, Any]) -> Optional[str]:
        """State transition for a simple name. The starting point of a chain."""
        symbol_manager = context.get('symbol_manager')
        if symbol_manager:
            symbol_type = symbol_manager.get_variable_type(op.node.id)
            if symbol_type:
                return symbol_type
        return self.name_resolver.resolve_name([op.node.id], context)

    def _handle_attribute(self, op: AttributeOperation, current_type_fqn: str, context: Dict[str, Any]) -> Optional[str]:
        """State transition for attribute access."""
        # --- FIX ---
        # The TypeInferenceEngine does not have a public 'infer_attribute_type' method.
        # This logic manually replicates the required steps for a simple case.
        # It finds the class in recon_data, then checks for a method or attribute.
        # TODO: This needs to be expanded to handle inheritance.
        attr_name = op.node.attr
        class_data = self.recon_data.get("classes", {}).get(current_type_fqn)

        if not class_data:
            return None

        # Check if the attribute is a method of the class
        for method in class_data.get("methods", []):
            if method.get("name") == attr_name:
                return method.get("fqn")

        # Check if it's a class-level attribute
        for attribute in class_data.get("attributes", []):
            if attribute.get("name") == attr_name:
                attr_type_str = attribute.get("type")
                if attr_type_str:
                    # Use the existing helper from the inference engine to resolve the type string
                    return self.type_inference._resolve_return_type_to_fqn(attr_type_str, context)
        
        return None

    def _handle_call(self, op: CallOperation, current_type_fqn: str, context: Dict[str, Any]) -> Optional[str]:
        """State transition for a call."""
        function_data = self.recon_data.get("functions", {}).get(current_type_fqn)

        if not function_data:
            self._log(LogLevel.WARNING, f"Could not find function data for FQN in _handle_call: {current_type_fqn}")
            return None
            
        return_type_str = function_data.get("return_type")
        if not return_type_str:
            return None

        # --- FIX ---
        # The method '_get_return_type_from_function_data' does not exist.
        # The correct existing method is 'infer_from_return_type_str'.
        return self.type_inference.infer_from_return_type_str(return_type_str, context)

