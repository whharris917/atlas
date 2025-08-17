"""
Call Visitor - Code Atlas

Specialized visitor for method call analysis including intermediate
chain tracking and function argument processing.
"""

import ast
from typing import Dict, List, Any, Optional


class CallVisitor:
    """Specialized visitor for method call analysis."""
    
    def __init__(self, name_resolver, recon_data, current_function_report, 
                 resolution_cache, emit_visitor, logger):
        self.name_resolver = name_resolver
        self.recon_data = recon_data
        self.current_function_report = current_function_report
        self.resolution_cache = resolution_cache
        self.emit_visitor = emit_visitor
        self.logger = logger
        
        # Built-in functions to ignore
        self.builtin_functions = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 
            'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 
            'max', 'min', 'sum', 'abs', 'round', 'sorted'
        }
    
    def process_call(self, node: ast.Call, context: Dict[str, Any]) -> None:
        """Process function calls with comprehensive SocketIO emit detection."""
        try:
            name_parts = self.name_resolver.extract_name_parts(node.func)
            if not name_parts:
                self.logger.log(f"[CALL] Could not extract name parts from call", 3)
                return
            
            raw_name = ".".join(name_parts)
            self.logger.log(f"[CALL] Found call: {raw_name}", 3)
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in self.builtin_functions:
                self.logger.log(f"-> IGNORED (built-in function)", 3)
                return
            
            # Always resolve the complete call first
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            # Track intermediate calls in method chains
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            
            # **ENHANCED EMIT DETECTION**
            if self.emit_visitor.is_emit_call_enhanced(resolved_fqn or "", name_parts, raw_name, node):
                # Extract event name using enhanced methods
                event_name = self.emit_visitor.extract_dynamic_event_name(node)
                
                # Create emit entry with resolved or raw name
                emit_target_base = resolved_fqn if resolved_fqn else raw_name
                emit_target = f"{emit_target_base}::{event_name}"
                
                self._add_unique_call(emit_target)
                self.logger.log(f"-> DETECTED and ADDED emit call: {emit_target}", 3)
                
                # Extract enhanced emit context
                self.emit_visitor.extract_enhanced_emit_context(node, emit_target, event_name)
                
            elif resolved_fqn:
                self.logger.log(f"-> Resolved to: {resolved_fqn}", 3)
                
                # Handle instantiations
                if resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.logger.log(f"-> ADDED to instantiations", 3)
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.logger.log(f"-> ADDED to instantiations (external)", 3)
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self._add_unique_call(resolved_fqn)
                    self.logger.log(f"-> ADDED to calls", 3)
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self._add_unique_call(resolved_fqn)
                    self.logger.log(f"-> ADDED to calls (external)", 3)
                # Handle external library calls
                elif self._is_external_library_call(resolved_fqn):
                    self._add_unique_call(resolved_fqn)
                    self.logger.log(f"-> ADDED to calls (external library)", 3)
                else:
                    self.logger.log(f"-> REJECTED (not in catalog or allowlist)", 3)
            else:
                self.logger.log(f"-> REJECTED (could not resolve)", 3)
                
                # **FALLBACK EMIT DETECTION** for unresolved calls
                if self.emit_visitor.is_emit_call_enhanced("", name_parts, raw_name, node):
                    event_name = self.emit_visitor.extract_dynamic_event_name(node)
                    emit_target = f"{raw_name}::{event_name}"
                    
                    self._add_unique_call(emit_target)
                    self.logger.log(f"-> ADDED unresolved emit call: {emit_target}", 3)
                    
                    # Extract context for unresolved emits too
                    self.emit_visitor.extract_enhanced_emit_context(node, emit_target, event_name)
            
            # Check for function arguments
            self._process_function_arguments(node, context)
        
        except Exception as e:
            self.logger.log(f"-> ERROR: {e}", 3)
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name with caching to avoid redundant work."""
        cache_key = tuple(name_parts)
        
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if self.logger.log_level >= 2:
                print(f"    [CACHE] {'.'.join(name_parts)} -> {cached_result} (cached)")
            return cached_result
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    def _is_external_library_call(self, resolved_fqn: str) -> bool:
        """Check if this is an external library call."""
        from ...utils import EXTERNAL_LIBRARY_ALLOWLIST
        return any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST)
    
    def _track_intermediate_chain_calls(self, name_parts: List[str], context: Dict[str, Any], final_resolved_fqn: str):
        """Track intermediate method calls in complex chains."""
        self.logger.log(f"    [INTERMEDIATE] Tracking chain steps for: {'.'.join(name_parts)}", 4)
        
        # Only track intermediate calls if we have a multi-part chain
        if len(name_parts) <= 1:
            return
        
        # Track each progressive step in the chain (excluding the final call)
        for i in range(1, len(name_parts)):
            partial_chain = name_parts[:i+1]
            partial_name = ".".join(partial_chain)
            
            self.logger.log(f"    [INTERMEDIATE] Step {i}: {partial_name}", 4)
            
            # Skip if this is the same as the final resolved call
            if partial_name == ".".join(name_parts):
                continue
            
            # Try to resolve this partial chain
            partial_resolved = self._cached_resolve_name(partial_chain, context)
            
            if partial_resolved and partial_resolved != final_resolved_fqn:
                self.logger.log(f"    [INTERMEDIATE] Step {i} resolved to: {partial_resolved}", 4)
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.current_function_report["calls"]:
                        self._add_unique_call(partial_resolved)
                        self.logger.log(f"    [INTERMEDIATE] ADDED intermediate call: {partial_resolved}", 4)
                
                # Update context for next step using return type if available
                if i < len(name_parts) - 1:
                    self._update_chain_context(partial_resolved, name_parts[0], context)
            else:
                self.logger.log(f"    [INTERMEDIATE] Step {i} could not be resolved or same as final", 4)
    
    def _update_chain_context(self, resolved_fqn: str, base_name: str, context: Dict[str, Any]):
        """Update resolution context based on intermediate call return type."""
        if resolved_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][resolved_fqn]
            return_type = func_info.get("return_type")
            if return_type:
                # Extract core type and try to resolve it to FQN
                type_inference = context.get('type_inference')
                if type_inference:
                    core_type = type_inference.extract_core_type(return_type)
                    if core_type:
                        resolved_type_fqn = type_inference._resolve_return_type_to_fqn(core_type, context)
                        if resolved_type_fqn:
                            # Update symbol table for next resolution step
                            symbol_manager = context.get('symbol_manager')
                            if symbol_manager:
                                symbol_manager.update_variable_type(base_name, resolved_type_fqn)
                                self.logger.log(f"    [INTERMEDIATE] Updated context: {base_name} -> {resolved_type_fqn}", 4)
    
    def _process_function_arguments(self, node: ast.Call, context: Dict[str, Any]):
        """Process function arguments for function references."""
        for arg in node.args:
            if isinstance(arg, ast.Name):
                self.logger.log(f"[FUNCTION_ARG] Checking argument: {arg.id}", 4)
                arg_fqn = self.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                            arg_fqn in self.recon_data.get("external_functions", {}))):
                    self._add_unique_call(arg_fqn)
                    self.logger.log(f"-> ADDED to calls (function as argument): {arg_fqn}", 4)
