"""
Refactored Analysis Visitor - Code Atlas

Main analysis visitor that orchestrates specialized visitors for different concerns.
This replaces the monolithic AnalysisVisitor with a modular approach.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional

# Import core components
from .base import BaseVisitor
from .specialized.emit_visitor import EmitVisitor
from .specialized.call_visitor import CallVisitor
from .specialized.assignment_visitor import AssignmentVisitor

# Import utilities
from ..utils.logger import AnalysisLogger, get_logger
from ..utils.naming import generate_function_fqn, generate_class_fqn
from ..core.configuration import get_config

# Import existing components (to be refactored later)
from ..resolver_compat import create_name_resolver
from ..type_inference import TypeInferenceEngine
from ..symbol_table import SymbolTableManager
from ..code_checker import CodeStandardChecker


class RefactoredAnalysisVisitor(BaseVisitor):
    """
    Refactored analysis visitor that orchestrates specialized visitors.
    
    This replaces the monolithic AnalysisVisitor with a clean, modular approach
    while preserving all existing functionality.
    """
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str):
        # Get global configuration and logger
        self.config = get_config()
        logger = get_logger()
        
        # Initialize base visitor
        super().__init__(recon_data, module_name, logger)
        
        # Core analysis components - FORCE refactored resolver
        self.name_resolver = create_name_resolver(recon_data, use_refactored=True)
        
        # Debug: Verify we're using refactored
        if hasattr(self.name_resolver, 'get_implementation_info'):
            impl_info = self.name_resolver.get_implementation_info()
            self.logger.log(f"[RESOLVER] Using implementation: {impl_info['implementation']}", 1)
        
        self.type_inference = TypeInferenceEngine(recon_data)
        self.symbol_manager = SymbolTableManager()
        self.code_checker = CodeStandardChecker()
        
        # Context tracking
        self.current_function_report = None
        self.resolution_cache = {}
        
        # Module report structure (MUST be defined before creating visitors)
        self.module_report = {
            "file_path": f"{module_name}.py",
            "module_docstring": None,
            "imports": {},
            "classes": [],
            "functions": [],
            "module_state": []
        }
        
        # Initialize specialized visitors immediately (not just when needed)
        self.emit_visitor = EmitVisitor(
            self.name_resolver,
            None,  # Will be updated when we have a function report
            self.logger
        )
        
        self.call_visitor = CallVisitor(
            self.name_resolver,
            self.recon_data,
            None,  # Will be updated when we have a function report
            self.resolution_cache,
            self.emit_visitor,
            self.logger
        )
        
        self.assignment_visitor = AssignmentVisitor(
            self.name_resolver,
            self.type_inference,
            self.symbol_manager,
            None,  # Will be updated when we have a function report
            self.module_report,  # NOW this exists!
            self.logger
        )
    
    def _update_specialized_visitors_context(self):
        """Update specialized visitors with current function context."""
        # Create new visitor instances with current context
        # This ensures they have the correct function_report reference
        
        self.emit_visitor = EmitVisitor(
            self.name_resolver,
            self.current_function_report,  # Pass current function report
            self.logger
        )
        
        self.call_visitor = CallVisitor(
            self.name_resolver,
            self.recon_data,
            self.current_function_report,  # Pass current function report
            self.resolution_cache,
            self.emit_visitor,
            self.logger
        )
        
        self.assignment_visitor = AssignmentVisitor(
            self.name_resolver,
            self.type_inference,
            self.symbol_manager,
            self.current_function_report,  # Pass current function report
            self.module_report,
            self.logger
        )
    
    def visit_Module(self, node: ast.Module):
        """Process module and extract docstring."""
        self.logger.log("=== Starting Module Analysis ===")
        
        # Extract module docstring
        self.module_report["module_docstring"] = self.extract_docstring(node)
        
        # Process module body
        self.generic_visit(node)
        
        # Finalize module report
        self.module_report["imports"] = self.import_map.copy()
        self.logger.log("=== Module Analysis Complete ===")
    
    def visit_Import(self, node: ast.Import):
        """Process import statements."""
        self.process_imports(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from-import statements."""
        self.process_from_imports(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        class_fqn = generate_class_fqn(self.module_name, node.name)
        self.logger.log(f"[CLASS] Analyzing class: {node.name}", 1)
        
        # Create class report
        class_report = {
            "name": node.name,
            "docstring": self.extract_docstring(node),
            "methods": []
        }
        
        # Enter class context
        old_class = self.enter_class_context(node.name)
        self.symbol_manager.enter_class_scope()
        
        try:
            # Process class body
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_report = self._analyze_function(child)
                    class_report["methods"].append(method_report)
                else:
                    self.visit(child)
        
        finally:
            # Exit class context
            self.exit_class_context(old_class)
            self.symbol_manager.exit_class_scope()
        
        self.module_report["classes"].append(class_report)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and handle nested functions properly."""
        if not self.current_class:
            # Top-level function
            self.logger.log(f"[FUNCTION] Analyzing function: {node.name}", 1)
            function_report = self._analyze_function(node)
            self.module_report["functions"].append(function_report)
        elif not self.current_function_report:
            # Class method (not nested) - will be handled by visit_ClassDef
            pass
        else:
            # Nested function - process within current function context
            self.logger.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
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
        # Generate function FQN
        if self.current_class:
            function_fqn = f"{self.current_class}.{node.name}"
        else:
            function_fqn = f"{self.module_name}.{node.name}"
        
        self.logger.log_function_analysis_start(function_fqn)
        
        # Create function report
        function_report = {
            "name": node.name,
            "args": self.get_function_args(node),
            "docstring": self.extract_docstring(node),
            "calls": [],
            "instantiations": [],
            "accessed_state": [],
            "decorators": self.extract_decorators(node),
            "emit_contexts": {}
        }
        
        # Check for code standard violations
        if self.config.report_missing_type_hints:
            violations = self.code_checker.check_function_type_hints(node, function_fqn)
            if violations:
                self.logger.log(f"[CODE_QUALITY] Found {len(violations)} violations in {function_fqn}", 3)
        
        # Set up function context
        old_report = self.current_function_report
        old_function_context = self.enter_function_context(node.name)
        self.current_function_report = function_report
        self.symbol_manager.enter_function_scope()
        self.resolution_cache = {}
        
        # Update specialized visitors with current context
        self._update_specialized_visitors_context()
        
        try:
            # Populate symbol table from arguments
            self._populate_symbols_from_args(node.args)
            
            # Analyze function body
            for child in node.body:
                self._visit_with_nested_handling(child)
        
        finally:
            # Restore context
            self.current_function_report = old_report
            self.exit_function_context(old_function_context)
            # Note: SymbolTableManager doesn't have exit_function_scope method
            # It only tracks scopes internally
        
        # Clean up empty emit_contexts to keep JSON clean
        if not function_report.get("emit_contexts"):
            function_report.pop("emit_contexts", None)
        
        self.logger.log_function_analysis_complete(function_fqn, function_report)
        return function_report
    
    def _populate_symbols_from_args(self, args: ast.arguments):
        """Populate symbol table from function arguments with enhanced type resolution."""
        context = self.get_current_context()
        context.update({
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        })
        
        self.logger.log(f"[ARG_PROCESSING] Processing {len(args.args)} arguments", 3)
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.current_function_fqn and self.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                self.logger.log(f"[ARG_PROCESSING] Found parameter types in recon data: {param_types_from_recon}", 4)
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
            
            self._process_function_argument(arg, param_types_from_recon, context)
    
    def _process_function_argument(self, arg: ast.arg, param_types_from_recon: Dict[str, str], context: Dict[str, Any]):
        """Process individual function argument for type resolution."""
        if arg.annotation:
            # Type hint present - process normally
            try:
                type_parts = self.name_resolver.extract_name_parts(arg.annotation)
                if type_parts:
                    self.logger.log(f"[ARG_TYPE] Processing type annotation for {arg.arg}: {'.'.join(type_parts)}", 4)
                    resolved_type = self._cached_resolve_name(type_parts, context)
                    if resolved_type:
                        self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                        self.logger.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type}", 4)
                    else:
                        self.logger.log(f"[ARG_TYPE] FAILED Could not resolve type annotation for {arg.arg}", 4)
            except Exception as e:
                self.logger.log(f"[ARG_TYPE] ERROR processing type for {arg.arg}: {e}", 4)
        
        elif arg.arg in param_types_from_recon:
            # No direct annotation but we have type info from recon
            param_type_str = param_types_from_recon[arg.arg]
            self.logger.log(f"[ARG_TYPE] Using recon data type for {arg.arg}: {param_type_str}", 4)
            
            try:
                # Parse the type string and resolve it
                import ast as ast_module
                type_node = ast_module.parse(param_type_str, mode='eval').body
                type_parts = self.name_resolver.extract_name_parts(type_node)
                if type_parts:
                    resolved_type = self._cached_resolve_name(type_parts, context)
                    if resolved_type:
                        self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                        self.logger.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type} (from recon)", 4)
                    else:
                        # Fallback to the original string
                        self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        self.logger.log(f"[ARG_TYPE] FALLBACK {arg.arg} : {param_type_str} (from recon)", 4)
                else:
                    # Simple type, use as-is
                    self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                    self.logger.log(f"[ARG_TYPE] SIMPLE {arg.arg} : {param_type_str} (from recon)", 4)
            except Exception as e:
                self.logger.log(f"[ARG_TYPE] ERROR processing recon type for {arg.arg}: {e}", 4)
                # Still use the string as fallback
                self.symbol_manager.update_variable_type(arg.arg, param_type_str)
        else:
            # Missing type hint and no recon data
            self.logger.log(f"[ARG_TYPE] No type hint or recon data for {arg.arg}", 4)
    
    def _visit_with_nested_handling(self, node: ast.AST):
        """Handle nested functions properly."""
        if isinstance(node, ast.FunctionDef) and self.current_function_report:
            self.logger.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
            self.symbol_manager.enter_nested_scope()
            try:
                self._populate_symbols_from_args(node.args)
                for child in node.body:
                    self.visit(child)
            finally:
                self.symbol_manager.exit_nested_scope()
        else:
            self.visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Process function calls using the specialized call visitor."""
        if not self.current_function_report:
            return
        
        context = self.get_current_context()
        context.update({
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        })
        
        # Use the specialized call visitor
        self.call_visitor.process_call(node, context)
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Process assignments using the specialized assignment visitor."""
        context = self.get_current_context()
        context.update({
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        })
        
        # Use the specialized assignment visitor
        self.assignment_visitor.process_assign(node, context, self.current_class)
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments using the specialized assignment visitor."""
        context = self.get_current_context()
        context.update({
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        })
        
        # Use the specialized assignment visitor
        self.assignment_visitor.process_ann_assign(node, context, self.current_class)
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Process name references for state access."""
        if not self.current_function_report:
            return
        
        try:
            self.logger.log(f"[NAME] Found name reference: {node.id}", 3)
            
            context = self.get_current_context()
            context.update({
                'symbol_manager': self.symbol_manager,
                'type_inference': self.type_inference
            })
            
            resolved_fqn = self._cached_resolve_name([node.id], context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.logger.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check
                if not self.symbol_manager.get_variable_type(node.id):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.logger.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.logger.log(f"-> REJECTED (shadowed by local variable)", 3)
            else:
                self.logger.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.logger.log(f"-> ERROR: {e}", 3)
        
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
            self.logger.log(f"[ATTRIBUTE] Found attribute access: {full_name}", 3)
            
            context = self.get_current_context()
            context.update({
                'symbol_manager': self.symbol_manager,
                'type_inference': self.type_inference
            })
            
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.logger.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check on base
                base_name = name_parts[0]
                if not self.symbol_manager.get_variable_type(base_name):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.logger.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.logger.log(f"-> REJECTED (base shadowed)", 3)
            else:
                self.logger.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.logger.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name with caching to avoid redundant work."""
        cache_key = tuple(name_parts)
        
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if self.logger.log_level >= 2:
                self.logger.log_cache_hit(name_parts, cached_result)
            return cached_result
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with refactored visitor."""
    print("=== ANALYSIS PASS START (Refactored Architecture) ===")
    
    atlas = {}
    
    for py_file in python_files:
        print(f"=== Analyzing {py_file.name} ===")
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            # Use the refactored visitor
            visitor = RefactoredAnalysisVisitor(recon_data, module_name)
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
