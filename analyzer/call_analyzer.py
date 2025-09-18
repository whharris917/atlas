"""
Call Analyzer - Code Atlas (Enhanced with ExpressionTraversal)

Handles the detailed analysis of `ast.Call` nodes using the unified ExpressionTraversal engine.
This replaces the fragmented name resolution approach with the modern Expression Traversal system.

REFACTORED: Uses ExpressionTraversal.resolve_and_evaluate() to eliminate redundant resolution logic.
"""

import ast
from typing import Dict, Any, Optional, List

from .utils import EXTERNAL_LIBRARY_ALLOWLIST
from .logger import get_logger, LogLevel
from .utils import get_source
from .expression_traversal import ExpressionTraversal


class CallAnalyzer:
    """Analyzes ast.Call nodes using unified ExpressionTraversal engine."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor  # The main AnalysisVisitor instance
        self.logger = get_logger()
        
        # Initialize ExpressionTraversal engine with all required parameters
        self.expression_traversal = ExpressionTraversal(
            recon_data=recon_data,
            scope_manager=visitor.scope_manager, 
            module_fqn=visitor.module_name  # AnalysisVisitor stores module name
        )
        
        self._log(LogLevel.DEBUG, "CallAnalyzer initialized with ExpressionTraversal engine")

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    def analyze_call(self, node: ast.Call):
        """
        Process function calls using unified ExpressionTraversal engine.
        
        This replaces the legacy name resolution approach with the modern
        Expression Traversal system that provides proper Type Propagation
        and unified expression analysis.
        """
        if not self.visitor.current_function_report:
            return
        
        try:
            # **NEW APPROACH: Use ExpressionTraversal for unified analysis**
            identity_fqn, resulting_type = self.expression_traversal.resolve_and_evaluate(node.func)
            
            if identity_fqn:
                self._log(LogLevel.DEBUG, f"ExpressionTraversal resolved call: {ast.unparse(node.func)} -> {identity_fqn}")
                
                # Check for built-in functions that should be ignored
                if self._is_builtin_function(identity_fqn):
                    self._log(LogLevel.TRACE, f"Ignored built-in function: {identity_fqn}")
                    return
                
                # Handle different types of calls based on resolved FQN
                self._process_resolved_call(node, identity_fqn, resulting_type)
                
            else:
                # **FALLBACK: Handle unresolved calls with pattern detection**
                self._log(LogLevel.TRACE, f"ExpressionTraversal could not resolve: {ast.unparse(node.func)}")
                self._handle_unresolved_call(node)
            
            # Process function arguments for additional analysis
            self._process_function_arguments(node)
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error in ExpressionTraversal call analysis: {e}")
            # Graceful fallback - continue without crashing
            
    def _is_builtin_function(self, resolved_fqn: str) -> bool:
        """Check if the resolved FQN represents a built-in function."""
        builtin_functions = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 
            'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 
            'max', 'min', 'sum', 'abs', 'round', 'sorted'
        }
        
        # Check if it's a simple built-in (e.g., "print")
        if resolved_fqn in builtin_functions:
            return True
            
        # Check if it's a module-qualified built-in (e.g., "builtins.print")
        if '.' in resolved_fqn:
            name_part = resolved_fqn.split('.')[-1]
            return name_part in builtin_functions
            
        return False
    
    def _process_resolved_call(self, node: ast.Call, identity_fqn: str, resulting_type: Optional[str]):
        """
        Process a successfully resolved call based on its type.
        
        Args:
            node: The ast.Call node
            identity_fqn: The resolved FQN of the called entity
            resulting_type: The type that results from calling this entity
        """
        
        # **ENHANCED EMIT DETECTION**: Check for SocketIO emit patterns
        if self._is_emit_call(identity_fqn):
            self._handle_emit_call(node, identity_fqn)
            self._log(LogLevel.INFO, f"SocketIO emit detected: {identity_fqn}")
            return
        
        # **CATEGORIZE BY ENTITY TYPE**: Use reconnaissance data to determine call type
        
        # Handle class instantiations (internal)
        if identity_fqn in self.recon_data.get("classes", {}):
            if identity_fqn not in self.visitor.current_function_report["instantiations"]:
                self.visitor.current_function_report["instantiations"].append(identity_fqn)
            self._log(LogLevel.DEBUG, f"Class instantiation: {identity_fqn}")
            
        # Handle external class instantiations
        elif identity_fqn in self.recon_data.get("external_classes", {}):
            if identity_fqn not in self.visitor.current_function_report["instantiations"]:
                self.visitor.current_function_report["instantiations"].append(identity_fqn)
            self._log(LogLevel.DEBUG, f"External class instantiation: {identity_fqn}")
            
        # Handle function calls (internal)
        elif identity_fqn in self.recon_data.get("functions", {}):
            self.visitor._add_unique_call(identity_fqn)
            self._log(LogLevel.DEBUG, f"Function call: {identity_fqn}")
            
        # Handle external function calls
        elif identity_fqn in self.recon_data.get("external_functions", {}):
            self.visitor._add_unique_call(identity_fqn)
            self._log(LogLevel.DEBUG, f"External function call: {identity_fqn}")
            
        # Handle external library calls (backward compatibility)
        elif any(identity_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
            self.visitor._add_unique_call(identity_fqn)
            self._log(LogLevel.DEBUG, f"External library call: {identity_fqn}")
            
        else:
            self._log(LogLevel.TRACE, f"Call not in catalog: {identity_fqn}")
    
    def _handle_unresolved_call(self, node: ast.Call):
        """
        Handle calls that couldn't be resolved by ExpressionTraversal.
        
        This provides fallback detection for special patterns like SocketIO emits
        that might not be in reconnaissance data.
        """
        try:
            # Extract raw name for pattern matching
            raw_name = ast.unparse(node.func)
            
            # **FALLBACK EMIT DETECTION**: Check for emit patterns even when resolution fails
            if self._is_emit_call_fallback(raw_name):
                self._log(LogLevel.INFO, f"Unresolved SocketIO emit detected: {raw_name}")
                self._handle_emit_call(node, raw_name)  # Use raw name if we can't resolve
                
        except Exception as e:
            self._log(LogLevel.TRACE, f"Error in unresolved call handling: {e}")
    
    def _is_emit_call(self, resolved_fqn: str) -> bool:
        """
        Comprehensive emit call detection for resolved FQNs.
        
        Detects various SocketIO emit patterns including Flask-SocketIO and
        standard SocketIO patterns.
        """
        emit_patterns = [
            '.emit',           # Standard SocketIO emit
            'socketio.emit',   # Flask-SocketIO emit  
            'flask_socketio.emit',  # Direct import emit
            '.send',           # SocketIO send (alias for emit)
        ]
        
        return any(pattern in resolved_fqn for pattern in emit_patterns)
    
    def _is_emit_call_fallback(self, raw_name: str) -> bool:
        """
        Fallback emit detection for unresolved calls.
        
        Uses string patterns to detect emit calls that couldn't be resolved.
        """
        emit_patterns = [
            'emit(',
            '.emit(',
            'socketio.emit(',
            'send(',
            '.send(',
        ]
        
        return any(pattern in raw_name for pattern in emit_patterns)
    
    def _handle_emit_call(self, node: ast.Call, resolved_fqn: str):
        """
        Handle special SocketIO emit methods for event name extraction.
        
        Extracts event names, room parameters, and other emit context for
        SocketIO analysis.
        """
        self._log(LogLevel.DEBUG, f"Processing SocketIO emit call: {resolved_fqn}")
        
        # Extract event name from first argument
        event_name = None
        if node.args and len(node.args) > 0:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                event_name = first_arg.value
            elif isinstance(first_arg, ast.Name):
                # Variable reference - try to resolve if it's a string constant
                event_name = f"${first_arg.id}"  # Mark as variable reference
        
        # Create special emit entry
        emit_target = f"{resolved_fqn}::{event_name or 'unknown_event'}"
        self.visitor._add_unique_call(emit_target)
        
        # Extract additional emit parameters for context
        emit_context = {}
        
        # Check for room parameter and other SocketIO-specific keywords
        for keyword in node.keywords:
            if keyword.arg == 'room':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['room'] = keyword.value.value
                elif isinstance(keyword.value, ast.Name):
                    emit_context['room'] = f"${keyword.value.id}"
            elif keyword.arg == 'broadcast':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['broadcast'] = keyword.value.value
        
        # Store emit context if we have any
        if emit_context:
            context_key = f"{emit_target}_context"
            if "emit_contexts" not in self.visitor.current_function_report:
                self.visitor.current_function_report["emit_contexts"] = {}
            self.visitor.current_function_report["emit_contexts"][context_key] = emit_context
        
        self._log(LogLevel.TRACE, f"Emit details - Event: {event_name}, Context: {emit_context}")
    
    def _process_function_arguments(self, node: ast.Call):
        """
        Process function arguments to detect function references being passed as arguments.
        
        This catches cases where functions are passed as callbacks or event handlers.
        """
        for arg in node.args:
            if isinstance(arg, ast.Name):
                # **NEW: Use ExpressionTraversal for argument resolution**
                try:
                    arg_identity, _ = self.expression_traversal.resolve_and_evaluate(arg)
                    if (arg_identity and 
                        (arg_identity in self.recon_data.get("functions", {}) or
                         arg_identity in self.recon_data.get("external_functions", {}))):
                        self.visitor._add_unique_call(arg_identity)
                        self._log(LogLevel.TRACE, f"Function argument reference: {arg_identity}")
                except Exception as e:
                    self._log(LogLevel.TRACE, f"Error resolving function argument: {e}")