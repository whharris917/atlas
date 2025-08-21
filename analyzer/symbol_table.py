"""
Symbol Table Manager - Code Atlas

Manages symbol tables for tracking variable types in different scopes
(class, function, nested functions).
"""
from typing import Optional

from .logger import get_logger, create_context, AnalysisPhase, log_debug, log_trace


class SymbolTableManager:
    """Manages symbol tables for tracking variable types in different scopes."""
    
    def __init__(self):
        self.function_symbols = {}
        self.nested_symbols = {}
        self.class_symbols = {}
        self.is_in_nested = False
    
    def log_symbol_table_state(self, context_desc: str, indent: int = 3):
        """Log current symbol table state for debugging."""
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "log_state")
        
        log_debug(f"Symbol Table State: {context_desc}", log_context)
        log_debug(f"Function symbols: {self.function_symbols}", log_context.with_indent(1))
        log_debug(f"Nested symbols: {self.nested_symbols}", log_context.with_indent(1))
        log_debug(f"Is in nested: {self.is_in_nested}", log_context.with_indent(1))
    
    def enter_function_scope(self):
        """Enter new function scope."""
        self.function_symbols = {}
        self.nested_symbols = {}
        self.is_in_nested = False
        
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "enter_function_scope")
        log_debug("Entered function scope", log_context)
    
    def enter_nested_scope(self):
        """Enter nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = True
        
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "enter_nested_scope")
        log_debug("Entered nested scope", log_context)
    
    def exit_nested_scope(self):
        """Exit nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = False
        
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "exit_nested_scope")
        log_debug("Exited nested scope", log_context)
    
    def enter_class_scope(self):
        """Enter class scope."""
        self.class_symbols = {}
        
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "enter_class_scope")
        log_debug("Entered class scope", log_context)
    
    def exit_class_scope(self):
        """Exit class scope."""
        self.class_symbols = {}
        
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "exit_class_scope")
        log_debug("Exited class scope", log_context)
    
    def update_variable_type(self, var_name: str, var_type: str):
        """Update variable type in current scope."""
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "update_variable_type")
        
        if self.is_in_nested:
            self.nested_symbols[var_name] = var_type
            log_debug(f"Nested scope update: {var_name} -> {var_type}", log_context)
        else:
            self.function_symbols[var_name] = var_type
            log_debug(f"Function scope update: {var_name} -> {var_type}", log_context)
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get variable type from current scope."""
        log_context = create_context("symbol_table", AnalysisPhase.ANALYSIS, "get_variable_type")
        
        if self.is_in_nested and var_name in self.nested_symbols:
            var_type = self.nested_symbols[var_name]
            log_debug(f"Found {var_name} in nested scope: {var_type}", log_context)
            return var_type
        
        if var_name in self.function_symbols:
            var_type = self.function_symbols[var_name]
            log_debug(f"Found {var_name} in function scope: {var_type}", log_context)
            return var_type
        
        log_debug(f"Variable {var_name} not found in any scope", log_context)
        return None
