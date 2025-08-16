"""
Reconnaissance Pass - Code Atlas

Contains the ReconVisitor and logic for the first pass of the analysis,
which catalogs all definitions (classes, functions, etc.) in the project.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional
from .type_inference import TypeInferenceEngine
from .utils import EXTERNAL_LIBRARY_ALLOWLIST

class ReconVisitor(ast.NodeVisitor):
    """Enhanced reconnaissance visitor with inheritance tracking, attribute cataloging, parameter type extraction, and external library support."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.current_class = None
        self.current_class_attributes = {}
        self.type_inference = TypeInferenceEngine({})  # Empty for recon pass
        
        self.classes = []
        self.functions = {}
        self.state = {}
        self.external_classes = {}  # Track external classes from imports
        self.external_functions = {}  # Track external functions from imports
    
    def _is_camel_case(self, name: str) -> bool:
        """Check if a name follows CamelCase convention (likely a class)."""
        return name and name[0].isupper() and '_' not in name and not name.isupper()
    
    def _process_import(self, module_name: str, imported_name: str, alias: Optional[str] = None):
        """Process an import and add to external catalogs if from approved library."""
        if module_name in EXTERNAL_LIBRARY_ALLOWLIST:
            fqn = f"{module_name}.{imported_name}"
            local_name = alias if alias else imported_name
            
            if self._is_camel_case(imported_name):
                # Likely a class
                self.external_classes[fqn] = {
                    "module": module_name,
                    "name": imported_name,
                    "local_alias": local_name
                }
                print(f"    [EXTERNAL_CLASS] Added: {fqn} (alias: {local_name})")
            else:
                # Likely a function
                self.external_functions[fqn] = {
                    "module": module_name, 
                    "name": imported_name,
                    "local_alias": local_name,
                    "return_type": None  # We don't know external function return types
                }
                print(f"    [EXTERNAL_FUNCTION] Added: {fqn} (alias: {local_name})")
    
    def visit_Import(self, node: ast.Import):
        """Process imports and extract external library items."""
        for alias in node.names:
            # Handle direct module imports like: import threading
            if alias.name in EXTERNAL_LIBRARY_ALLOWLIST:
                # For direct module imports, we'll handle them during name resolution
                print(f"    [EXTERNAL_MODULE] Direct import: {alias.name}")
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports and extract external library items."""
        if node.module and node.module in EXTERNAL_LIBRARY_ALLOWLIST:
            print(f"    [EXTERNAL_IMPORT] Processing from {node.module}")
            for alias in node.names:
                if alias.name == '*':
                    print(f"    [EXTERNAL_IMPORT] Warning: star import from {node.module} - cannot track individual items")
                    continue
                
                self._process_import(node.module, alias.name, alias.asname)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions with inheritance capture and attribute cataloging."""
        class_fqn = f"{self.module_name}.{node.name}"
        
        # Capture inheritance information
        parent_classes = []
        for base in node.bases:
            try:
                if isinstance(base, ast.Name):
                    # Simple inheritance: class Child(Parent)
                    parent_classes.append(base.id)
                elif isinstance(base, ast.Attribute):
                    # Module inheritance: class Child(module.Parent)
                    base_parts = []
                    current = base
                    while isinstance(current, ast.Attribute):
                        base_parts.insert(0, current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        base_parts.insert(0, current.id)
                        parent_classes.append(".".join(base_parts))
            except Exception:
                pass
        
        # Initialize attribute tracking for this class
        old_class = self.current_class
        old_attributes = self.current_class_attributes
        self.current_class = class_fqn
        self.current_class_attributes = {}
        
        # Process all class body elements
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self.visit_FunctionDef(child)
            elif isinstance(child, ast.Assign):
                self.visit_Assign(child)
            elif isinstance(child, ast.AnnAssign):
                self.visit_AnnAssign(child)
        
        # Store class with inheritance info and attributes
        self.classes.append({
            "fqn": class_fqn,
            "parents": parent_classes,
            "attributes": self.current_class_attributes.copy()
        })
        
        # Restore previous context
        self.current_class = old_class
        self.current_class_attributes = old_attributes
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and extract class attributes from __init__."""
        if self.current_class:
            fqn = f"{self.current_class}.{node.name}"
        else:
            fqn = f"{self.module_name}.{node.name}"
        
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                pass
        
        # Extract parameter types
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                except Exception:
                    pass
        
        # Store function with return type and parameter types
        self.functions[fqn] = {
            "return_type": return_type,
            "param_types": param_types
        }
        
        # Special handling for __init__ methods to extract attribute assignments
        if self.current_class and node.name == "__init__":
            self._extract_init_attributes(node)
    
    def _extract_init_attributes(self, init_node: ast.FunctionDef):
        """Extract class attribute assignments from __init__ method with parameter type inference."""
        # First, extract parameter type hints from __init__ method
        param_types = {}
        for arg in init_node.args.args:
            if arg.arg != 'self' and arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                    print(f"        [INIT_PARAM] Parameter {arg.arg} has type hint: {param_type}")
                except Exception as e:
                    print(f"        [INIT_PARAM] Failed to extract type for {arg.arg}: {e}")
        
        print(f"        [INIT_ANALYSIS] Found {len(param_types)} parameter type hints")
        
        for stmt in ast.walk(init_node):
            if isinstance(stmt, ast.Assign):
                # Handle self.attr = value assignments
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and 
                        isinstance(target.value, ast.Name) and 
                        target.value.id == "self"):
                        
                        attr_name = target.attr
                        resolved_type = None
                        
                        # Check if assignment is from a parameter with type hint
                        if (isinstance(stmt.value, ast.Name) and 
                            stmt.value.id in param_types):
                            resolved_type = param_types[stmt.value.id]
                            print(f"        [ATTR_FROM_PARAM] {attr_name} = {stmt.value.id} : {resolved_type}")
                        else:
                            # Fallback to value-based inference
                            resolved_type = self._infer_init_attribute_type(stmt.value)
                            print(f"        [ATTR_FROM_VALUE] {attr_name} inferred as: {resolved_type}")
                        
                        self.current_class_attributes[attr_name] = {
                            "type": resolved_type or "Unknown"
                        }
            
            elif isinstance(stmt, ast.AnnAssign):
                # Handle self.attr: Type = value assignments
                if (isinstance(stmt.target, ast.Attribute) and 
                    isinstance(stmt.target.value, ast.Name) and 
                    stmt.target.value.id == "self"):
                    
                    attr_name = stmt.target.attr
                    type_annotation = None
                    
                    if stmt.annotation:
                        try:
                            type_annotation = ast.unparse(stmt.annotation)
                            print(f"        [ATTR_ANNOTATED] {attr_name} : {type_annotation}")
                        except Exception:
                            pass
                    
                    # If no annotation, try parameter type inference, then value inference
                    if not type_annotation:
                        if (stmt.value and isinstance(stmt.value, ast.Name) and 
                            stmt.value.id in param_types):
                            type_annotation = param_types[stmt.value.id]
                            print(f"        [ATTR_FROM_PARAM_ANN] {attr_name} from param {stmt.value.id} : {type_annotation}")
                        elif stmt.value:
                            type_annotation = self._infer_init_attribute_type(stmt.value)
                            print(f"        [ATTR_FROM_VALUE_ANN] {attr_name} inferred as: {type_annotation}")
                    
                    self.current_class_attributes[attr_name] = {
                        "type": type_annotation or "Unknown"
                    }
    
    def _infer_init_attribute_type(self, value_node: ast.AST) -> str:
        """Infer type of attribute from its initialization value in __init__."""
        if isinstance(value_node, ast.Call):
            # Direct instantiation: self.attr = ClassName()
            if isinstance(value_node.func, ast.Name):
                return value_node.func.id
            elif isinstance(value_node.func, ast.Attribute):
                # Module.ClassName() pattern
                parts = []
                current = value_node.func
                while isinstance(current, ast.Attribute):
                    parts.insert(0, current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.insert(0, current.id)
                    return ".".join(parts)
        
        elif isinstance(value_node, ast.Name):
            # Assignment from parameter: self.attr = param
            return value_node.id
        
        elif isinstance(value_node, ast.Constant):
            # Literal assignment: self.attr = "string" or self.attr = 42
            if isinstance(value_node.value, str):
                return "str"
            elif isinstance(value_node.value, int):
                return "int"
            elif isinstance(value_node.value, float):
                return "float"
            elif isinstance(value_node.value, bool):
                return "bool"
        
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Subscript):
            # Handle subscript access like: self.attr = some_dict[key]
            try:
                return ast.unparse(value_node)
            except Exception:
                pass
        
        return None
    
    def visit_Assign(self, node: ast.Assign):
        """Process assignments for state variables and class attributes."""
        if self.current_class is None:
            # Module level assignments - state variables
            for target in node.targets:
                if isinstance(target, ast.Name):
                    fqn = f"{self.module_name}.{target.id}"
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    self.state[fqn] = {
                        "type": inferred_type,
                        "inferred_from_value": bool(inferred_type)
                    }
        else:
            # Class level assignments - class attributes
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Simple assignment: self.attr = value
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    self.current_class_attributes[target.id] = {
                        "type": inferred_type or "Unknown"
                    }
                elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    # Self assignment: self.attr = value
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    self.current_class_attributes[target.attr] = {
                        "type": inferred_type or "Unknown"
                    }
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments for class attributes and state variables."""
        if self.current_class is None and isinstance(node.target, ast.Name):
            # Module level annotated assignment
            fqn = f"{self.module_name}.{node.target.id}"
            type_annotation = None
            if node.annotation:
                try:
                    type_annotation = ast.unparse(node.annotation)
                except Exception:
                    pass
            
            self.state[fqn] = {
                "type": type_annotation,
                "inferred_from_value": False
            }
        elif self.current_class is not None:
            # Class level annotated assignment
            if isinstance(node.target, ast.Name):
                # Direct assignment: attr: Type = value
                type_annotation = None
                if node.annotation:
                    try:
                        type_annotation = ast.unparse(node.annotation)
                    except Exception:
                        pass
                
                self.current_class_attributes[node.target.id] = {
                    "type": type_annotation or "Unknown"
                }
            elif isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name) and node.target.value.id == "self":
                # Self assignment: self.attr: Type = value
                type_annotation = None
                if node.annotation:
                    try:
                        type_annotation = ast.unparse(node.annotation)
                    except Exception:
                        pass
                
                self.current_class_attributes[node.target.attr] = {
                    "type": type_annotation or "Unknown"
                }
                
