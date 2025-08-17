"""
Chain Resolution Visitor - Code Atlas

Handles complex attribute chain resolution (e.g., self.manager.emit).
This visitor focuses on resolving multi-part name chains through attributes.
"""

from typing import Dict, List, Any, Optional

# Import LOG_LEVEL from utils - handle both relative and absolute imports
try:
    from ...utils import LOG_LEVEL
except ImportError:
    try:
        from utils import LOG_LEVEL
    except ImportError:
        # Fallback if utils not available
        LOG_LEVEL = 1


class ChainResolutionVisitor:
    """
    Handles complex attribute chain resolution.
    
    This visitor resolves multi-part names like 'self.manager.emit' by:
    1. Resolving the base name ('self')
    2. Walking through each attribute in the chain
    3. Using inheritance and type information for resolution
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def resolve(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a complex attribute chain.
        
        Args:
            name_parts: List of name components (e.g., ['self', 'manager', 'emit'])
            context: Resolution context
            
        Returns:
            Fully qualified name if resolved, None otherwise
        """
        if len(name_parts) < 2:
            if LOG_LEVEL >= 2:
                print(f"      [CHAIN] ERROR: Expected multi-part name, got: {name_parts}")
            return None
        
        if LOG_LEVEL >= 2:
            print(f"      [CHAIN] Resolving chain: {'.'.join(name_parts)}")
        
        # Import the simple resolver to resolve the base
        try:
            from .simple_resolution_visitor import SimpleResolutionVisitor
        except ImportError:
            # Handle relative import failure
            from simple_resolution_visitor import SimpleResolutionVisitor
        
        simple_resolver = SimpleResolutionVisitor(self.recon_data)
        
        # Step 1: Resolve the base name
        base_name = name_parts[0]
        if LOG_LEVEL >= 2:
            print(f"      [CHAIN] Resolving base: {base_name}")
        
        base_fqn = simple_resolver.resolve(base_name, context)
        if not base_fqn:
            if LOG_LEVEL >= 2:
                print(f"      [CHAIN] FAILED to resolve base: {base_name}")
            return None
        
        if LOG_LEVEL >= 2:
            print(f"      [CHAIN] Base resolved: {base_name} -> {base_fqn}")
        
        # Step 2: Walk through the attribute chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            if LOG_LEVEL >= 2:
                print(f"      [CHAIN] Step {i}: Resolving {current_fqn}.{attr}")
            
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                if LOG_LEVEL >= 2:
                    print(f"      [CHAIN] FAILED at step {i}: .{attr}")
                return None
            
            if LOG_LEVEL >= 2:
                print(f"      [CHAIN] Step {i} resolved: {current_fqn}")
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve an attribute in the context of a given FQN.
        
        This method handles:
        - State variable type resolution
        - Internal class method/attribute resolution  
        - External class method resolution
        - Inheritance chain resolution
        
        Args:
            context_fqn: The FQN of the context object
            attr: The attribute name to resolve
            context: Resolution context
            
        Returns:
            FQN of the resolved attribute, None if not found
        """
        candidate = f"{context_fqn}.{attr}"
        if LOG_LEVEL >= 3:
            print(f"        [ATTRIBUTE] Resolving: {context_fqn}.{attr}")
        
        # Strategy 1: State variable type resolution
        if context_fqn in self.recon_data.get("state", {}):
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] Context is state variable, resolving through type")
            
            state_type = self._get_state_type(context_fqn)
            if state_type:
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] State type resolved: {state_type}")
                return self._resolve_attribute(state_type, attr, context)
            else:
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] Could not resolve state type")
        
        # Strategy 2: Internal class resolution
        if context_fqn in self.recon_data.get("classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] Context is internal class")
            
            # Check direct method
            if candidate in self.recon_data.get("functions", {}):
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] SUCCESS Found direct method: {candidate}")
                return candidate
            
            # Check class attribute
            class_info = self.recon_data["classes"][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_type = class_attributes[attr].get("type")
                if attr_type and attr_type != "Unknown":
                    if LOG_LEVEL >= 3:
                        print(f"        [ATTRIBUTE] SUCCESS Found class attribute: {attr} of type {attr_type}")
                    
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        if LOG_LEVEL >= 3:
                            print(f"        [ATTRIBUTE] Attribute type resolved to: {resolved_type}")
                        return resolved_type
            
            # Check inheritance chain
            try:
                from .inheritance_resolution_visitor import InheritanceResolutionVisitor
            except ImportError:
                from inheritance_resolution_visitor import InheritanceResolutionVisitor
            
            inheritance_resolver = InheritanceResolutionVisitor(self.recon_data)
            inherited_result = inheritance_resolver.resolve_inherited_attribute(context_fqn, attr, context)
            if inherited_result:
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] SUCCESS Found in inheritance: {inherited_result}")
                return inherited_result
        
        # Strategy 3: External class resolution
        elif context_fqn in self.recon_data.get("external_classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] Context is external class")
            
            try:
                from .external_resolution_visitor import ExternalResolutionVisitor
            except ImportError:
                from external_resolution_visitor import ExternalResolutionVisitor
            
            external_resolver = ExternalResolutionVisitor(self.recon_data)
            external_result = external_resolver.resolve_external_method(context_fqn, attr)
            if external_result:
                if LOG_LEVEL >= 3:
                    print(f"        [ATTRIBUTE] SUCCESS Found external method: {external_result}")
                return external_result
        
        # Strategy 4: Direct candidate check (fallback)
        if candidate in self.recon_data.get("functions", {}):
            if LOG_LEVEL >= 3:
                print(f"        [ATTRIBUTE] SUCCESS Found direct function: {candidate}")
            return candidate
        
        if LOG_LEVEL >= 3:
            print(f"        [ATTRIBUTE] FAILED to resolve: {context_fqn}.{attr}")
        return None
    
    def _get_state_type(self, state_fqn: str) -> Optional[str]:
        """
        Get the type of a state variable.
        
        Args:
            state_fqn: FQN of the state variable
            
        Returns:
            Type FQN if available, None otherwise
        """
        state_info = self.recon_data.get("state", {}).get(state_fqn, {})
        return state_info.get("type")
    
    def _resolve_attribute_type(self, attr_type: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve attribute type string to FQN.
        
        This handles both internal and external class type resolution.
        
        Args:
            attr_type: Type string to resolve
            context: Resolution context
            
        Returns:
            Resolved type FQN, None if not found
        """
        if LOG_LEVEL >= 3:
            print(f"        [TYPE] Resolving attribute type: {attr_type}")
        
        # Check if it's already an FQN in our classes
        if attr_type in self.recon_data.get("classes", {}):
            if LOG_LEVEL >= 3:
                print(f"        [TYPE] Found internal class: {attr_type}")
            return attr_type
        
        # Check external classes
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info.get("local_alias") == attr_type:
                if LOG_LEVEL >= 3:
                    print(f"        [TYPE] Found external class: {ext_class_fqn}")
                return ext_class_fqn
        
        # Try resolving through import map
        import_map = context.get('import_map', {})
        if attr_type in import_map:
            resolved = import_map[attr_type]
            if LOG_LEVEL >= 3:
                print(f"        [TYPE] Resolved through imports: {attr_type} -> {resolved}")
            return resolved
        
        if LOG_LEVEL >= 3:
            print(f"        [TYPE] Could not resolve type: {attr_type}")
        return None
