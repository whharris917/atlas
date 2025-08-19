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
        """
        FIXED: Track intermediate method calls in both fluent interfaces and module instance calls.
        
        Handles two patterns:
        1. Fluent interfaces: obj.method1().method2().method3()
        2. Module instances: module_var.method() where module_var is an instance
        """
        self.logger.log(f"    [INTERMEDIATE] Tracking chain steps for: {'.'.join(name_parts)}", 4)
        
        if len(name_parts) <= 1:
            return
        
        # STRATEGY 1: Handle simple module instance calls (e.g., event_validator.validate_event)
        if len(name_parts) == 2:
            base_name = name_parts[0]
            method_name = name_parts[1]
            
            self.logger.log(f"    [INTERMEDIATE] Strategy 1: Module instance call {base_name}.{method_name}", 4)
            
            # Try to resolve the base as a module-level variable
            base_resolved = self._cached_resolve_name([base_name], context)
            
            if base_resolved and base_resolved in self.recon_data.get("state", {}):
                self.logger.log(f"    [INTERMEDIATE] Base resolved to state variable: {base_resolved}", 4)
                
                # Get the type of this state variable
                state_info = self.recon_data["state"][base_resolved]
                if isinstance(state_info, dict):
                    var_type = state_info.get("type")
                    if var_type:
                        self.logger.log(f"    [INTERMEDIATE] State variable type: {var_type}", 4)
                        
                        # Resolve the type to get the class FQN
                        type_fqn = self._resolve_type_to_fqn(var_type, context)
                        if type_fqn:
                            self.logger.log(f"    [INTERMEDIATE] Type resolved to: {type_fqn}", 4)
                            
                            # Check if the method exists on this type
                            method_fqn = f"{type_fqn}.{method_name}"
                            if method_fqn in self.recon_data.get("functions", {}):
                                if method_fqn not in self.current_function_report["calls"]:
                                    self._add_unique_call(method_fqn)
                                    self.logger.log(f"    [INTERMEDIATE] ADDED module instance call: {method_fqn}", 4)
                                return
                            else:
                                self.logger.log(f"    [INTERMEDIATE] Method {method_fqn} not found in functions", 4)
                        else:
                            self.logger.log(f"    [INTERMEDIATE] Could not resolve type: {var_type}", 4)
                    else:
                        self.logger.log(f"    [INTERMEDIATE] No type information for state variable", 4)
                else:
                    self.logger.log(f"    [INTERMEDIATE] State info is not dict format", 4)
            else:
                self.logger.log(f"    [INTERMEDIATE] Base not resolved as state variable", 4)
        
        # STRATEGY 2: Handle fluent interface chains (3+ parts)
        if len(name_parts) >= 3:
            self.logger.log(f"    [INTERMEDIATE] Strategy 2: Fluent interface chain", 4)
            
            # Find where the method chain starts by trying different split points
            current_context_fqn = None
            method_start_index = None
            
            # Try resolving progressively longer base objects
            for split_point in range(1, len(name_parts)):
                base_parts = name_parts[:split_point]
                base_resolved = self._cached_resolve_name(base_parts, context)
                
                if base_resolved:
                    self.logger.log(f"    [INTERMEDIATE] Split point {split_point}: base {'.'.join(base_parts)} -> {base_resolved}", 4)
                    
                    # Check if the next part could be a method on this resolved object
                    if split_point < len(name_parts):
                        next_method = name_parts[split_point]
                        
                        # Get the type of the base object
                        base_type = self._get_object_type(base_resolved, context)
                        if base_type:
                            self.logger.log(f"    [INTERMEDIATE] Base type: {base_type}", 4)
                            
                            method_candidate = f"{base_type}.{next_method}"
                            if method_candidate in self.recon_data.get("functions", {}):
                                # Found the start of the method chain!
                                current_context_fqn = base_type
                                method_start_index = split_point
                                self.logger.log(f"    [INTERMEDIATE] Found fluent chain start: base={'.'.join(base_parts)} -> {base_type}", 4)
                                break
                            else:
                                self.logger.log(f"    [INTERMEDIATE] Method candidate {method_candidate} not found", 4)
                        else:
                            self.logger.log(f"    [INTERMEDIATE] Could not get type for base: {base_resolved}", 4)
            
            if current_context_fqn and method_start_index is not None:
                self.logger.log(f"    [INTERMEDIATE] Processing fluent chain starting at index {method_start_index}", 4)
                
                # Process each method in the fluent chain
                for i in range(method_start_index, len(name_parts)):
                    method_name = name_parts[i]
                    method_fqn = f"{current_context_fqn}.{method_name}"
                    
                    self.logger.log(f"    [INTERMEDIATE] Processing method {i}: {method_name} on {current_context_fqn}", 4)
                    
                    # Check if this method exists
                    if method_fqn in self.recon_data.get("functions", {}):
                        # Don't double-add the final method (handled by main call processing)
                        if i < len(name_parts) - 1:
                            if method_fqn not in self.current_function_report["calls"]:
                                self._add_unique_call(method_fqn)
                                self.logger.log(f"    [INTERMEDIATE] ADDED fluent method: {method_fqn}", 4)
                        
                        # Get return type for next method in chain
                        func_info = self.recon_data["functions"][method_fqn]
                        return_type = func_info.get("return_type")
                        
                        if return_type and return_type not in ["None", "Unknown", None]:
                            # Clean quoted return types
                            clean_return_type = return_type.strip("'\"")
                            self.logger.log(f"    [INTERMEDIATE] Method {method_name} returns: {clean_return_type}", 4)
                            
                            # Resolve return type to FQN for next method
                            resolved_return_type = self._resolve_type_to_fqn(clean_return_type, context)
                            if resolved_return_type:
                                current_context_fqn = resolved_return_type
                                self.logger.log(f"    [INTERMEDIATE] Chain continues with: {resolved_return_type}", 4)
                            else:
                                self.logger.log(f"    [INTERMEDIATE] Could not resolve return type: {clean_return_type}", 4)
                                break
                        else:
                            self.logger.log(f"    [INTERMEDIATE] No useful return type for {method_fqn}", 4)
                            break
                    else:
                        self.logger.log(f"    [INTERMEDIATE] Method {method_fqn} not found", 4)
                        break
            else:
                self.logger.log(f"    [INTERMEDIATE] Could not identify fluent chain start", 4)
    
    def _get_object_type(self, resolved_fqn: str, context: Dict[str, Any]) -> Optional[str]:
        """Get the type of a resolved object (for fluent interface processing)."""
        self.logger.log(f"    [TYPE] Getting object type for: {resolved_fqn}", 4)
        
        # If it's already a class, return as-is
        if resolved_fqn in self.recon_data.get("classes", {}):
            self.logger.log(f"    [TYPE] Object is a class: {resolved_fqn}", 4)
            return resolved_fqn
        
        # If it's a state variable, get its type
        if resolved_fqn in self.recon_data.get("state", {}):
            self.logger.log(f"    [TYPE] Object is a state variable", 4)
            state_info = self.recon_data["state"][resolved_fqn]
            if isinstance(state_info, dict):
                var_type = state_info.get("type")
                if var_type:
                    self.logger.log(f"    [TYPE] State variable type: {var_type}", 4)
                    resolved_type = self._resolve_type_to_fqn(var_type, context)
                    self.logger.log(f"    [TYPE] Resolved to: {resolved_type}", 4)
                    return resolved_type
        
        # If it's a function, get its return type
        if resolved_fqn in self.recon_data.get("functions", {}):
            self.logger.log(f"    [TYPE] Object is a function", 4)
            func_info = self.recon_data["functions"][resolved_fqn]
            return_type = func_info.get("return_type")
            if return_type and return_type not in ["None", "Unknown", None]:
                clean_return_type = return_type.strip("'\"")
                self.logger.log(f"    [TYPE] Function returns: {clean_return_type}", 4)
                resolved_type = self._resolve_type_to_fqn(clean_return_type, context)
                self.logger.log(f"    [TYPE] Resolved to: {resolved_type}", 4)
                return resolved_type
        
        self.logger.log(f"    [TYPE] Could not determine type for: {resolved_fqn}", 4)
        return None
    
    def _resolve_type_to_fqn(self, type_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve a type name to its fully qualified name."""
        if not type_name or type_name in ["None", "Unknown"]:
            return None
        
        self.logger.log(f"    [TYPE_RESOLVE] Resolving type: {type_name}", 4)
        
        # Already FQN
        if "." in type_name:
            if type_name in self.recon_data.get("classes", {}):
                self.logger.log(f"    [TYPE_RESOLVE] Already FQN and exists: {type_name}", 4)
                return type_name
        
        # Extract core type from generics
        core_type = type_name.split("[")[0] if "[" in type_name else type_name
        self.logger.log(f"    [TYPE_RESOLVE] Core type: {core_type}", 4)
        
        # Try name resolver first
        resolved = self.name_resolver.resolve_name([core_type], context)
        if resolved and resolved in self.recon_data.get("classes", {}):
            self.logger.log(f"    [TYPE_RESOLVE] Name resolver found: {resolved}", 4)
            return resolved
        
        # Search all classes for this type name
        for class_fqn in self.recon_data.get("classes", {}):
            if class_fqn.endswith(f".{core_type}"):
                self.logger.log(f"    [TYPE_RESOLVE] Found by suffix match: {class_fqn}", 4)
                return class_fqn
        
        # Try current module
        current_module = context.get('current_module', '')
        if current_module:
            candidate = f"{current_module}.{core_type}"
            if candidate in self.recon_data.get("classes", {}):
                self.logger.log(f"    [TYPE_RESOLVE] Found in current module: {candidate}", 4)
                return candidate
        
        self.logger.log(f"    [TYPE_RESOLVE] Could not resolve type: {type_name}", 4)
        return None
    
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
