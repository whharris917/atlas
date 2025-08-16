"""
Symbol Table Manager - Code Atlas

Manages symbol tables for tracking variable types in different scopes
(class, function, nested functions).
"""
from typing import Optional
from .utils import LOG_LEVEL


class SymbolTableManager:
    """Manages symbol tables for tracking variable types in different scopes."""
    
    def __init__(self):
        self.function_symbols = {}
        self.nested_symbols = {}
        self.class_symbols = {}
        self.is_in_nested = False
    
    def log_symbol_table_state(self, context: str, indent: int = 3):
        """Log current symbol table state for debugging."""
        print("  " * indent + f"[SYMBOL_TABLE] {context}")
        print("  " * (indent + 1) + f"Function symbols: {self.function_symbols}")
        print("  " * (indent + 1) + f"Nested symbols: {self.nested_symbols}")
        print("  " * (indent + 1) + f"Is in nested: {self.is_in_nested}")
    
    def enter_function_scope(self):
        """Enter new function scope."""
        self.function_symbols = {}
        self.nested_symbols = {}
        self.is_in_nested = False
        if LOG_LEVEL >= 2:
            print("    [SYMBOL_TABLE] Entered function scope")
    
    def enter_nested_scope(self):
        """Enter nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = True
        if LOG_LEVEL >= 2:
            print("      [SYMBOL_TABLE] Entered nested scope")
    
    def exit_nested_scope(self):
        """Exit nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = False
        if LOG_LEVEL >= 2:
            print("      [SYMBOL_TABLE] Exited nested scope")
    
    def enter_class_scope(self):
        """Enter class scope."""
        self.class_symbols = {}
        if LOG_LEVEL >= 2:
            print("    [SYMBOL_TABLE] Entered class scope")
    
    def exit_class_scope(self):
        """Exit class scope."""
        self.class_symbols = {}
        if LOG_LEVEL >= 2:
            print("    [SYMBOL_TABLE] Exited class scope")
    
    def update_variable_type(self, var_name: str, var_type: str):
        """Update variable type in current scope."""
        if self.is_in_nested:
            self.nested_symbols[var_name] = var_type
            if LOG_LEVEL >= 2:
                print(f"      [SYMBOL_UPDATE] Nested: {var_name} -> {var_type}")
        else:
            self.function_symbols[var_name] = var_type
            if LOG_LEVEL >= 2:
                print(f"      [SYMBOL_UPDATE] Function: {var_name} -> {var_type}")
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get variable type from current scope."""
        if self.is_in_nested and var_name in self.nested_symbols:
            var_type = self.nested_symbols[var_name]
            if LOG_LEVEL >= 2:
                print(f"      [SYMBOL_LOOKUP] Found {var_name} in nested scope: {var_type}")
            return var_type
        if var_name in self.function_symbols:
            var_type = self.function_symbols[var_name]
            if LOG_LEVEL >= 2:
                print(f"      [SYMBOL_LOOKUP] Found {var_name} in function scope: {var_type}")
            return var_type
        
        if LOG_LEVEL >= 2:
            print(f"      [SYMBOL_LOOKUP] Variable {var_name} not found in any scope")
        return None
