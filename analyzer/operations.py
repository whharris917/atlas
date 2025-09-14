"""
Defines the atomic operations for the ExpressionTraversal engine.

Each class in this module represents a single, discrete step that can occur
during the evaluation of a complex expression (e.g., looking up a name,
accessing an attribute, calling a function). The ExpressionTraversal engine
linearizes an AST expression into a queue of these operation objects.
"""

import ast
from typing import Optional, Dict, Any

from .scope_manager import ScopeManager
from .logger import get_logger

logger = get_logger()

class Operation:
    """
    Base class for all operations in the Linear Operation Queue.
    
    Each operation represents a single, atomic step in the process of
    evaluating a complex expression.
    """
    def execute(self, context_fqn: Optional[str], recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """
        Executes the operation's logic.

        This method takes the resulting type from the previous operation (the
        context) and returns the resulting type of the current operation,
        enabling the stateful process of Type Propagation.

        Args:
            context_fqn: The FQN of the type of the object the operation is
                         being performed on. For the first operation in a
                         chain, this will be None.
            recon_data: The read-only dictionary of all discovered code
                        entities from the reconnaissance phase.
            scope_manager: The manager for the current lexical scope stack.

        Returns:
            The FQN of the resulting type of this operation, or None if
            the type cannot be determined.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """Provides a user-friendly string representation for logging."""
        return self.__class__.__name__


class GetName(Operation):
    """Represents looking up a variable or name in the current scope."""
    def __init__(self, name: str):
        self.name = name

    def execute(self, context_fqn: Optional[str], recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """
        Executes the GetName operation.

        It first checks the local lexical scope for the variable. If not
        found, it falls back to checking the global reconnaissance data.
        This correctly models Python's name resolution order.
        """
        # 1. Check the local scope first.
        local_type = scope_manager.lookup_variable_type(self.name)
        if local_type:
            logger.debug(f"GetName '{self.name}': Found in local scope with type '{local_type}'.")
            return local_type

        # 2. If not in local scope, check the global recon data.
        logger.debug(f"GetName '{self.name}': Not found in local scope. Performing global lookup.")
        for fqn, data in recon_data.items():
            if fqn.endswith(f".{self.name}"):
                logger.debug(f"GetName '{self.name}': Found global match '{fqn}'.")
                # For a function or class, its 'type' is its own FQN.
                return fqn

        logger.warning(f"GetName '{self.name}': Name not found in local scope or global recon data.")
        return None
    
    def __str__(self) -> str:
        return f"GetName('{self.name}')"


class GetAttribute(Operation):
    """Represents accessing an attribute of an object (e.g., `obj.attr`)."""
    def __init__(self, attr: str):
        self.attr = attr

    def execute(self, context_fqn: Optional[str], recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """
        Executes the GetAttribute operation.

        It looks up the context FQN in the reconnaissance data to find the
        class or module definition, then checks its attributes to find the
        type of the requested attribute.
        """
        if not context_fqn:
            logger.warning(f"GetAttribute '{self.attr}': Cannot execute without a context FQN.")
            return None

        context_data = recon_data.get(context_fqn)
        if not context_data:
            logger.warning(f"GetAttribute '{self.attr}': Context FQN '{context_fqn}' not found in recon data.")
            return None

        attribute_type = context_data.get("attributes", {}).get(self.attr)
        if attribute_type:
            logger.debug(f"GetAttribute '{self.attr}': Found on '{context_fqn}' with type '{attribute_type}'.")
            return attribute_type
        else:
            logger.warning(f"GetAttribute '{self.attr}': Attribute not found on '{context_fqn}'.")
            return None

    def __str__(self) -> str:
        return f".GetAttribute(\"{self.attr}\")"


class CallFunction(Operation):
    """Represents a function or method call (e.g., `func()`)."""
    def execute(self, context_fqn: Optional[str], recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """
        Executes the CallFunction operation.

        It takes the FQN of a function (the context) and looks it up in
        the reconnaissance data to find its return type.
        """
        if not context_fqn:
            logger.warning("CallFunction: Cannot execute without a context FQN for the function to be called.")
            return None

        function_data = recon_data.get(context_fqn)
        if not function_data:
            logger.warning(f"CallFunction: Function FQN '{context_fqn}' not found in recon data.")
            return None
            
        if function_data.get("type") != "function":
            logger.warning(f"CallFunction: Context FQN '{context_fqn}' is not a function.")
            return None

        return_type = function_data.get("return_type")
        if return_type:
            logger.debug(f"CallFunction: '{context_fqn}' returns type '{return_type}'.")
            return return_type
        else:
            logger.debug(f"CallFunction: '{context_fqn}' has no specified return type, assuming 'builtins.NoneType'.")
            return "builtins.NoneType"

    def __str__(self) -> str:
        return f".CallFunction()"
