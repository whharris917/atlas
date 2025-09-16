"""
Enhanced Scope Manager - Code Atlas

Provides unified scope and context management for the Atlas analysis engine.
This module replaces the dual scope tracking system (scope_stack + SymbolTableManager)
with a single, theoretically sound approach that properly supports lexical scoping
while maintaining sophisticated hierarchical logging.

Key Features:
- Unified scope and variable type tracking
- Direct logger context integration
- Proper lexical scoping support
- Clean interface for AnalysisVisitor integration
- Foundation for Expression Traversal engine
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from .logger import get_logger, LogLevel
from .utils import get_source


class ScopeType(Enum):
    """Types of lexical scopes in Python code analysis."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"


class ScopeFrame:
    """
    Represents a single lexical scope with enhanced metadata for context tracking.
    
    Each ScopeFrame contains:
    - Variable type mappings for the scope
    - Metadata for logger context (FQN, scope type)
    - Parent scope reference for hierarchical context
    """
    
    def __init__(self, fqn: str, scope_type: ScopeType, parent: Optional['ScopeFrame'] = None):
        """
        Initialize a new scope frame.
        
        Args:
            fqn: Fully Qualified Name of this scope (e.g., "module.Class.method")
            scope_type: Type of scope (MODULE, CLASS, FUNCTION)
            parent: Reference to parent scope frame (None for module scope)
        """
        self.fqn = fqn
        self.scope_type = scope_type
        self.parent = parent
        
        # Variable type mappings for this scope
        self.variables: Dict[str, str] = {}
        
        # Context metadata derived from FQN and hierarchy
        self.module_name: Optional[str] = None
        self.class_name: Optional[str] = None
        self.function_name: Optional[str] = None
        
        # Parse FQN to extract context components
        self._parse_context_from_fqn()
    
    def _parse_context_from_fqn(self):
        """Extract module, class, and function names from FQN and scope hierarchy."""
        parts = self.fqn.split('.')
        
        # Module is always the first part
        if parts:
            self.module_name = parts[0]
        
        # For class and function, we need to walk the scope hierarchy
        # to properly identify which parts are classes vs functions
        if self.scope_type == ScopeType.CLASS:
            self.class_name = self.fqn
        elif self.scope_type == ScopeType.FUNCTION:
            self.function_name = self.fqn
            # Find the nearest class scope in the hierarchy
            current = self.parent
            while current:
                if current.scope_type == ScopeType.CLASS:
                    self.class_name = current.fqn
                    break
                current = current.parent
    
    def add_variable(self, name: str, type_fqn: str):
        """Add or update a variable type in this scope."""
        self.variables[name] = type_fqn
    
    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable type from this scope (does not search parent scopes)."""
        return self.variables.get(name)
    
    def get_variable_count(self) -> int:
        """Get the number of variables in this scope."""
        return len(self.variables)
    
    def __repr__(self) -> str:
        return f"ScopeFrame({self.scope_type.value}:{self.fqn}, {len(self.variables)} vars)"


class ScopeManager:
    """
    Unified scope and context manager for Atlas analysis.
    
    This class replaces both the AnalysisVisitor.scope_stack and SymbolTableManager
    with a single, coherent system that:
    - Tracks lexical scopes using a stack of enhanced ScopeFrames
    - Provides variable type lookup with proper lexical scoping rules
    - Directly manages logger context to eliminate fragile FQN lookups
    - Offers clean interface for AnalysisVisitor integration
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        """
        Initialize the scope manager.
        
        Args:
            recon_data: Reconnaissance data for context validation
        """
        self.scope_stack: List[ScopeFrame] = []
        self.recon_data = recon_data
        self.logger = get_logger()
        
        self._log(LogLevel.DEBUG, "Enhanced scope manager initialized")
    
    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Consolidated logging with automatic source detection."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    # === Core Scope Operations ===
    
    def enter_scope(self, fqn: str, scope_type: ScopeType):
        """
        Enter a new lexical scope.
        
        Args:
            fqn: Fully qualified name of the scope
            scope_type: Type of scope being entered
        """
        parent = self.scope_stack[-1] if self.scope_stack else None
        new_frame = ScopeFrame(fqn, scope_type, parent)
        self.scope_stack.append(new_frame)
        
        self._log(LogLevel.DEBUG, f"Entered {scope_type.value} scope: {fqn}",
                  extra={"scope_depth": len(self.scope_stack), "scope_type": scope_type.value})
        
        # Update logger context immediately when scope changes
        self._update_logger_context()
    
    def exit_scope(self):
        """Exit the current lexical scope."""
        if not self.scope_stack:
            self._log(LogLevel.WARNING, "Attempted to exit scope with empty stack")
            return
        
        exited_frame = self.scope_stack.pop()
        self._log(LogLevel.DEBUG, f"Exited {exited_frame.scope_type.value} scope: {exited_frame.fqn}",
                  extra={"scope_depth": len(self.scope_stack), 
                         "variables_cleared": exited_frame.get_variable_count()})
        
        # Update logger context after scope change
        self._update_logger_context()
    
    def get_current_scope(self) -> Optional[ScopeFrame]:
        """Get the current (top) scope frame."""
        return self.scope_stack[-1] if self.scope_stack else None
    
    def get_current_scope_fqn(self) -> str:
        """Get the FQN of the current scope."""
        current = self.get_current_scope()
        return current.fqn if current else "unknown"
    
    # === Variable Type Management (SymbolTableManager Replacement Interface) ===
    
    def update_variable_type(self, var_name: str, var_type: str):
        """
        Add or update a variable type in the current scope.
        
        This method provides compatibility with the existing SymbolTableManager interface.
        """
        current_scope = self.get_current_scope()
        if not current_scope:
            self._log(LogLevel.WARNING, f"Cannot update variable '{var_name}': no active scope")
            return
        
        current_scope.add_variable(var_name, var_type)
        self._log(LogLevel.TRACE, f"Updated variable: {var_name} -> {var_type}",
                  extra={"scope": current_scope.fqn, "variable": var_name, "type": var_type})
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """
        Look up a variable type using proper lexical scoping rules.
        
        Searches from innermost to outermost scope, following Python's LEGB rule.
        This method provides compatibility with the existing SymbolTableManager interface.
        """
        # Search from innermost to outermost scope
        for i in range(len(self.scope_stack) - 1, -1, -1):
            scope_frame = self.scope_stack[i]
            var_type = scope_frame.get_variable(var_name)
            if var_type:
                self._log(LogLevel.TRACE, f"Found variable '{var_name}' -> {var_type}",
                          extra={"scope": scope_frame.fqn, "variable": var_name, "type": var_type})
                return var_type
        
        # Variable not found in any scope
        self._log(LogLevel.TRACE, f"Variable '{var_name}' not found in any scope",
                  extra={"variable": var_name, "scopes_searched": len(self.scope_stack)})
        return None
    
    # === Compatibility Methods for Current Integration ===
    
    def enter_function_scope(self):
        """
        Compatibility method for existing FunctionAnalyzer integration.
        
        Note: This is a transitional method. The proper approach is to use
        enter_scope() with the function FQN and ScopeType.FUNCTION.
        """
        self._log(LogLevel.WARNING, "Using deprecated enter_function_scope(). " +
                  "Consider using enter_scope() with ScopeType.FUNCTION instead.")
    
    def exit_function_scope(self):
        """
        Compatibility method for existing FunctionAnalyzer integration.
        
        Note: This is a transitional method. The proper approach is to use exit_scope().
        """
        self._log(LogLevel.WARNING, "Using deprecated exit_function_scope(). " +
                  "Consider using exit_scope() instead.")
        self.exit_scope()
    
    def enter_class_scope(self):
        """
        Compatibility method for existing ClassDef integration.
        
        Note: This is a transitional method. The proper approach is to use
        enter_scope() with the class FQN and ScopeType.CLASS.
        """
        self._log(LogLevel.WARNING, "Using deprecated enter_class_scope(). " +
                  "Consider using enter_scope() with ScopeType.CLASS instead.")
    
    def exit_class_scope(self):
        """
        Compatibility method for existing ClassDef integration.
        
        Note: This is a transitional method. The proper approach is to use exit_scope().
        """
        self._log(LogLevel.WARNING, "Using deprecated exit_class_scope(). " +
                  "Consider using exit_scope() instead.")
        self.exit_scope()
    
    # === Logger Context Integration ===
    
    def _update_logger_context(self):
        """
        Update logger context directly from scope state.
        
        This method replaces the fragile FQN-based lookup approach in AnalysisVisitor
        with direct access to scope frame metadata.
        """
        current_scope = self.get_current_scope()
        if not current_scope:
            # No active scope - clear all context
            self.logger.module = None
            self.logger.class_name = None
            self.logger.function = None
            return
        
        # Set context directly from scope frame metadata
        self.logger.module = current_scope.module_name
        self.logger.class_name = current_scope.class_name
        self.logger.function = current_scope.function_name
        
        self._log(LogLevel.TRACE, "Updated logger context",
                  extra={
                      "module": current_scope.module_name,
                      "class": current_scope.class_name,
                      "function": current_scope.function_name
                  })
    
    def reset_context(self):
        """
        Reset all scope context - used between module analysis.
        
        This method provides compatibility with the existing logger.reset_context() usage.
        """
        self.scope_stack.clear()
        self._update_logger_context()
        self._log(LogLevel.DEBUG, "Scope context reset")
    
    # === Context Access Methods (for AnalysisVisitor._get_context()) ===
    
    def get_current_module(self) -> Optional[str]:
        """Get current module name from scope context."""
        current_scope = self.get_current_scope()
        return current_scope.module_name if current_scope else None
    
    def get_current_class_fqn(self) -> Optional[str]:
        """Get current class FQN from scope context."""
        current_scope = self.get_current_scope()
        return current_scope.class_name if current_scope else None
    
    def get_current_function_fqn(self) -> Optional[str]:
        """Get current function FQN from scope context."""
        current_scope = self.get_current_scope()
        return current_scope.function_name if current_scope else None
    
    # === Debugging and State Inspection ===
    
    def get_scope_summary(self) -> Dict[str, Any]:
        """
        Get summary of current scope state for debugging.
        
        This method provides compatibility with SymbolTableManager.get_scope_summary().
        """
        if not self.scope_stack:
            return {"scopes": 0, "variables": 0, "current_scope": None}
        
        current_scope = self.get_current_scope()
        total_variables = sum(frame.get_variable_count() for frame in self.scope_stack)
        
        summary = {
            "scopes": len(self.scope_stack),
            "variables": total_variables,
            "current_scope": current_scope.fqn,
            "current_scope_type": current_scope.scope_type.value,
            "current_variables": current_scope.get_variable_count()
        }
        
        self._log(LogLevel.DEBUG, "Scope summary", extra=summary)
        return summary
    
    def log_scope_stack(self, context: str = "debug"):
        """Log the current scope stack for debugging."""
        if not self.scope_stack:
            self._log(LogLevel.DEBUG, f"Scope stack ({context}): empty")
            return
        
        stack_info = []
        for i, frame in enumerate(self.scope_stack):
            stack_info.append(f"  {i}: {frame}")
        
        self._log(LogLevel.DEBUG, f"Scope stack ({context}):\n" + "\n".join(stack_info),
                  extra={"context": context, "depth": len(self.scope_stack)})
