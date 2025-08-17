"""
SocketIO Emit Visitor - Code Atlas

Specialized visitor for comprehensive SocketIO emit detection including
f-strings, dynamic patterns, and nested emits.
"""

import ast
from typing import Dict, List, Any, Optional


class EmitVisitor:
    """Specialized visitor for advanced SocketIO emit detection."""
    
    def __init__(self, name_resolver, current_function_report, logger):
        self.name_resolver = name_resolver
        self.current_function_report = current_function_report
        self.logger = logger
    
    def is_emit_call_enhanced(self, resolved_fqn: str, name_parts: List[str], 
                              raw_name: str, call_node: ast.Call) -> bool:
        """ENHANCED: Comprehensive emit call detection with multiple strategies."""
        
        # Strategy 1: Direct FQN matching
        if self._is_direct_emit_match(resolved_fqn):
            self.logger.log(f"[EMIT_DETECTION] Direct FQN match: {resolved_fqn}", 4)
            return True
            
        # Strategy 2: Pattern-based matching
        if self._is_pattern_emit_match(resolved_fqn, name_parts, raw_name):
            self.logger.log(f"[EMIT_DETECTION] Pattern match: {raw_name}", 4)
            return True
            
        # Strategy 3: F-string emit detection
        if self._is_fstring_emit_call(call_node):
            self.logger.log(f"[EMIT_DETECTION] F-string emit detected", 4)
            return True
            
        # Strategy 4: Dynamic variable-based emit detection
        if self._is_dynamic_emit_call(call_node, name_parts):
            self.logger.log(f"[EMIT_DETECTION] Dynamic emit detected", 4)
            return True
            
        # Strategy 5: Instance method emit detection
        if self._is_instance_emit_call(call_node):
            self.logger.log(f"[EMIT_DETECTION] Instance emit detected", 4)
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
        """Detect f-string based emit calls like socketio.emit(f'{event}_success', ...)"""
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
        """Detect dynamic emit calls where the method or event name is computed."""
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
        """Detect emit calls on instances that might be SocketIO objects."""
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
    
    def extract_dynamic_event_name(self, call_node: ast.Call) -> str:
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
    
    def extract_enhanced_emit_context(self, call_node: ast.Call, emit_target: str, event_name: str):
        """Extract and store enhanced emit context information."""
        emit_context = {}
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == 'room':
                emit_context['room'] = self._extract_context_value(keyword.value)
                self.logger.log(f"[EMIT] Room parameter: {emit_context['room']}", 4)
                
            elif keyword.arg == 'broadcast':
                emit_context['broadcast'] = self._extract_context_value(keyword.value)
                self.logger.log(f"[EMIT] Broadcast parameter: {emit_context['broadcast']}", 4)
                
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
