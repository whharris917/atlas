"""
External Resolution Visitor - Code Atlas

Handles name resolution for external libraries and frameworks.
This visitor focuses on resolving names from imported external libraries.
"""

from typing import Dict, Any, Optional

# Import LOG_LEVEL from utils - handle both relative and absolute imports
try:
    from ...utils import LOG_LEVEL
except ImportError:
    try:
        from utils import LOG_LEVEL
    except ImportError:
        # Fallback if utils not available
        LOG_LEVEL = 1


class ExternalResolutionVisitor:
    """
    Handles name resolution for external libraries and frameworks.
    
    This visitor resolves:
    - External class methods and attributes
    - Common framework patterns (SocketIO, threading, etc.)
    - Library-specific method signatures
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def resolve_external_name(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a name from external libraries.
        
        Args:
            name: Name to resolve
            context: Resolution context
            
        Returns:
            FQN if resolved from external libraries, None otherwise
        """
        if LOG_LEVEL >= 3:
            print(f"        [EXTERNAL] Resolving external name: {name}")
        
        # Strategy 1: Check external classes
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info.get("local_alias") == name:
                if LOG_LEVEL >= 3:
                    print(f"        [EXTERNAL] Found external class: {ext_class_fqn}")
                return ext_class_fqn
        
        # Strategy 2: Check external functions
        for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
            if ext_info.get("local_alias") == name:
                if LOG_LEVEL >= 3:
                    print(f"        [EXTERNAL] Found external function: {ext_func_fqn}")
                return ext_func_fqn
        
        if LOG_LEVEL >= 3:
            print(f"        [EXTERNAL] No external match for: {name}")
        return None
    
    def resolve_external_method(self, class_fqn: str, method_name: str) -> Optional[str]:
        """
        Resolve a method call on an external class.
        
        Args:
            class_fqn: FQN of the external class
            method_name: Name of the method
            
        Returns:
            FQN of the external method if valid, None otherwise
        """
        if LOG_LEVEL >= 3:
            print(f"        [EXTERNAL] Resolving external method: {class_fqn}.{method_name}")
        
        # Check if the class is in our external classes catalog
        if class_fqn not in self.recon_data.get("external_classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [EXTERNAL] Class not in external catalog: {class_fqn}")
            return None
        
        # For external classes, we use heuristic method validation
        if self._is_valid_external_method(class_fqn, method_name):
            external_method_fqn = f"{class_fqn}.{method_name}"
            if LOG_LEVEL >= 3:
                print(f"        [EXTERNAL] SUCCESS External method: {external_method_fqn}")
            return external_method_fqn
        
        if LOG_LEVEL >= 3:
            print(f"        [EXTERNAL] Invalid external method: {class_fqn}.{method_name}")
        return None
    
    def _is_valid_external_method(self, class_fqn: str, method_name: str) -> bool:
        """
        Validate if a method exists on an external class using heuristics.
        
        Since we don't have complete external library information,
        we use known patterns and common methods to validate.
        
        Args:
            class_fqn: FQN of the external class
            method_name: Method name to validate
            
        Returns:
            True if likely valid, False otherwise
        """
        # Framework-specific method validation
        if self._is_socketio_method(class_fqn, method_name):
            return True
        
        if self._is_threading_method(class_fqn, method_name):
            return True
        
        if self._is_common_object_method(method_name):
            return True
        
        if self._is_flask_method(class_fqn, method_name):
            return True
        
        if self._is_database_method(class_fqn, method_name):
            return True
        
        return False
    
    def _is_socketio_method(self, class_fqn: str, method_name: str) -> bool:
        """Check if method is a valid SocketIO method."""
        if 'SocketIO' not in class_fqn and 'socketio' not in class_fqn.lower():
            return False
        
        socketio_methods = {
            'emit', 'on', 'send', 'disconnect', 'join_room', 'leave_room',
            'close_room', 'rooms', 'get_session', 'save_session', 'session',
            'start_background_task', 'sleep'
        }
        
        return method_name in socketio_methods
    
    def _is_threading_method(self, class_fqn: str, method_name: str) -> bool:
        """Check if method is a valid threading method."""
        if 'threading' not in class_fqn.lower() and 'Thread' not in class_fqn:
            return False
        
        threading_methods = {
            'start', 'join', 'run', 'is_alive', 'daemon', 'name',
            'acquire', 'release', 'locked', 'wait', 'notify', 'notify_all'
        }
        
        return method_name in threading_methods
    
    def _is_flask_method(self, class_fqn: str, method_name: str) -> bool:
        """Check if method is a valid Flask method."""
        if 'flask' not in class_fqn.lower() and 'Flask' not in class_fqn:
            return False
        
        flask_methods = {
            'route', 'run', 'before_request', 'after_request', 'teardown_request',
            'errorhandler', 'url_for', 'redirect', 'abort', 'make_response',
            'jsonify', 'render_template', 'send_file', 'send_from_directory'
        }
        
        return method_name in flask_methods
    
    def _is_database_method(self, class_fqn: str, method_name: str) -> bool:
        """Check if method is a valid database-related method."""
        db_indicators = ['db', 'database', 'sql', 'mongo', 'redis', 'sqlite']
        
        if not any(indicator in class_fqn.lower() for indicator in db_indicators):
            return False
        
        db_methods = {
            'connect', 'disconnect', 'execute', 'query', 'commit', 'rollback',
            'close', 'cursor', 'fetchone', 'fetchall', 'fetchmany',
            'insert', 'update', 'delete', 'create', 'drop', 'select'
        }
        
        return method_name in db_methods
    
    def _is_common_object_method(self, method_name: str) -> bool:
        """Check if method is a common object method available on most classes."""
        common_methods = {
            '__init__', '__str__', '__repr__', '__call__', '__len__', '__iter__',
            '__enter__', '__exit__', '__getitem__', '__setitem__', '__delitem__',
            '__contains__', '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__',
            '__hash__', '__bool__', '__getattr__', '__setattr__', '__delattr__'
        }
        
        return method_name in common_methods
    
    def get_external_class_info(self, class_fqn: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an external class.
        
        Args:
            class_fqn: FQN of the external class
            
        Returns:
            External class information if available, None otherwise
        """
        return self.recon_data.get("external_classes", {}).get(class_fqn)
    
    def get_external_function_info(self, func_fqn: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an external function.
        
        Args:
            func_fqn: FQN of the external function
            
        Returns:
            External function information if available, None otherwise
        """
        return self.recon_data.get("external_functions", {}).get(func_fqn)
    
    def list_external_classes(self) -> list:
        """
        List all known external classes.
        
        Returns:
            List of external class FQNs
        """
        return list(self.recon_data.get("external_classes", {}).keys())
    
    def list_external_functions(self) -> list:
        """
        List all known external functions.
        
        Returns:
            List of external function FQNs
        """
        return list(self.recon_data.get("external_functions", {}).keys())
    
    def find_external_by_alias(self, alias: str) -> Optional[str]:
        """
        Find external class or function by local alias.
        
        Args:
            alias: Local alias to search for
            
        Returns:
            FQN if found, None otherwise
        """
        # Check external classes
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info.get("local_alias") == alias:
                return ext_class_fqn
        
        # Check external functions
        for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
            if ext_info.get("local_alias") == alias:
                return ext_func_fqn
        
        return None