"""
Symbol Table Manager - Code Atlas

Manages symbol tables for tracking variable types in different scopes
(class, function, nested functions).
"""
import inspect
from typing import Optional

from .logger import get_logger, LogContext, AnalysisPhase, LogLevel


class SymbolTableManager:
    """Manages symbol tables for tracking variable types in different scopes."""
    
    def __init__(self):
        self.function_symbols = {}
        self.nested_symbols = {}
        self.class_symbols = {}
        self.is_in_nested = False
        
        self._log(LogLevel.DEBUG, "Symbol table manager initialized")
    
    def _log(self, level: LogLevel, message: str, **extra):
        """Consolidated logging with automatic source detection and context."""
        try:
            source_frame = inspect.currentframe().f_back
            source_function = f"{self.__class__.__name__}.{source_frame.f_code.co_name}"
        except Exception:
            source_function = f"{self.__class__.__name__}.unknown"
        
        context = LogContext(
            module="symbol_table",
            phase=AnalysisPhase.ANALYSIS,
            source=source_function,
            extra=extra
        )
        
        getattr(get_logger(__name__), level.name.lower())(message, context=context)
    
    def log_symbol_table_state(self, context_description: str):
        """Log current symbol table state for debugging."""
        self._log(LogLevel.TRACE, f"Symbol table state: {context_description}",
                 function_symbols=dict(self.function_symbols),
                 nested_symbols=dict(self.nested_symbols),
                 is_in_nested=self.is_in_nested,
                 function_symbol_count=len(self.function_symbols),
                 nested_symbol_count=len(self.nested_symbols))
    
    def enter_function_scope(self):
        """Enter new function scope."""
        self.function_symbols = {}
        self.nested_symbols = {}
        self.is_in_nested = False
        
        self._log(LogLevel.DEBUG, "Entered function scope")
    
    def enter_nested_scope(self):
        """Enter nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = True
        
        self._log(LogLevel.DEBUG, "Entered nested function scope")
    
    def exit_nested_scope(self):
        """Exit nested function scope."""
        nested_count = len(self.nested_symbols)
        self.nested_symbols = {}
        self.is_in_nested = False
        
        self._log(LogLevel.DEBUG, f"Exited nested scope ({nested_count} symbols cleared)", cleared_symbols=nested_count)
    
    def enter_class_scope(self):
        """Enter class scope."""
        self.class_symbols = {}
        
        self._log(LogLevel.DEBUG, "Entered class scope")
    
    def exit_class_scope(self):
        """Exit class scope."""
        class_count = len(self.class_symbols)
        self.class_symbols = {}
        
        self._log(LogLevel.DEBUG, f"Exited class scope ({class_count} symbols cleared)", cleared_symbols=class_count)
    
    def update_variable_type(self, var_name: str, var_type: str):
        """Update variable type in current scope."""
        if self.is_in_nested:
            self.nested_symbols[var_name] = var_type
            self._log(LogLevel.TRACE, f"Updated nested symbol: {var_name} -> {var_type}", 
                     scope='nested', variable=var_name, type=var_type)
        else:
            self.function_symbols[var_name] = var_type
            self._log(LogLevel.TRACE, f"Updated function symbol: {var_name} -> {var_type}", 
                     scope='function', variable=var_name, type=var_type)
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get variable type from current scope."""
        # Check nested scope first if we're in nested context
        if self.is_in_nested and var_name in self.nested_symbols:
            var_type = self.nested_symbols[var_name]
            self._log(LogLevel.TRACE, f"Found variable in nested scope: {var_name} -> {var_type}", 
                     scope='nested', variable=var_name, type=var_type)
            return var_type
        
        # Check function scope
        if var_name in self.function_symbols:
            var_type = self.function_symbols[var_name]
            self._log(LogLevel.TRACE, f"Found variable in function scope: {var_name} -> {var_type}", 
                     scope='function', variable=var_name, type=var_type)
            return var_type
        
        # Variable not found in any scope
        self._log(LogLevel.TRACE, f"Variable not found in any scope: {var_name}", 
                 variable=var_name,
                 nested_scope_active=self.is_in_nested,
                 function_symbols_count=len(self.function_symbols),
                 nested_symbols_count=len(self.nested_symbols))
        return None
    
    def get_scope_summary(self) -> dict:
        """Get summary of current symbol table state."""
        summary = {
            'function_symbols': len(self.function_symbols),
            'nested_symbols': len(self.nested_symbols),
            'class_symbols': len(self.class_symbols),
            'is_in_nested': self.is_in_nested,
            'total_symbols': len(self.function_symbols) + len(self.nested_symbols) + len(self.class_symbols)
        }
        
        self._log(LogLevel.DEBUG, "Symbol table summary", **summary)
        
        return summary
