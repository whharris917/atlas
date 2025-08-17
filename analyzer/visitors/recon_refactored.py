"""
Refactored Reconnaissance Visitor - Code Atlas

Main reconnaissance visitor that orchestrates specialized visitors for different concerns.
This replaces the monolithic ReconVisitor with a modular approach.

CRITICAL FIX: Added support for ast.AsyncFunctionDef to prevent recursive method body processing.
"""

import ast
from typing import Dict, List, Any, Optional

# Import specialized visitors
from .specialized.import_recon_visitor import ImportReconVisitor
from .specialized.class_recon_visitor import ClassReconVisitor
from .specialized.function_recon_visitor import FunctionReconVisitor
from .specialized.state_recon_visitor import StateReconVisitor

# Import utilities and base functionality
from ..utils.logger import AnalysisLogger, get_logger
from ..core.configuration import get_config
from ..type_inference import TypeInferenceEngine


class RefactoredReconVisitor(ast.NodeVisitor):
    """
    Refactored reconnaissance visitor that orchestrates specialized visitors.
    
    This replaces the monolithic ReconVisitor with a clean, modular approach
    while preserving all existing functionality.
    """
    
    def __init__(self, module_name: str):
        # Get global configuration and logger
        self.config = get_config()
        self.logger = get_logger()
        
        # Core setup
        self.module_name = module_name
        self.type_inference = TypeInferenceEngine({})  # Empty for recon pass
        
        # Initialize specialized visitors
        self.import_visitor = ImportReconVisitor(module_name, self.logger)
        self.class_visitor = ClassReconVisitor(module_name, self.logger)
        self.function_visitor = FunctionReconVisitor(module_name, self.logger)
        self.state_visitor = StateReconVisitor(module_name, self.logger, self.type_inference)
        
        # Results aggregation
        self.classes = []
        self.functions = {}
        self.state = {}
        self.external_classes = {}
        self.external_functions = {}
        
        self.logger.log(f"[RECON_INIT] Initialized refactored reconnaissance for module: {module_name}", 1)
    
    def visit_Import(self, node: ast.Import):
        """Process import statements using specialized visitor."""
        self.import_visitor.process_import(node)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports using specialized visitor."""
        self.import_visitor.process_import_from(node)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions using specialized visitor."""
        self.logger.log(f"[RECON_CLASS] Starting class analysis: {node.name}", 2)
        
        # Process class structure
        class_info = self.class_visitor.process_class_def(node)
        
        # Set context for other visitors
        class_fqn = class_info["fqn"]
        self.function_visitor.set_class_context(class_fqn)
        self.state_visitor.set_class_context(class_fqn)
        self.class_visitor.enter_class_context(class_fqn)
        
        try:
            # Process class body elements
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    self.visit_FunctionDef(child)
                elif isinstance(child, ast.AsyncFunctionDef):  # CRITICAL FIX: Handle async functions
                    self.visit_AsyncFunctionDef(child)
                elif isinstance(child, ast.Assign):
                    self.visit_Assign(child)
                elif isinstance(child, ast.AnnAssign):
                    self.visit_AnnAssign(child)
                else:
                    self.visit(child)
            
            # Handle special __init__ processing for attribute extraction
            init_method = self._find_init_method(node)
            if init_method:
                attributes = self.function_visitor.extract_init_attributes(init_method, self.type_inference)
                for attr_name, attr_info in attributes.items():
                    self.class_visitor.add_class_attribute(attr_name, attr_info)
        
        finally:
            # Clear context
            self.function_visitor.set_class_context(None)
            self.state_visitor.set_class_context(None)
            self.class_visitor.exit_class_context()
        
        self.logger.log(f"[RECON_CLASS] Completed class analysis: {node.name}", 2)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions using specialized visitor."""
        self.function_visitor.process_function_def(node)
        # Note: We don't recursively visit function bodies in reconnaissance pass
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Process async function definitions using specialized visitor.
        
        CRITICAL FIX: This method was missing, causing async methods to fall through
        to generic_visit() which recursively processed method bodies and treated
        local variables as class attributes.
        """
        # Treat async functions the same as regular functions for reconnaissance
        self.function_visitor.process_function_def(node)
        # IMPORTANT: Do NOT call self.generic_visit(node) to prevent visiting method bodies
    
    def visit_Assign(self, node: ast.Assign):
        """Process assignments using specialized visitor."""
        def class_attr_callback(name: str, info: Dict[str, Any]):
            self.class_visitor.add_class_attribute(name, info)
        
        self.state_visitor.process_assign(node, class_attr_callback)
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments using specialized visitor."""
        def class_attr_callback(name: str, info: Dict[str, Any]):
            self.class_visitor.add_class_attribute(name, info)
        
        self.state_visitor.process_ann_assign(node, class_attr_callback)
        self.generic_visit(node)
    
    def _find_init_method(self, class_node: ast.ClassDef) -> Optional[ast.FunctionDef]:
        """Find __init__ method in class definition."""
        for child in class_node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                return child
        return None
    
    def finalize_results(self):
        """Collect results from all specialized visitors."""
        self.logger.log("[RECON_FINALIZE] Collecting results from specialized visitors", 2)
        
        # Collect from specialized visitors
        self.classes = self.class_visitor.get_classes_data()
        self.functions = self.function_visitor.get_functions_data()
        self.state = self.state_visitor.get_state_data()
        
        external_data = self.import_visitor.get_external_data()
        self.external_classes = external_data["external_classes"]
        self.external_functions = external_data["external_functions"]
        
        # Log summary
        self.logger.log(f"[RECON_SUMMARY] Found {len(self.classes)} classes", 1)
        self.logger.log(f"[RECON_SUMMARY] Found {len(self.functions)} functions/methods", 1)
        self.logger.log(f"[RECON_SUMMARY] Found {len(self.state)} state variables", 1)
        self.logger.log(f"[RECON_SUMMARY] Found {len(self.external_classes)} external classes", 1)
        self.logger.log(f"[RECON_SUMMARY] Found {len(self.external_functions)} external functions", 1)


def run_reconnaissance_pass_refactored(python_files: List, recon_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Execute reconnaissance pass with refactored visitor.
    
    This function provides the same interface as the original reconnaissance pass
    but uses the new modular architecture.
    """
    logger = get_logger()
    logger.log("=== REFACTORED RECONNAISSANCE PASS START ===", 1)
    
    if recon_data is None:
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
        logger.log(f"=== Analyzing {py_file.name} ===", 1)
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = RefactoredReconVisitor(module_name)
            visitor.visit(tree)
            visitor.finalize_results()
            
            all_class_info.extend(visitor.classes)
            recon_data["functions"].update(visitor.functions)
            recon_data["state"].update(visitor.state)
            recon_data["external_classes"].update(visitor.external_classes)
            recon_data["external_functions"].update(visitor.external_functions)
            
            logger.log(f"  Found {len(visitor.classes)} classes", 1)
            logger.log(f"  Found {len(visitor.functions)} functions/methods", 1)
            logger.log(f"  Found {len(visitor.state)} state variables", 1)
            logger.log(f"  Found {len(visitor.external_classes)} external classes", 1)
            logger.log(f"  Found {len(visitor.external_functions)} external functions", 1)
        
        except Exception as e:
            logger.log(f"  ERROR: Failed to analyze {py_file.name}: {e}", 1)
            continue
    
    # Now process inheritance relationships and include attributes
    logger.log("\n=== PROCESSING INHERITANCE RELATIONSHIPS ===", 1)
    for class_info in all_class_info:
        class_fqn = class_info["fqn"]
        resolved_parents = []
        
        logger.log(f"Processing {class_fqn} with parents: {class_info['parents']}", 1)
        
        for parent in class_info["parents"]:
            logger.log(f"  Resolving parent: {parent}", 2)
            
            if "." not in parent:
                module_name = class_fqn.split(".")[0]
                candidate = f"{module_name}.{parent}"
                
                if any(c["fqn"] == candidate for c in all_class_info):
                    resolved_parents.append(candidate)
                    logger.log(f"    -> Resolved to: {candidate}", 2)
                else:
                    # Search across all modules
                    found = False
                    for collected_class in all_class_info:
                        if collected_class["fqn"].endswith(f".{parent}"):
                            resolved_parents.append(collected_class["fqn"])
                            logger.log(f"    -> Resolved to: {collected_class['fqn']}", 2)
                            found = True
                            break
                    
                    if not found:
                        logger.log(f"    -> Could not resolve parent: {parent}", 1)
                        resolved_parents.append(parent)
            else:
                resolved_parents.append(parent)
                logger.log(f"    -> Using qualified parent: {parent}", 2)
        
        # Update the class info with resolved parents and store in recon_data
        class_data = {
            "parents": resolved_parents,
            "attributes": class_info.get("attributes", {})
        }
        recon_data["classes"][class_fqn] = class_data
    
    logger.log("=== REFACTORED RECONNAISSANCE PASS COMPLETE ===", 1)
    return recon_data
