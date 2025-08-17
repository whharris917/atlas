"""
Inheritance Resolution Visitor - Code Atlas

Handles name resolution through inheritance chains.
This visitor focuses on resolving methods and attributes through class inheritance.
"""

from typing import Dict, Any, Optional

from ...utils import LOG_LEVEL


class InheritanceResolutionVisitor:
    """
    Handles name resolution through inheritance chains.
    
    This visitor resolves methods and attributes by walking up
    the inheritance hierarchy to find the defining class.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def resolve_inherited_attribute(self, class_fqn: str, attr_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve method or attribute through inheritance chain.
        
        Args:
            class_fqn: FQN of the class to search from
            attr_name: Name of the attribute/method to find
            context: Resolution context
            
        Returns:
            FQN of the resolved attribute, None if not found
        """
        if LOG_LEVEL >= 3:
            print(f"        [INHERITANCE] Checking inheritance chain for {class_fqn}.{attr_name}")
        
        if class_fqn not in self.recon_data.get("classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [INHERITANCE] Class {class_fqn} not found in catalog")
            return None
        
        class_info = self.recon_data["classes"][class_fqn]
        parents = class_info.get("parents", [])
        
        if LOG_LEVEL >= 3:
            print(f"        [INHERITANCE] Parents of {class_fqn}: {parents}")
        
        # Search through each parent class
        for parent_fqn in parents:
            if LOG_LEVEL >= 3:
                print(f"        [INHERITANCE] Checking parent: {parent_fqn}")
            
            # Strategy 1: Look for method in parent
            method_candidate = f"{parent_fqn}.{attr_name}"
            if method_candidate in self.recon_data.get("functions", {}):
                if LOG_LEVEL >= 3:
                    print(f"        [INHERITANCE] SUCCESS Found inherited method: {method_candidate}")
                return method_candidate
            
            # Strategy 2: Look for attribute in parent
            if parent_fqn in self.recon_data.get("classes", {}):
                parent_info = self.recon_data["classes"][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                
                if attr_name in parent_attributes:
                    attr_type = parent_attributes[attr_name].get("type")
                    if attr_type and attr_type != "Unknown":
                        if LOG_LEVEL >= 3:
                            print(f"        [INHERITANCE] SUCCESS Found inherited attribute: {attr_name} of type {attr_type}")
                        
                        # Resolve the attribute type to its FQN
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            if LOG_LEVEL >= 3:
                                print(f"        [INHERITANCE] Attribute type resolved to: {resolved_type}")
                            return resolved_type
            
            # Strategy 3: Recursive search up the inheritance chain
            inherited = self.resolve_inherited_attribute(parent_fqn, attr_name, context)
            if inherited:
                if LOG_LEVEL >= 3:
                    print(f"        [INHERITANCE] SUCCESS Found in grandparent: {inherited}")
                return inherited
        
        if LOG_LEVEL >= 3:
            print(f"        [INHERITANCE] Method/attribute {attr_name} not found in inheritance chain")
        return None
    
    def _resolve_attribute_type(self, attr_type: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve attribute type string to FQN, including external classes.
        
        Args:
            attr_type: Type string to resolve
            context: Resolution context
            
        Returns:
            Resolved type FQN, None if not found
        """
        if LOG_LEVEL >= 3:
            print(f"        [TYPE] Resolving attribute type: {attr_type}")
        
        # Strategy 1: Check if it's already an FQN in our classes
        if attr_type in self.recon_data.get("classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [TYPE] Found internal class: {attr_type}")
            return attr_type
        
        # Strategy 2: Check external classes
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info.get("local_alias") == attr_type:
                if LOG_LEVEL >= 3:
                    print(f"        [TYPE] Found external class: {ext_class_fqn}")
                return ext_class_fqn
        
        # Strategy 3: Try resolving through import map
        import_map = context.get('import_map', {})
        if attr_type in import_map:
            resolved = import_map[attr_type]
            if LOG_LEVEL >= 3:
                print(f"        [TYPE] Resolved through imports: {attr_type} -> {resolved}")
            return resolved
        
        # Strategy 4: Check if it matches a known type pattern
        if self._is_known_type_pattern(attr_type):
            if LOG_LEVEL >= 3:
                print(f"        [TYPE] Recognized as known type pattern: {attr_type}")
            return attr_type
        
        if LOG_LEVEL >= 3:
            print(f"        [TYPE] Could not resolve type: {attr_type}")
        return None
    
    def _is_known_type_pattern(self, type_str: str) -> bool:
        """
        Check if a type string matches known patterns.
        
        This helps identify built-in types or common patterns
        that should be considered valid even if not in our data.
        
        Args:
            type_str: Type string to check
            
        Returns:
            True if recognized pattern, False otherwise
        """
        # Built-in types
        builtin_types = {
            'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
            'None', 'object', 'type', 'bytes', 'bytearray'
        }
        
        if type_str in builtin_types:
            return True
        
        # Generic types (List[T], Dict[K,V], etc.)
        if any(type_str.startswith(prefix) for prefix in ['List[', 'Dict[', 'Tuple[', 'Set[', 'Optional[']):
            return True
        
        # Module-qualified types (e.g., typing.List, collections.defaultdict)
        if '.' in type_str:
            module_part = type_str.split('.')[0]
            common_modules = {'typing', 'collections', 'abc', 'enum', 'dataclasses'}
            if module_part in common_modules:
                return True
        
        return False
    
    def get_inheritance_chain(self, class_fqn: str) -> list:
        """
        Get the complete inheritance chain for a class.
        
        Args:
            class_fqn: FQN of the class
            
        Returns:
            List of FQNs in inheritance order (immediate parent first)
        """
        if class_fqn not in self.recon_data.get("classes", {}):
            return []
        
        chain = []
        visited = set()  # Prevent infinite loops in case of circular inheritance
        
        def _collect_parents(current_class):
            if current_class in visited or current_class not in self.recon_data.get("classes", {}):
                return
            
            visited.add(current_class)
            class_info = self.recon_data["classes"][current_class]
            parents = class_info.get("parents", [])
            
            for parent in parents:
                if parent not in chain:
                    chain.append(parent)
                _collect_parents(parent)
        
        _collect_parents(class_fqn)
        return chain
    
    def find_method_definition(self, class_fqn: str, method_name: str) -> Optional[str]:
        """
        Find where a method is actually defined in the inheritance chain.
        
        Args:
            class_fqn: FQN of the class to search from
            method_name: Name of the method to find
            
        Returns:
            FQN of the class where the method is defined, None if not found
        """
        # Check the class itself first
        method_candidate = f"{class_fqn}.{method_name}"
        if method_candidate in self.recon_data.get("functions", {}):
            return class_fqn
        
        # Check the inheritance chain
        inheritance_chain = self.get_inheritance_chain(class_fqn)
        for parent_class in inheritance_chain:
            parent_method = f"{parent_class}.{method_name}"
            if parent_method in self.recon_data.get("functions", {}):
                return parent_class
        
        return None
