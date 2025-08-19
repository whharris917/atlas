"""
Centralized Logger - Code Atlas

Unified logging functionality to eliminate code duplication across modules.
"""

from typing import Optional


class AnalysisLogger:
    """Centralized logger for Atlas analysis operations."""
    
    def __init__(self, log_level: int = 3):
        self.log_level = log_level
    
    def log(self, message: str, indent: int = 0, level: int = 1, context: str = "") -> None:
        """Output formatted log messages with level control."""
        if level <= self.log_level:
            prefix = f"[{context}] " if context else ""
            print("  " * indent + prefix + message)
    
    def set_level(self, level: int) -> None:
        """Set logging level: 0=minimal, 1=normal, 2=verbose, 3=debug"""
        self.log_level = level
        self.log(f"Log level set to {level}")
    
    def log_symbol_table_state(self, symbol_manager, context: str, indent: int = 3) -> None:
        """Log current symbol table state for debugging."""
        if hasattr(symbol_manager, 'log_symbol_table_state'):
            symbol_manager.log_symbol_table_state(context, indent)
    
    def log_function_analysis_start(self, function_fqn: str, indent: int = 2) -> None:
        """Log start of function analysis."""
        self.log(f"[FUNCTION_ANALYSIS] Starting analysis of: {function_fqn}", indent)
    
    def log_function_analysis_complete(self, function_fqn: str, function_report: dict, indent: int = 2) -> None:
        """Log completion of function analysis with statistics."""
        self.log(f"[FUNCTION_ANALYSIS] Completed analysis of: {function_fqn}", indent)
        self.log(f"  Calls: {len(function_report['calls'])}", indent + 1)
        self.log(f"  Instantiations: {len(function_report['instantiations'])}", indent + 1)
        self.log(f"  State Access: {len(function_report['accessed_state'])}", indent + 1)
        emit_count = len(function_report.get("emit_contexts", {}))
        if emit_count > 0:
            self.log(f"  SocketIO Emits: {emit_count}", indent + 1)
    
    def log_resolution_attempt(self, name_parts: list, indent: int = 2) -> None:
        """Log name resolution attempts."""
        if self.log_level >= 2:
            self.log(f"[RESOLVE] Attempting to resolve: {name_parts}", indent)
    
    def log_resolution_result(self, name_parts: list, result: Optional[str], indent: int = 1) -> None:
        """Log name resolution results."""
        if result:
            if self.log_level >= 1:
                self.log(f"[RESOLVE] RESOLVED to: {result}", indent)
        else:
            if self.log_level >= 1:
                name_str = '.'.join(name_parts) if isinstance(name_parts, list) else str(name_parts)
                self.log(f"[RESOLVE] FAILED to resolve: {name_str}", indent)
    
    def log_cache_hit(self, name_parts: list, result: str, indent: int = 4) -> None:
        """Log cache hits for resolution."""
        if self.log_level >= 2:
            name_str = '.'.join(name_parts) if isinstance(name_parts, list) else str(name_parts)
            self.log(f"[CACHE] {name_str} -> {result} (cached)", indent)


# Global logger instance
_global_logger: Optional[AnalysisLogger] = None


def get_logger() -> AnalysisLogger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AnalysisLogger()
    return _global_logger


def set_global_log_level(level: int) -> None:
    """Set the global logging level."""
    logger = get_logger()
    logger.set_level(level)