def run_reconnaissance_pass(python_files: List[pathlib.Path]) -> Dict[str, Any]:
    """Execute reconnaissance pass with inheritance tracking, attribute cataloging, parameter type extraction, and external library support."""
    print("=== RECONNAISSANCE PASS START ===")
    
    recon_data = {
        "classes": {},  # Internal classes
        "functions": {},  # Internal functions
        "state": {},  # Internal state
        "external_classes": {},  # External classes from approved libraries
        "external_functions": {}  # External functions from approved libraries
    }
    
    # Collect all class information first
    all_class_info = []
    
    for py_file in python_files:
        print(f"=== Analyzing {py_file.name} ===")
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = ReconVisitor(module_name)
            visitor.visit(tree)
            
            all_class_info.extend(visitor.classes)
            recon_data["functions"].update(visitor.functions)
            recon_data["state"].update(visitor.state)
            recon_data["external_classes"].update(visitor.external_classes)
            recon_data["external_functions"].update(visitor.external_functions)
            
            print(f"  Found {len(visitor.classes)} classes")
            print(f"  Found {len(visitor.functions)} functions/methods")
            print(f"  Found {len(visitor.state)} state variables")
            print(f"  Found {len(visitor.external_classes)} external classes")
            print(f"  Found {len(visitor.external_functions)} external functions")
        
        except Exception as e:
            print(f"  ERROR: Failed to analyze {py_file.name}: {e}")
            continue
    
    # Now process inheritance relationships and include attributes
    print("\n=== PROCESSING INHERITANCE RELATIONSHIPS ===")
    for class_info in all_class_info:
        class_fqn = class_info["fqn"]
        resolved_parents = []
        
        print(f"Processing {class_fqn} with parents: {class_info['parents']}")
        
        for parent in class_info["parents"]:
            print(f"  Resolving parent: {parent}")
            
            if "." not in parent:
                module_name = class_fqn.split(".")[0]
                candidate = f"{module_name}.{parent}"
                
                if any(c["fqn"] == candidate for c in all_class_info):
                    resolved_parents.append(candidate)
                    print(f"    -> Resolved to: {candidate}")
                else:
                    # Search across all modules
                    found = False
                    for collected_class in all_class_info:
                        if collected_class["fqn"].endswith(f".{parent}"):
                            resolved_parents.append(collected_class["fqn"])
                            print(f"    -> Resolved to: {collected_class['fqn']}")
                            found = True
                            break
                    if not found:
                        print(f"    -> Could not resolve parent: {parent}")
            else:
                # Already fully qualified
                resolved_parents.append(parent)
                print(f"    -> Already qualified: {parent}")
        
        recon_data["classes"][class_fqn] = {
            "parents": resolved_parents,
            "attributes": class_info.get("attributes", {})
        }
    
    print("=== RECONNAISSANCE PASS COMPLETE ===")
    print(f"Total project inventory:")
    print(f"  Classes: {len(recon_data['classes'])}")
    print(f"  Functions/Methods: {len(recon_data['functions'])}")
    print(f"  State Variables: {len(recon_data['state'])}")
    print(f"  External Classes: {len(recon_data['external_classes'])}")
    print(f"  External Functions: {len(recon_data['external_functions'])}")
    print()
    
    # Log the complete catalog for debugging
    print("=== RECONNAISSANCE CATALOG ===")
    print("Classes with inheritance and attributes:")
    for class_fqn, class_info in recon_data["classes"].items():
        parents = class_info.get("parents", [])
        attributes = class_info.get("attributes", {})
        if parents:
            print(f"  {class_fqn} extends {parents}")
        else:
            print(f"  {class_fqn}")
        
        if attributes:
            print(f"    Attributes:")
            for attr_name, attr_info in attributes.items():
                print(f"      {attr_name}: {attr_info.get('type', 'Unknown')}")
        else:
            print(f"    No attributes detected")
    
    print("\nExternal Classes (from approved libraries):")
    for ext_class_fqn, ext_info in recon_data["external_classes"].items():
        print(f"  {ext_class_fqn} (alias: {ext_info['local_alias']}) from {ext_info['module']}")
    
    print("\nExternal Functions (from approved libraries):")
    for ext_func_fqn, ext_info in recon_data["external_functions"].items():
        print(f"  {ext_func_fqn} (alias: {ext_info['local_alias']}) from {ext_info['module']}")
    
    print("\nFunctions/Methods with Parameter Types:")
    for func_fqn in sorted(recon_data["functions"].keys()):
        func_info = recon_data["functions"][func_fqn]
        return_type = func_info.get("return_type", "None")
        param_types = func_info.get("param_types", {})
        param_str = ", ".join([f"{name}: {ptype}" for name, ptype in param_types.items()]) if param_types else "no typed params"
        print(f"  {func_fqn}({param_str}) -> {return_type}")
    
    print("\nState Variables:")
    for state_fqn in sorted(recon_data["state"].keys()):
        state_info = recon_data["state"][state_fqn]
        print(f"  {state_fqn} : {state_info.get('type', 'Unknown')} (inferred: {state_info.get('inferred_from_value', False)})")
    print("=== CATALOG END ===")
    print()
    
    return recon_data
