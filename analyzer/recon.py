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
from .logger import get_logger, create_context, AnalysisPhase, log_info, log_debug, log_trace, log_section_start, log_section_end


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
        
        # Logging context
        self.log_context = create_context("recon", AnalysisPhase.RECONNAISSANCE, file_name=f"{module_name}.py")
    
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
                log_debug(f"Added external class: {fqn} (alias: {local_name})", self.log_context.with_indent(1))
            else:
                # Likely a function
                self.external_functions[fqn] = {
                    "module": module_name, 
                    "name": imported_name,
                    "local_alias": local_name,
                    "return_type": None  # We don't know external function return types
                }
                log_debug(f"Added external function: {fqn} (alias: {local_name})", self.log_context.with_indent(1))
    
    def visit_Import(self, node: ast.Import):
        """Process imports and extract external library items."""
        for alias in node.names:
            # Handle direct module imports like: import threading
            if alias.name in EXTERNAL_LIBRARY_ALLOWLIST:
                # For direct module imports, we'll handle them during name resolution
                log_debug(f"Direct module import: {alias.name}", self.log_context.with_indent(1))
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports and extract external library items."""
        if node.module and node.module in EXTERNAL_LIBRARY_ALLOWLIST:
            log_debug(f"Processing from {node.module}", self.log_context.with_indent(1))
            for alias in node.names:
                if alias.name == '*':
                    log_debug(f"Warning: star import from {node.module} - cannot track individual items", self.log_context.with_indent(2))
                    continue
                
                self._process_import(node.module, alias.name, alias.asname)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions with inheritance capture and attribute cataloging."""
        class_fqn = f"{self.module_name}.{node.name}"
        
        class_context = self.log_context.with_function(f"visit_ClassDef:{node.name}")
        log_debug(f"Processing class: {node.name}", class_context)
        
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
        
        if parent_classes:
            log_debug(f"Found parent classes: {parent_classes}", class_context.with_indent(1))
        
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
        
        log_debug(f"Class {node.name} processed with {len(self.current_class_attributes)} attributes", class_context)
        
        # Restore previous context
        self.current_class = old_class
        self.current_class_attributes = old_attributes
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and extract class attributes from __init__."""
        if self.current_class:
            fqn = f"{self.current_class}.{node.name}"
        else:
            fqn = f"{self.module_name}.{node.name}"
        
        func_context = self.log_context.with_function(f"visit_FunctionDef:{node.name}")
        log_trace(f"Processing function: {fqn}", func_context)
        
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
                log_trace(f"Found return type: {return_type}", func_context.with_indent(1))
            except Exception:
                pass
        
        # Extract parameter types
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                    log_trace(f"Parameter {arg.arg}: {param_type}", func_context.with_indent(1))
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
        init_context = self.log_context.with_function("_extract_init_attributes")
        log_debug("Analyzing __init__ method for attributes", init_context)
        
        # First, extract parameter type hints from __init__ method
        param_types = {}
        for arg in init_node.args.args:
            if arg.arg != 'self' and arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                    log_trace(f"Parameter {arg.arg} has type hint: {param_type}", init_context.with_indent(1))
                except Exception as e:
                    log_trace(f"Failed to extract type for {arg.arg}: {e}", init_context.with_indent(1))
        
        log_trace(f"Found {len(param_types)} parameter type hints", init_context)
        
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
                            log_trace(f"{attr_name} = {stmt.value.id} : {resolved_type}", init_context.with_indent(1))
                        else:
                            # Fallback to value-based inference
                            resolved_type = self._infer_init_attribute_type(stmt.value)
                            log_trace(f"{attr_name} inferred as: {resolved_type}", init_context.with_indent(1))
                        
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
                            log_trace(f"{attr_name} : {type_annotation}", init_context.with_indent(1))
                        except Exception:
                            pass
                    
                    # If no annotation, try parameter type inference, then value inference
                    if not type_annotation:
                        if (stmt.value and isinstance(stmt.value, ast.Name) and 
                            stmt.value.id in param_types):
                            type_annotation = param_types[stmt.value.id]
                            log_trace(f"{attr_name} from param {stmt.value.id} : {type_annotation}", init_context.with_indent(1))
                        elif stmt.value:
                            type_annotation = self._infer_init_attribute_type(stmt.value)
                            log_trace(f"{attr_name} inferred as: {type_annotation}", init_context.with_indent(1))
                    
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
                    log_trace(f"State variable: {fqn} : {inferred_type}", self.log_context.with_indent(1))
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
            log_trace(f"Annotated state: {fqn} : {type_annotation}", self.log_context.with_indent(1))
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
    logger = get_logger()
    main_context = create_context("recon", AnalysisPhase.RECONNAISSANCE, "run_reconnaissance_pass")
    
    log_section_start("RECONNAISSANCE PASS", main_context)
    
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
        file_context = main_context.with_function(f"analyze_file").with_indent(1)
        log_info(f"Analyzing {py_file.name}", file_context)
        
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
            
            log_debug(f"Found {len(visitor.classes)} classes", file_context.with_indent(1))
            log_debug(f"Found {len(visitor.functions)} functions/methods", file_context.with_indent(1))
            log_debug(f"Found {len(visitor.state)} state variables", file_context.with_indent(1))
            log_debug(f"Found {len(visitor.external_classes)} external classes", file_context.with_indent(1))
            log_debug(f"Found {len(visitor.external_functions)} external functions", file_context.with_indent(1))
        
        except Exception as e:
            log_info(f"ERROR: Failed to analyze {py_file.name}: {e}", file_context.with_indent(1))
            continue
    
    # Now process inheritance relationships and include attributes
    inheritance_context = main_context.with_function("process_inheritance").with_indent(1)
    log_info("Processing inheritance relationships", inheritance_context)
    
    for class_info in all_class_info:
        class_fqn = class_info["fqn"]
        resolved_parents = []
        
        log_debug(f"Processing {class_fqn} with parents: {class_info['parents']}", inheritance_context.with_indent(1))
        
        for parent in class_info["parents"]:
            log_trace(f"Resolving parent: {parent}", inheritance_context.with_indent(2))
            
            if "." not in parent:
                module_name = class_fqn.split(".")[0]
                candidate = f"{module_name}.{parent}"
                
                if any(c["fqn"] == candidate for c in all_class_info):
                    resolved_parents.append(candidate)
                    log_trace(f"Resolved to: {candidate}", inheritance_context.with_indent(3))
                else:
                    # Search across all modules
                    found = False
                    for collected_class in all_class_info:
                        if collected_class["fqn"].endswith(f".{parent}"):
                            resolved_parents.append(collected_class["fqn"])
                            log_trace(f"Resolved to: {collected_class['fqn']}", inheritance_context.with_indent(3))
                            found = True
                            break
                    if not found:
                        log_trace(f"Could not resolve parent: {parent}", inheritance_context.with_indent(3))
            else:
                # Already fully qualified
                resolved_parents.append(parent)
                log_trace(f"Already qualified: {parent}", inheritance_context.with_indent(3))
        
        recon_data["classes"][class_fqn] = {
            "parents": resolved_parents,
            "attributes": class_info.get("attributes", {})
        }
    
    # Generate summary
    summary_context = main_context.with_function("generate_summary").with_indent(1)
    log_info("Total project inventory:", summary_context)
    log_info(f"Classes: {len(recon_data['classes'])}", summary_context.with_indent(1))
    log_info(f"Functions/Methods: {len(recon_data['functions'])}", summary_context.with_indent(1))
    log_info(f"State Variables: {len(recon_data['state'])}", summary_context.with_indent(1))
    log_info(f"External Classes: {len(recon_data['external_classes'])}", summary_context.with_indent(1))
    log_info(f"External Functions: {len(recon_data['external_functions'])}", summary_context.with_indent(1))
    
    # Detailed catalog logging (debug level)
    catalog_context = main_context.with_function("log_catalog").with_indent(1)
    log_debug("RECONNAISSANCE CATALOG", catalog_context)
    
    log_debug("Classes with inheritance and attributes:", catalog_context.with_indent(1))
    for class_fqn, class_info in recon_data["classes"].items():
        parents = class_info.get("parents", [])
        attributes = class_info.get("attributes", {})
        if parents:
            log_debug(f"{class_fqn} extends {parents}", catalog_context.with_indent(2))
        else:
            log_debug(f"{class_fqn}", catalog_context.with_indent(2))
        
        if attributes:
            log_trace("Attributes:", catalog_context.with_indent(3))
            for attr_name, attr_info in attributes.items():
                log_trace(f"{attr_name}: {attr_info.get('type', 'Unknown')}", catalog_context.with_indent(4))
        else:
            log_trace("No attributes detected", catalog_context.with_indent(3))
    
    log_debug("External Classes (from approved libraries):", catalog_context.with_indent(1))
    for ext_class_fqn, ext_info in recon_data["external_classes"].items():
        log_debug(f"{ext_class_fqn} (alias: {ext_info['local_alias']}) from {ext_info['module']}", catalog_context.with_indent(2))
    
    log_debug("External Functions (from approved libraries):", catalog_context.with_indent(1))
    for ext_func_fqn, ext_info in recon_data["external_functions"].items():
        log_debug(f"{ext_func_fqn} (alias: {ext_info['local_alias']}) from {ext_info['module']}", catalog_context.with_indent(2))
    
    log_debug("Functions/Methods with Parameter Types:", catalog_context.with_indent(1))
    for func_fqn in sorted(recon_data["functions"].keys()):
        func_info = recon_data["functions"][func_fqn]
        return_type = func_info.get("return_type", "None")
        param_types = func_info.get("param_types", {})
        param_str = ", ".join([f"{name}: {ptype}" for name, ptype in param_types.items()]) if param_types else "no typed params"
        log_trace(f"{func_fqn}({param_str}) -> {return_type}", catalog_context.with_indent(2))
    
    log_debug("State Variables:", catalog_context.with_indent(1))
    for state_fqn in sorted(recon_data["state"].keys()):
        state_info = recon_data["state"][state_fqn]
        log_trace(f"{state_fqn} : {state_info.get('type', 'Unknown')} (inferred: {state_info.get('inferred_from_value', False)})", catalog_context.with_indent(2))
    
    log_section_end("RECONNAISSANCE PASS", main_context)
    
    return recon_data
