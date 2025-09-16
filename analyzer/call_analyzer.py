"""
Call Analyzer - Code Atlas

Handles the detailed analysis of `ast.Call` nodes. This module is responsible
for resolving the call's FQN, identifying its type (e.g., class instantiation,
function call), and detecting special patterns like SocketIO emits.
"""

import ast
from typing import Dict, Any, Optional, List

from .utils import EXTERNAL_LIBRARY_ALLOWLIST
from .logger import get_logger, LogLevel
from .utils import get_source


class CallAnalyzer:
    """Analyzes ast.Call nodes to resolve and categorize function calls."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor  # The main AnalysisVisitor instance
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    def analyze_call(self, node: ast.Call):
        """Process function calls with comprehensive logging - FIXED VERSION."""
        if not self.visitor.current_function_report:
            return
        
        try:
            name_parts = self.visitor.name_resolver.extract_name_parts(node.func)
            if not name_parts:
                self._log(LogLevel.TRACE, "Could not extract name parts from call")
                return
            
            raw_name = ".".join(name_parts)
            self._log(LogLevel.TRACE, f"Found call: {raw_name}")
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 'max', 'min', 'sum', 'abs', 'round', 'sorted']:
                self._log(LogLevel.TRACE, f"Ignored built-in function: {raw_name}")
                return
            
            context = self.visitor._get_context()
            
            # **FIXED: Always resolve the complete call first**
            resolved_fqn = self.visitor._cached_resolve_name(name_parts, context)
            
            """
            # **ENHANCED: Track intermediate calls in method chains**
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            """
            
            if resolved_fqn:
                self._log(LogLevel.TRACE, f"Resolved call: {raw_name} -> {resolved_fqn}")
                
                # **ENHANCED EMIT DETECTION**: Check for emit calls with comprehensive patterns
                is_emit_call = self._is_emit_call(resolved_fqn, name_parts, raw_name)
                
                if is_emit_call:
                    self._handle_emit_call(node, resolved_fqn)
                    self._log(LogLevel.INFO, f"SocketIO emit detected: {resolved_fqn}")
                # Handle instantiations
                elif resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.visitor.current_function_report["instantiations"]:
                        self.visitor.current_function_report["instantiations"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Class instantiation: {resolved_fqn}")
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.visitor.current_function_report["instantiations"]:
                        self.visitor.current_function_report["instantiations"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External class instantiation: {resolved_fqn}")
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self.visitor._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Function call: {resolved_fqn}")
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self.visitor._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External function call: {resolved_fqn}")
                # Handle external library calls from old allowlist (for backward compatibility)
                elif any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
                    self.visitor._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External library call: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Call not in catalog: {resolved_fqn}")
            else:
                self._log(LogLevel.TRACE, f"Could not resolve call: {raw_name}")
                
                # **FALLBACK EMIT DETECTION**: Check for emit patterns even when resolution fails
                if self._is_emit_call_fallback(name_parts, raw_name):
                    self._log(LogLevel.INFO, f"Unresolved SocketIO emit detected: {raw_name}")
                    self._handle_emit_call(node, raw_name)  # Use raw name if we can't resolve
            
            # Check for function arguments
            self._process_function_arguments(node)
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing call: {e}")

    def _is_emit_call(self, resolved_fqn: str, name_parts: List[str], raw_name: str) -> bool:
        """Comprehensive emit call detection with multiple patterns including external libraries."""
        
        # Pattern 1: Direct flask_socketio.emit import
        if resolved_fqn == 'flask_socketio.emit':
            return True
        
        # Pattern 2: Any method ending with .emit
        if resolved_fqn.endswith('.emit'):
            return True
        
        # Pattern 3: External SocketIO class emit method
        if 'flask_socketio.SocketIO.emit' in resolved_fqn:
            return True
        
        # Pattern 4: Contains SocketIO
        if 'SocketIO' in resolved_fqn:
            return True
        
        # Pattern 5: Contains socketio (case insensitive)
        if 'socketio' in resolved_fqn.lower():
            return True
        
        # Pattern 6: Check if resolved to external emit function
        if resolved_fqn in self.recon_data.get("external_functions", {}):
            ext_func_info = self.recon_data["external_functions"][resolved_fqn]
            if ext_func_info["name"] == "emit" and "socketio" in ext_func_info["module"]:
                return True
        
        # Pattern 7: Check if any part of the name is 'emit'
        if 'emit' in name_parts:
            return True
        
        # Pattern 8: Check raw name patterns
        if '.emit(' in raw_name or raw_name.endswith('.emit'):
            return True
        
        return False
    
    def _is_emit_call_fallback(self, name_parts: List[str], raw_name: str) -> bool:
        """Fallback emit detection for unresolved calls."""
        
        # Check if 'emit' is the last part of the call
        if name_parts and name_parts[-1] == 'emit':
            return True
        
        # Check for common SocketIO patterns in the raw name
        if any(pattern in raw_name.lower() for pattern in ['socketio.emit', '.emit']):
            return True
        
        return False
    
    def _track_intermediate_chain_calls(self, name_parts: List[str], context: Dict[str, Any], final_resolved_fqn: str):
        """Track intermediate method calls in complex chains - FIXED VERSION."""
        self._log(LogLevel.TRACE, f"Tracking intermediate chain calls for: {'.'.join(name_parts)}")
        
        # Only track intermediate calls if we have a multi-part chain
        if len(name_parts) <= 1:
            return
        
        # Track each progressive step in the chain (excluding the final call which is handled separately)
        for i in range(1, len(name_parts)):  # Skip the final step since it's handled by main resolution
            partial_chain = name_parts[:i+1]
            partial_name = ".".join(partial_chain)
            
            # Skip if this is the same as the final resolved call
            if partial_name == ".".join(name_parts):
                continue
            
            # Try to resolve this partial chain
            partial_resolved = self.visitor._cached_resolve_name(partial_chain, context)
            
            if partial_resolved and partial_resolved != final_resolved_fqn:
                self._log(LogLevel.TRACE, f"Intermediate chain step {i}: {partial_name} -> {partial_resolved}")
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.visitor.current_function_report["calls"]:
                        self.visitor._add_unique_call(partial_resolved)
                        self._log(LogLevel.DEBUG, f"Intermediate call added: {partial_resolved}")
                
                # Update context for next step using return type if available
                if i < len(name_parts) - 1:  # Don't update for the last step
                    self._update_chain_context(partial_resolved, name_parts[0], context)
    
    def _update_chain_context(self, resolved_fqn: str, base_name: str, context: Dict[str, Any]):
        """Update resolution context based on intermediate call return type."""
        if resolved_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][resolved_fqn]
            return_type = func_info.get("return_type")
            if return_type:
                # Extract core type and try to resolve it to FQN
                core_type = self.visitor.type_inference.extract_core_type(return_type)
                if core_type:
                    resolved_type_fqn = self.visitor.type_inference._resolve_return_type_to_fqn(core_type, context)
                    if resolved_type_fqn:
                        # CHANGE: Update scope manager instead of symbol manager
                        self.visitor.scope_manager.update_variable_type(base_name, resolved_type_fqn)
                        self._log(LogLevel.TRACE, f"Updated chain context: {base_name} -> {resolved_type_fqn}")

    def _handle_emit_call(self, node: ast.Call, resolved_fqn: str):
        """Handle special emit methods for event name extraction."""
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
        
        # Check for room parameter
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
        """Process function arguments for function references."""
        context = self.visitor._get_context()
        
        for arg in node.args:
            if isinstance(arg, ast.Name):
                arg_fqn = self.visitor.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                               arg_fqn in self.recon_data.get("external_functions", {}))):
                    self.visitor._add_unique_call(arg_fqn)
                    self._log(LogLevel.TRACE, f"Function argument reference: {arg_fqn}")
