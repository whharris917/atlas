"""
Symbol Table Manager - Code Atlas

Manages symbol tables for tracking variable types in different scopes
(class, function, nested functions).
"""
from typing import Optional, Dict, Any

from .logger import get_logger, LogLevel
from .utils import get_source


class SymbolTableManager:
    """Manages symbol tables for tracking variable types in different scopes."""
    
    def __init__(self):
        self.function_symbols = {}
        self.class_symbols = {}
        
        self._log(LogLevel.DEBUG, "Symbol table manager initialized")
    
    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Consolidated logging with automatic source detection and context."""
    
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    def log_symbol_table_state(self, context_description: str):
        """Log current symbol table state for debugging."""
        self._log(LogLevel.TRACE, f"Symbol table state: {context_description}",
            extra={
                "function_symbols": dict(self.function_symbols),
                "function_symbol_count": len(self.function_symbols),
            }
        )
    
    def enter_function_scope(self):
        """Enter new function scope."""
        self.function_symbols = {}
        self._log(LogLevel.DEBUG, "Entered function scope")
    
    def exit_function_scope(self):
        """Exit function scope."""
        function_count = len(self.function_symbols)
        self.function_symbols = {}
        self._log(LogLevel.DEBUG, f"Exited function scope ({function_count} symbols cleared)", extra={"cleared_symbols": function_count})

    def enter_class_scope(self):
        """Enter class scope."""
        self.class_symbols = {}
        self._log(LogLevel.DEBUG, "Entered class scope")
    
    def exit_class_scope(self):
        """Exit class scope."""
        class_count = len(self.class_symbols)
        self.class_symbols = {}
        self._log(LogLevel.DEBUG, f"Exited class scope ({class_count} symbols cleared)", extra={"cleared_symbols": class_count})
    
    def update_variable_type(self, var_name: str, var_type: str):
        """Update variable type in current scope."""
        self.function_symbols[var_name] = var_type
        self._log(LogLevel.TRACE, f"Updated function symbol: {var_name} -> {var_type}", 
            extra={
                "scope": "function",
                "variable": var_name, 
                "type": var_type
            }
        )
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get variable type from current scope."""
        if var_name in self.function_symbols:
            var_type = self.function_symbols[var_name]
            self._log(LogLevel.TRACE, f"Found variable in function scope: {var_name} -> {var_type}", 
                extra={
                    "scope": "function",
                    "variable": var_name, 
                    "type": var_type
                }
            )
            return var_type
        
        # Variable not found in any scope
        self._log(LogLevel.TRACE, f"Variable not found in any scope: {var_name}", 
            extra={
                "variable": var_name,
                "function_symbols_count": len(self.function_symbols),
            }
        )
        return None
    
    def get_scope_summary(self) -> dict:
        """Get summary of current symbol table state."""
        summary = {
            'function_symbols': len(self.function_symbols),
            'class_symbols': len(self.class_symbols),
            'total_symbols': len(self.function_symbols) + len(self.class_symbols)
        }
        
        self._log(LogLevel.DEBUG, "Symbol table summary", extra=summary)
        
        return summary
