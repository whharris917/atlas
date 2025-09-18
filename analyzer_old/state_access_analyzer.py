"""
State Access Analyzer - Code Atlas

Handles the analysis of `ast.Name` and `ast.Attribute` nodes to detect
access to module-level state variables.
"""

import ast
from typing import Dict, Any, Optional

from .logger import get_logger, LogLevel
from .utils import get_source


class StateAccessAnalyzer:
    """Analyzes Name and Attribute nodes to detect state access."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor  # The main AnalysisVisitor instance
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)

    def analyze_name_access(self, node: ast.Name):
        """Process name references for state access."""
        if not self.visitor.current_function_report:
            return
        
        try:
            context = self.visitor._get_context()
            resolved_fqn = self.visitor._cached_resolve_name([node.id], context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                # Shadow check
                if not self.visitor.symbol_manager.get_variable_type(node.id):
                    if resolved_fqn not in self.visitor.current_function_report["accessed_state"]:
                        self.visitor.current_function_report["accessed_state"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"State access: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Name {node.id} shadowed by local variable")
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing name reference {node.id}: {e}")

    def analyze_attribute_access(self, node: ast.Attribute):
        """Process attribute access for state variables."""
        if not self.visitor.current_function_report:
            return
        
        try:
            name_parts = self.visitor.name_resolver.extract_name_parts(node)
            if not name_parts:
                return
            
            full_name = ".".join(name_parts)
            context = self.visitor._get_context()
            resolved_fqn = self.visitor._cached_resolve_name(name_parts, context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                # Shadow check on base
                base_name = name_parts[0]
                if not self.visitor.symbol_manager.get_variable_type(base_name):
                    if resolved_fqn not in self.visitor.current_function_report["accessed_state"]:
                        self.visitor.current_function_report["accessed_state"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Attribute state access: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Attribute base {base_name} shadowed by local variable")
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing attribute access: {e}")
