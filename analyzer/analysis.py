"""
Analysis Pass - Code Atlas - ENHANCED SOCKETIO EMIT DETECTION

This file contains the enhanced version of analysis.py with significantly improved
SocketIO emit detection capabilities including f-strings, dynamic patterns, and nested emits.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional

from .resolver import NameResolver
from .type_inference import TypeInferenceEngine
from .symbol_table import SymbolTableManager
from .code_checker import CodeStandardChecker
from .utils import LOG_LEVEL, EXTERNAL_LIBRARY_ALLOWLIST, log_violation, ViolationType


class AnalysisVisitor(ast.NodeVisitor):
    """Enhanced analysis visitor with advanced SocketIO emit detection."""
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str):
        self.recon_data = recon_data
        self.module_name = module_name
        self.import_map = {}
        
        # Core components
        self.name_resolver = NameResolver(recon_data)
        self.type_inference = TypeInferenceEngine(recon_data)
        self.symbol_manager = SymbolTableManager()
        self.code_checker = CodeStandardChecker()
        
        # Context tracking
        self.current_class = None
        self.current_function_report = None
        self.current_function_fqn = None
        self.resolution_cache = {}
        
        # Output
        self.module_report = {
            "file_path": f"{module_name}.py",
            "module_docstring": None,
            "imports": {},
            "classes": [],
            "functions": [],
            "module_state": []
        }
    
    def log(self, message: str, indent: int = 0, level: int = 1):
        """Output formatted log messages with level control."""
        if level <= LOG_LEVEL:
            print("  " * indent + message)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current resolution context."""
        return {
            'current_module': self.module_name,
            'current_class': self.current_class,
            'current_function_fqn': self.current_function_fqn,
            'import_map': self.import_map,
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        }
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name with caching to avoid redundant work."""
        cache_key = tuple(name_parts)
        
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if LOG_LEVEL >= 2:
                print(f"    [CACHE] {'.'.join(name_parts)} -> {cached_result} (cached)")
            return cached_result
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    # === ENHANCED SOCKETIO EMIT DETECTION ===
    
    def _is_emit_call_enhanced(self, resolved_fqn: str, name_parts: List[str], 
                              raw_name: str, call_node: ast.Call) -> bool:
        """ENHANCED: Comprehensive emit call detection with multiple strategies."""
        
        # Strategy 1: Direct FQN matching (existing)
        if self._is_direct_emit_match(resolved_fqn):
            self.log(f"[EMIT_DETECTION] Direct FQN match: {resolved_fqn}", 4)
            return True
            
        # Strategy 2: Pattern-based matching (enhanced)
        if self._is_pattern_emit_match(resolved_fqn, name_parts, raw_name):
            self.log(f"[EMIT_DETECTION] Pattern match: {raw_name}", 4)
            return True
            
        # Strategy 3: NEW - F-string emit detection
        if self._is_fstring_emit_call(call_node):
            self.log(f"[EMIT_DETECTION] F-string emit detected", 4)
            return True
            
        # Strategy 4: NEW - Dynamic variable-based emit detection
        if self._is_dynamic_emit_call(call_node, name_parts):
            self.log(f"[EMIT_DETECTION] Dynamic emit detected", 4)
            return True
            
        # Strategy 5: NEW - Instance method emit detection
        if self._is_instance_emit_call(call_node):
            self.log(f"[EMIT_DETECTION] Instance emit detected", 4)
            return True
            
        return False
    
    def _is_direct_emit_match(self, resolved_fqn: str) -> bool:
        """Check direct FQN matches."""
        if not resolved_fqn:
            return False
            
        return (resolved_fqn == 'flask_socketio.emit' or
                resolved_fqn.endswith('.emit') or
                'SocketIO' in resolved_fqn or
                'socketio' in resolved_fqn.lower())
    
    def _is_pattern_emit_match(self, resolved_fqn: str, name_parts: List[str], raw_name: str) -> bool:
        """Enhanced pattern matching."""
        # Check if 'emit' is in name parts
        if 'emit' in name_parts:
            return True
            
        # Check raw name patterns
        emit_patterns = ['.emit(', '.emit', 'socketio.emit', '_socketio_instance.emit']
        if any(pattern in raw_name for pattern in emit_patterns):
            return True
            
        # Check for common instance names with emit
        socketio_instances = ['socketio', 'socket_io', 'sio', '_socketio_instance', 'app_socketio']
        for instance in socketio_instances:
            if instance in raw_name and 'emit' in raw_name:
                return True
                
        return False
    
    def _is_fstring_emit_call(self, call_node: ast.Call) -> bool:
        """NEW: Detect f-string based emit calls like socketio.emit(f'{event}_success', ...)"""
        try:
            if isinstance(call_node.func, ast.Attribute) and call_node.func.attr == 'emit':
                # Check if the first argument contains dynamic content
                if call_node.args and len(call_node.args) > 0:
                    first_arg = call_node.args[0]
                    
                    # JoinedStr indicates f-string
                    if isinstance(first_arg, ast.JoinedStr):
                        return True
                        
                    # BinOp with Add might be string concatenation
                    if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
                        if self._involves_string_operations(first_arg):
                            return True
                            
                    # Call to .format() method
                    if isinstance(first_arg, ast.Call):
                        if (isinstance(first_arg.func, ast.Attribute) and 
                            first_arg.func.attr == 'format'):
                            return True
        except Exception:
            pass
        return False
    
    def _is_dynamic_emit_call(self, call_node: ast.Call, name_parts: List[str]) -> bool:
        """NEW: Detect dynamic emit calls where the method or event name is computed."""
        try:
            if isinstance(call_node.func, ast.Attribute) and call_node.func.attr == 'emit':
                # Check if the object being called looks like a socketio instance
                obj_name = self._extract_object_name(call_node.func.value)
                if obj_name:
                    socketio_hints = ['socketio', 'socket', 'sio', 'emit', 'app']
                    if any(hint in obj_name.lower() for hint in socketio_hints):
                        return True
        except Exception:
            pass
        return False
    
    def _is_instance_emit_call(self, call_node: ast.Call) -> bool:
        """NEW: Detect emit calls on instances that might be SocketIO objects."""
        try:
            if isinstance(call_node.func, ast.Attribute) and call_node.func.attr == 'emit':
                # Get the base object
                obj_node = call_node.func.value
                
                # Check for global/module-level socketio instances
                if isinstance(obj_node, ast.Name):
                    obj_name = obj_node.id
                    # Common global socketio variable names
                    global_socketio_names = [
                        'socketio', 'sio', 'app', 'socket_io', 
                        '_socketio_instance', 'socketio_app'
                    ]
                    if obj_name in global_socketio_names:
                        return True
                        
                # Check for attribute access like app.socketio.emit
                elif isinstance(obj_node, ast.Attribute):
                    full_name = self._extract_object_name(obj_node)
                    if full_name and any(hint in full_name.lower() 
                                       for hint in ['socketio', 'socket', 'sio']):
                        return True
        except Exception:
            pass
        return False
    
    def _involves_string_operations(self, node: ast.AST) -> bool:
        """Check if an AST node involves string operations."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.JoinedStr):  # f-string
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return (self._involves_string_operations(node.left) or 
                   self._involves_string_operations(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Check for string methods like .format(), .join(), etc.
            if node.func.attr in ['format', 'join', 'replace', 'strip', 'upper', 'lower']:
                return True
        return False
    
    def _extract_object_name(self, node: ast.AST) -> Optional[str]:
        """Extract object name from AST node for analysis."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._extract_object_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return None
    
    def _extract_dynamic_event_name(self, call_node: ast.Call) -> str:
        """Extract event name from dynamic emit calls with enhanced f-string support."""
        if not call_node.args:
            return "unknown_event"
            
        first_arg = call_node.args[0]
        
        # Handle f-strings (JoinedStr)
        if isinstance(first_arg, ast.JoinedStr):
            return self._extract_fstring_pattern(first_arg)
            
        # Handle string concatenation (BinOp)
        if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
            return self._extract_binop_pattern(first_arg)
            
        # Handle .format() calls
        if isinstance(first_arg, ast.Call):
            if (isinstance(first_arg.func, ast.Attribute) and 
                first_arg.func.attr == 'format'):
                return self._extract_format_pattern(first_arg)
                
        # Handle variable references
        if isinstance(first_arg, ast.Name):
            return f"${first_arg.id}"
            
        # Handle constant strings
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value
            
        return "dynamic_event"
    
    def _extract_fstring_pattern(self, fstring_node: ast.JoinedStr) -> str:
        """Extract pattern from f-string AST node."""
        parts = []
        for value in fstring_node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                if isinstance(value.value, ast.Name):
                    parts.append(f"${{{value.value.id}}}")
                elif isinstance(value.value, ast.Attribute):
                    attr_name = self._extract_object_name(value.value)
                    parts.append(f"${{{attr_name}}}")
                else:
                    parts.append("{expr}")
        return "".join(parts)
    
    def _extract_binop_pattern(self, binop_node: ast.BinOp) -> str:
        """Extract pattern from binary operation (string concatenation)."""
        try:
            left_part = self._extract_string_part(binop_node.left)
            right_part = self._extract_string_part(binop_node.right)
            return f"{left_part}{right_part}"
        except:
            return "concat_pattern"
    
    def _extract_format_pattern(self, call_node: ast.Call) -> str:
        """Extract pattern from .format() method calls."""
        try:
            if isinstance(call_node.func.value, ast.Constant):
                template = call_node.func.value.value
                # Replace {} with placeholder indicators
                import re
                pattern = re.sub(r'\{[^}]*\}', '{var}', template)
                return pattern
        except:
            pass
        return "format_pattern"
    
    def _extract_string_part(self, node: ast.AST) -> str:
        """Extract string representation from an AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Name):
            return f"${node.id}"
        elif isinstance(node, ast.Attribute):
            return f"${self._extract_object_name(node)}"
        else:
            return "{expr}"
    
    def _extract_enhanced_emit_context(self, call_node: ast.Call, emit_target: str, event_name: str):
        """Extract and store enhanced emit context information."""
        emit_context = {}
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == 'room':
                emit_context['room'] = self._extract_context_value(keyword.value)
                self.log(f"[EMIT] Room parameter: {emit_context['room']}", 4)
                
            elif keyword.arg == 'broadcast':
                emit_context['broadcast'] = self._extract_context_value(keyword.value)
                self.log(f"[EMIT] Broadcast parameter: {emit_context['broadcast']}", 4)
                
            elif keyword.arg == 'include_self':
                emit_context['include_self'] = self._extract_context_value(keyword.value)
                
            elif keyword.arg == 'namespace':
                emit_context['namespace'] = self._extract_context_value(keyword.value)
        
        # Check for additional positional arguments (data payload)
        if len(call_node.args) > 1:
            emit_context['has_data'] = True
            emit_context['data_args_count'] = len(call_node.args) - 1
        
        # Store emit context
        if emit_context:
            context_key = f"{emit_target}_context"
            if "emit_contexts" not in self.current_function_report:
                self.current_function_report["emit_contexts"] = {}
            self.current_function_report["emit_contexts"][context_key] = emit_context
    
    def _extract_context_value(self, node: ast.AST) -> Any:
        """Extract value from context parameter nodes."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return f"${node.id}"
        elif isinstance(node, ast.JoinedStr):
            return self._extract_fstring_pattern(node)
        elif isinstance(node, ast.Attribute):
            return f"${self._extract_object_name(node)}"
        else:
            return "dynamic_value"
    
    # === ENHANCED VISIT_CALL METHOD ===
    
    def visit_Call(self, node: ast.Call):
        """ENHANCED: Process function calls with comprehensive SocketIO emit detection."""
        if not self.current_function_report:
            return
        
        try:
            name_parts = self.name_resolver.extract_name_parts(node.func)
            if not name_parts:
                self.log(f"[CALL] Could not extract name parts from call", 3)
                return
            
            raw_name = ".".join(name_parts)
            self.log(f"[CALL] Found call: {raw_name}", 3)
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 'max', 'min', 'sum', 'abs', 'round', 'sorted']:
                self.log(f"-> IGNORED (built-in function)", 3)
                self.generic_visit(node)
                return
            
            context = self._get_context()
            
            # Always resolve the complete call first
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            # Track intermediate calls in method chains
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            
            # **ENHANCED EMIT DETECTION**
            if self._is_emit_call_enhanced(resolved_fqn or "", name_parts, raw_name, node):
                # Extract event name using enhanced methods
                event_name = self._extract_dynamic_event_name(node)
                
                # Create emit entry with resolved or raw name
                emit_target_base = resolved_fqn if resolved_fqn else raw_name
                emit_target = f"{emit_target_base}::{event_name}"
                
                self._add_unique_call(emit_target)
                self.log(f"-> DETECTED and ADDED emit call: {emit_target}", 3)
                
                # Extract enhanced emit context
                self._extract_enhanced_emit_context(node, emit_target, event_name)
                
            elif resolved_fqn:
                self.log(f"-> Resolved to: {resolved_fqn}", 3)
                
                # Handle instantiations
                if resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.log(f"-> ADDED to instantiations", 3)
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.log(f"-> ADDED to instantiations (external)", 3)
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls", 3)
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls (external)", 3)
                # Handle external library calls
                elif any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls (external library)", 3)
                else:
                    self.log(f"-> REJECTED (not in catalog or allowlist)", 3)
            else:
                self.log(f"-> REJECTED (could not resolve)", 3)
                
                # **FALLBACK EMIT DETECTION** for unresolved calls
                if self._is_emit_call_enhanced("", name_parts, raw_name, node):
                    event_name = self._extract_dynamic_event_name(node)
                    emit_target = f"{raw_name}::{event_name}"
                    
                    self._add_unique_call(emit_target)
                    self.log(f"-> ADDED unresolved emit call: {emit_target}", 3)
                    
                    # Extract context for unresolved emits too
                    self._extract_enhanced_emit_context(node, emit_target, event_name)
            
            # Check for function arguments
            self._process_function_arguments(node)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)
    
    # === REST OF THE CLASS METHODS (unchanged) ===
    # Note: All other methods from the original AnalysisVisitor remain the same
    # including visit_Module, visit_Import, visit_ClassDef, visit_FunctionDef, etc.
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        self.log("=== Starting Module Analysis ===")
        
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.module_report["module_docstring"] = node.body[0].value.value
        
        self.generic_visit(node)
        self.module_report["imports"] = self.import_map.copy()
        self.log("=== Module Analysis Complete ===")
    
    def visit_Import(self, node: ast.Import):
        """Process imports."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            self.log(f"[IMPORT] {key} -> {alias.name}", 2)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                self.log(f"[FROM_IMPORT] {key} -> {node.module}.{alias.name}", 2)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        class_fqn = f"{self.module_name}.{node.name}"
        self.log(f"[CLASS] Analyzing class: {node.name}", 1)
        
        class_report = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "methods": []
        }
        
        old_class = self.current_class
        self.current_class = class_fqn
        self.symbol_manager.enter_class_scope()
        
        try:
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_report = self._analyze_function(child)
                    class_report["methods"].append(method_report)
        finally:
            self.current_class = old_class
            self.symbol_manager.exit_class_scope()
        
        self.module_report["classes"].append(class_report)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and handle nested functions properly."""
        if not self.current_class:
            # Top-level function
            self.log(f"[FUNCTION] Analyzing function: {node.name}", 1)
            function_report = self._analyze_function(node)
            self.module_report["functions"].append(function_report)
        elif not self.current_function_report:
            # Class method (not nested)
            method_report = self._analyze_function(node)
            # This will be handled by visit_ClassDef
        else:
            # Nested function - process within current function context
            self.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
            self.symbol_manager.enter_nested_scope()
            try:
                # Populate symbol table from nested function arguments
                self._populate_symbols_from_args(node.args)
                # Traverse nested function body - all calls will be attributed to parent
                for child in node.body:
                    self.visit(child)
            finally:
                self.symbol_manager.exit_nested_scope()
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function with clean separation of concerns."""
        if self.current_class:
            function_fqn = f"{self.current_class}.{node.name}"
        else:
            function_fqn = f"{self.module_name}.{node.name}"
        
        self.log(f"[FUNCTION_ANALYSIS] Starting analysis of: {function_fqn}", 2)
        
        function_report = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "docstring": ast.get_docstring(node),
            "calls": [],
            "instantiations": [],
            "accessed_state": [],
            "decorators": [],
            "emit_contexts": {}  # Store SocketIO emit context information
        }
        
        # Check for code standard violations
        violations = self.code_checker.check_function_type_hints(node, function_fqn)
        if violations:
            self.log(f"[CODE_QUALITY] Found {len(violations)} violations in {function_fqn}", 3)
        
        # Process decorators
        for decorator in node.decorator_list:
            try:
                decorator_str = f"@{ast.unparse(decorator)}"
                function_report["decorators"].append(decorator_str)
                self.log(f"[DECORATOR] {decorator_str}", 2)
            except Exception:
                pass
        
        # Set up function context
        old_report = self.current_function_report
        old_fqn = self.current_function_fqn
        self.current_function_report = function_report
        self.current_function_fqn = function_fqn
        self.symbol_manager.enter_function_scope()
        self.resolution_cache = {}

        try:
            # Populate symbol table from arguments
            self._populate_symbols_from_args(node.args)
            
            # Analyze function body
            for child in node.body:
                self._visit_with_nested_handling(child)
        
        finally:
            self.current_function_report = old_report
            self.current_function_fqn = old_fqn
        
        # Clean up empty emit_contexts to keep JSON clean
        if not function_report.get("emit_contexts"):
            function_report.pop("emit_contexts", None)
        
        self.log(f"[FUNCTION_ANALYSIS] Completed analysis of: {function_fqn}", 2)
        self.log(f"  Calls: {len(function_report['calls'])}", 3)
        self.log(f"  Instantiations: {len(function_report['instantiations'])}", 3)
        self.log(f"  State Access: {len(function_report['accessed_state'])}", 3)
        emit_count = len(function_report.get("emit_contexts", {}))
        if emit_count > 0:
            self.log(f"  SocketIO Emits: {emit_count}", 3)
        
        return function_report

    def _populate_symbols_from_args(self, args: ast.arguments):
        """Populate symbol table from function arguments with violation checking and parameter type lookup."""
        context = self._get_context()
        self.log(f"[ARG_PROCESSING] Processing {len(args.args)} arguments", 3)
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.current_function_fqn and self.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                self.log(f"[ARG_PROCESSING] Found parameter types in recon data: {param_types_from_recon}", 4)
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
                
            if arg.annotation:
                # Type hint present - process normally
                try:
                    type_parts = self.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        self.log(f"[ARG_TYPE] Processing type annotation for {arg.arg}: {'.'.join(type_parts)}", 4)
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type}", 4)
                        else:
                            self.log(f"[ARG_TYPE] FAILED Could not resolve type annotation for {arg.arg}", 4)
                            log_violation(
                                ViolationType.UNRESOLVABLE_TYPE,
                                f"Type annotation for parameter '{arg.arg}' could not be resolved",
                                "Method calls on this parameter may fail"
                            )
                except Exception as e:
                    self.log(f"[ARG_TYPE] ERROR processing type for {arg.arg}: {e}", 4)
            elif arg.arg in param_types_from_recon:
                # No direct annotation but we have type info from recon
                param_type_str = param_types_from_recon[arg.arg]
                self.log(f"[ARG_TYPE] Using recon data type for {arg.arg}: {param_type_str}", 4)
                
                try:
                    # Parse the type string and resolve it
                    import ast as ast_module
                    type_node = ast_module.parse(param_type_str, mode='eval').body
                    type_parts = self.name_resolver.extract_name_parts(type_node)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type} (from recon)", 4)
                        else:
                            # Fallback to the original string
                            self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                            self.log(f"[ARG_TYPE] FALLBACK {arg.arg} : {param_type_str} (from recon)", 4)
                    else:
                        # Simple type, use as-is
                        self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        self.log(f"[ARG_TYPE] SIMPLE {arg.arg} : {param_type_str} (from recon)", 4)
                except Exception as e:
                    self.log(f"[ARG_TYPE] ERROR processing recon type for {arg.arg}: {e}", 4)
                    # Still use the string as fallback
                    self.symbol_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data - already logged by code checker
                self.log(f"[ARG_TYPE] No type hint or recon data for {arg.arg}", 4)

    def _visit_with_nested_handling(self, node: ast.AST):
        """Handle nested functions properly."""
        if isinstance(node, ast.FunctionDef) and self.current_function_report:
            self.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
            self.symbol_manager.enter_nested_scope()
            try:
                self._populate_symbols_from_args(node.args)
                for child in node.body:
                    self.visit(child)
            finally:
                self.symbol_manager.exit_nested_scope()
        else:
            self.visit(node)

    def _track_intermediate_chain_calls(self, name_parts: List[str], context: Dict[str, Any], final_resolved_fqn: str):
        """Track intermediate method calls in complex chains."""
        self.log(f"    [INTERMEDIATE] Tracking chain steps for: {'.'.join(name_parts)}", 4)
        
        # Only track intermediate calls if we have a multi-part chain
        if len(name_parts) <= 1:
            return
        
        # Track each progressive step in the chain (excluding the final call)
        for i in range(1, len(name_parts)):
            partial_chain = name_parts[:i+1]
            partial_name = ".".join(partial_chain)
            
            self.log(f"    [INTERMEDIATE] Step {i}: {partial_name}", 4)
            
            # Skip if this is the same as the final resolved call
            if partial_name == ".".join(name_parts):
                continue
            
            # Try to resolve this partial chain
            partial_resolved = self._cached_resolve_name(partial_chain, context)
            
            if partial_resolved and partial_resolved != final_resolved_fqn:
                self.log(f"    [INTERMEDIATE] Step {i} resolved to: {partial_resolved}", 4)
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.current_function_report["calls"]:
                        self._add_unique_call(partial_resolved)
                        self.log(f"    [INTERMEDIATE] ADDED intermediate call: {partial_resolved}", 4)
                
                # Update context for next step using return type if available
                if i < len(name_parts) - 1:
                    self._update_chain_context(partial_resolved, name_parts[0], context)
            else:
                self.log(f"    [INTERMEDIATE] Step {i} could not be resolved or same as final", 4)

    def _update_chain_context(self, resolved_fqn: str, base_name: str, context: Dict[str, Any]):
        """Update resolution context based on intermediate call return type."""
        if resolved_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][resolved_fqn]
            return_type = func_info.get("return_type")
            if return_type:
                # Extract core type and try to resolve it to FQN
                core_type = self.type_inference.extract_core_type(return_type)
                if core_type:
                    resolved_type_fqn = self.type_inference._resolve_return_type_to_fqn(core_type, context)
                    if resolved_type_fqn:
                        # Update symbol table for next resolution step
                        self.symbol_manager.update_variable_type(base_name, resolved_type_fqn)
                        self.log(f"    [INTERMEDIATE] Updated context: {base_name} -> {resolved_type_fqn}", 4)

    def _process_function_arguments(self, node: ast.Call):
        """Process function arguments for function references."""
        context = self._get_context()
        
        for arg in node.args:
            if isinstance(arg, ast.Name):
                self.log(f"[FUNCTION_ARG] Checking argument: {arg.id}", 4)
                arg_fqn = self.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                            arg_fqn in self.recon_data.get("external_functions", {}))):
                    self._add_unique_call(arg_fqn)
                    self.log(f"-> ADDED to calls (function as argument): {arg_fqn}", 4)

    def visit_Name(self, node: ast.Name):
        """Process name references for state access."""
        if not self.current_function_report:
            return
        
        try:
            self.log(f"[NAME] Found name reference: {node.id}", 3)
            
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name([node.id], context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check
                if not self.symbol_manager.get_variable_type(node.id):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.log(f"-> REJECTED (shadowed by local variable)", 3)
            else:
                self.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Process attribute access for state variables."""
        if not self.current_function_report:
            self.generic_visit(node)
            return
        
        try:
            name_parts = self.name_resolver.extract_name_parts(node)
            if not name_parts:
                self.generic_visit(node)
                return
            
            full_name = ".".join(name_parts)
            self.log(f"[ATTRIBUTE] Found attribute access: {full_name}", 3)
            
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check on base
                base_name = name_parts[0]
                if not self.symbol_manager.get_variable_type(base_name):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.log(f"-> REJECTED (base shadowed)", 3)
            else:
                self.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Process assignments for both module state and local variables."""
        if not self.current_class and not self.current_function_report:
            # Module-level state
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        state_entry = {
                            "name": target.id,
                            "value": ast.unparse(node.value) if node.value else "None"
                        }
                        self.module_report["module_state"].append(state_entry)
                        self.log(f"[MODULE_STATE] {target.id} = {state_entry['value']}", 2)
                    except Exception:
                        pass
        elif self.current_function_report:
            # Function-level assignments - update symbol table
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        self.log(f"[ASSIGNMENT] Processing: {target.id} = ...", 3)
                        
                        if isinstance(node.value, ast.Call):
                            # This is a function call assignment
                            self.log(f"[ASSIGNMENT] Call assignment detected", 4)
                            context = self._get_context()
                            var_type = self.type_inference.infer_from_call(node.value, self.name_resolver, context)
                            if var_type:
                                self.symbol_manager.update_variable_type(target.id, var_type)
                                self.log(f"[ASSIGNMENT] RESOLVED Updated symbol table: {target.id} = {var_type}", 4)
                            else:
                                self.log(f"[ASSIGNMENT] FAILED Could not infer type for {target.id}", 4)
                        else:
                            self.log(f"[ASSIGNMENT] Non-call assignment", 4)
                    except Exception as e:
                        self.log(f"[ASSIGNMENT] ERROR: {e}", 4)
        
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments."""
        if (not self.current_class and not self.current_function_report and
            isinstance(node.target, ast.Name)):
            try:
                state_entry = {
                    "name": node.target.id,
                    "value": ast.unparse(node.value) if node.value else "None"
                }
                self.module_report["module_state"].append(state_entry)
                self.log(f"[MODULE_STATE] {node.target.id} : {ast.unparse(node.annotation) if node.annotation else 'Unknown'} = {state_entry['value']}", 2)
            except Exception:
                pass
        elif self.current_function_report and isinstance(node.target, ast.Name):
            try:
                if node.annotation:
                    self.log(f"[ANNOTATED_ASSIGNMENT] {node.target.id} : {ast.unparse(node.annotation)}", 3)
                    context = self._get_context()
                    type_parts = self.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(node.target.id, resolved_type)
                            self.log(f"-> Updated symbol table: {node.target.id} : {resolved_type}", 4)
                        else:
                            self.log(f"-> Could not resolve type annotation", 4)
            except Exception as e:
                self.log(f"[ANNOTATED_ASSIGNMENT] ERROR: {e}", 3)
        
        self.generic_visit(node)


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with enhanced SocketIO emit detection."""
    print("=== ANALYSIS PASS START (Enhanced SocketIO Detection) ===")
    
    atlas = {}
    
    for py_file in python_files:
        print(f"=== Analyzing {py_file.name} ===")
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = AnalysisVisitor(recon_data, module_name)
            visitor.visit(tree)
            
            atlas[py_file.name] = visitor.module_report
            print(f"  Module analysis complete")
        
        except Exception as e:
            print(f"  ERROR: Failed to analyze {py_file.name}: {e}")
            atlas[py_file.name] = {
                "file_path": py_file.name,
                "module_docstring": None,
                "imports": {},
                "classes": [],
                "functions": [],
                "module_state": []
            }
            continue
    
    print("=== ANALYSIS PASS COMPLETE ===")
    print()
    
    return atlas
