"""
Symbol Table Manager - Code Atlas

Manages symbol tables for tracking variable types in different scopes
(class, function, nested functions).
"""
from typing import Optional

from .logger import get_logger, LogContext, AnalysisPhase

logger = get_logger(__name__)


class SymbolTableManager:
    """Manages symbol tables for tracking variable types in different scopes."""
    
    def __init__(self):
        self.function_symbols = {}
        self.nested_symbols = {}
        self.class_symbols = {}
        self.is_in_nested = False
        
        logger.debug("Symbol table manager initialized",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    def log_symbol_table_state(self, context_description: str):
        """Log current symbol table state for debugging."""
        logger.trace(f"Symbol table state: {context_description}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={
                                         'function_symbols': dict(self.function_symbols),
                                         'nested_symbols': dict(self.nested_symbols),
                                         'is_in_nested': self.is_in_nested,
                                         'function_symbol_count': len(self.function_symbols),
                                         'nested_symbol_count': len(self.nested_symbols)
                                     }))
    
    def enter_function_scope(self):
        """Enter new function scope."""
        self.function_symbols = {}
        self.nested_symbols = {}
        self.is_in_nested = False
        
        logger.debug("Entered function scope",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    def enter_nested_scope(self):
        """Enter nested function scope."""
        self.nested_symbols = {}
        self.is_in_nested = True
        
        logger.debug("Entered nested function scope",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    def exit_nested_scope(self):
        """Exit nested function scope."""
        nested_count = len(self.nested_symbols)
        self.nested_symbols = {}
        self.is_in_nested = False
        
        logger.debug(f"Exited nested scope ({nested_count} symbols cleared)",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'cleared_symbols': nested_count}))
    
    def enter_class_scope(self):
        """Enter class scope."""
        self.class_symbols = {}
        
        logger.debug("Entered class scope",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    def exit_class_scope(self):
        """Exit class scope."""
        class_count = len(self.class_symbols)
        self.class_symbols = {}
        
        logger.debug(f"Exited class scope ({class_count} symbols cleared)",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'cleared_symbols': class_count}))
    
    def update_variable_type(self, var_name: str, var_type: str):
        """Update variable type in current scope."""
        if self.is_in_nested:
            self.nested_symbols[var_name] = var_type
            logger.trace(f"Updated nested symbol: {var_name} -> {var_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'scope': 'nested', 'variable': var_name, 'type': var_type}))
        else:
            self.function_symbols[var_name] = var_type
            logger.trace(f"Updated function symbol: {var_name} -> {var_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'scope': 'function', 'variable': var_name, 'type': var_type}))
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """Get variable type from current scope."""
        # Check nested scope first if we're in nested context
        if self.is_in_nested and var_name in self.nested_symbols:
            var_type = self.nested_symbols[var_name]
            logger.trace(f"Found variable in nested scope: {var_name} -> {var_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'scope': 'nested', 'variable': var_name, 'type': var_type}))
            return var_type
        
        # Check function scope
        if var_name in self.function_symbols:
            var_type = self.function_symbols[var_name]
            logger.trace(f"Found variable in function scope: {var_name} -> {var_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'scope': 'function', 'variable': var_name, 'type': var_type}))
            return var_type
        
        # Variable not found in any scope
        logger.trace(f"Variable not found in any scope: {var_name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'variable': var_name,
                                            'nested_scope_active': self.is_in_nested,
                                            'function_symbols_count': len(self.function_symbols),
                                            'nested_symbols_count': len(self.nested_symbols)}))
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
        
        logger.debug("Symbol table summary",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS, extra=summary))
        
        return summary
