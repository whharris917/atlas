"""
Analysis Pass - Code Atlas

Contains the AnalysisVisitor, the central dispatcher for the second pass of
the analysis. This visitor coordinates a set of specialized analyzer components
to resolve relationships, track calls, and build the final analysis report.

UPDATED: Integrated with enhanced ScopeManager for unified scope/context management.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional

from .resolver import NameResolver
from .type_inference import TypeInferenceEngine
from .scope_manager import ScopeManager, ScopeType
from .code_checker import CodeStandardChecker
from .call_analyzer import CallAnalyzer
from .function_analyzer import FunctionAnalyzer
from .assignment_analyzer import AssignmentAnalyzer
from .state_access_analyzer import StateAccessAnalyzer
from .utils import EXTERNAL_LIBRARY_ALLOWLIST, get_source
from .logger import get_logger, LogLevel


class AnalysisVisitor(ast.NodeVisitor):
    """Enhanced analysis visitor with unified scope and context management."""
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str):
        self.recon_data = recon_data
        self.import_map = {}
        
        # Initialize logger
        self.logger = get_logger()
        
        # Enhanced scope management - replaces both scope_stack and SymbolTableManager
        self.scope_manager = ScopeManager(recon_data)
        self.module_name = module_name
        
        # Enter initial module scope
        self.scope_manager.enter_scope(module_name, ScopeType.MODULE)

        # Core components
        self.name_resolver = NameResolver(recon_data)
        self.type_inference = TypeInferenceEngine(recon_data)
        self.code_checker = CodeStandardChecker()
        
        # Specialized analyzer components for delegation
        self.call_analyzer = CallAnalyzer(recon_data, self)
        self.function_analyzer = FunctionAnalyzer(recon_data, self)
        self.assignment_analyzer = AssignmentAnalyzer(recon_data, self)
        self.state_analyzer = StateAccessAnalyzer(recon_data, self)
        
        # Context tracking
        self.current_function_report = None
        self.current_class_report = None 
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

    def _get_context(self) -> Dict[str, Any]:
        """Get current resolution context using scope manager."""
        return {
            'current_module': self.scope_manager.get_current_module(),
            'current_class': self.scope_manager.get_current_class_fqn(),
            'current_function_fqn': self.scope_manager.get_current_function_fqn(),
            'import_map': self.import_map,
            'symbol_manager': self.scope_manager,  # Pass scope_manager as symbol_manager
            'type_inference': self.type_inference
        }

    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name with caching to avoid redundant work."""
        cache_key = tuple(name_parts)
        
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            self._log(LogLevel.TRACE, f"Cache hit: {'.'.join(name_parts)} -> {cached_result}")
            return cached_result
        
        self._log(LogLevel.TRACE, f"Cache miss: {'.'.join(name_parts)}. Invoking resolver.")
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if self.current_function_report and call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    def _log_code_violation(self, violation_type: str, details: str, impact: str):
        """Log code standard violations using centralized logging."""
        self._log(LogLevel.WARNING, f"Code violation - {violation_type}: {details}", 
                  extra={'impact': impact, 'violation_type': violation_type})
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        self._log(LogLevel.INFO, f"Starting module analysis: {self.module_name}")
        
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.module_report["module_docstring"] = node.body[0].value.value
        
        self.generic_visit(node)
        self.module_report["imports"] = self.import_map.copy()
        
        self._log(LogLevel.INFO, f"Module analysis complete: {self.module_name}")
    
    def visit_Import(self, node: ast.Import):
        """Process imports."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            self._log(LogLevel.DEBUG, f"Import: {key} -> {alias.name}")
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                self._log(LogLevel.DEBUG, f"From import: {key} -> {node.module}.{alias.name}")
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions with unified scope management."""
        class_fqn = f"{self.module_name}.{node.name}"
        
        self._log(LogLevel.DEBUG, f"Analyzing class: {class_fqn}")
        
        class_report = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "methods": []
        }
        
        # Save previous class context
        old_class_report = self.current_class_report
        self.current_class_report = class_report
        
        # Enter class scope - this automatically updates logger context
        self.scope_manager.enter_scope(class_fqn, ScopeType.CLASS)
        
        try:
            # Process class body - all nested functions will be properly scoped
            self.generic_visit(node)
        finally:
            # Exit scope and restore context - logger context automatically updated
            self.scope_manager.exit_scope()
            self.current_class_report = old_class_report
        
        # Add completed class to module report
        self.module_report["classes"].append(class_report)
        
        self._log(LogLevel.DEBUG, f"Class analysis complete: {class_fqn}")
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process all function and method definitions."""
        function_report = self.function_analyzer.analyze_function(node)
        
        if self.current_class_report is not None:
            self.current_class_report["methods"].append(function_report)
        else:
            self.module_report["functions"].append(function_report)
    
    def visit_Call(self, node: ast.Call):
        self.call_analyzer.analyze_call(node)
        # FIX: Ensure that child nodes of the call (like arguments) are also visited.
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        self.assignment_analyzer.analyze_assignment(node)
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.assignment_analyzer.analyze_annotated_assignment(node)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        self.state_analyzer.analyze_name_access(node)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        self.state_analyzer.analyze_attribute_access(node)
        self.generic_visit(node)


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with clean architecture and external library support."""
    get_logger().info("Starting analysis pass", source=get_source())
    
    atlas = {}
    
    for py_file in python_files:
        get_logger().info(f"Analyzing file: {py_file.name}", source=get_source())
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = AnalysisVisitor(recon_data, module_name)
            visitor.visit(tree)
            
            atlas[py_file.name] = visitor.module_report
            get_logger().info(f"File analysis complete: {py_file.name}", source=get_source())
        
            # Reset context after module analysis completes
            visitor.scope_manager.reset_context()

        except Exception as e:
            get_logger().error(f"Failed to analyze {py_file.name}: {e}", source=get_source())
            atlas[py_file.name] = {
                "file_path": py_file.name,
                "module_docstring": None,
                "imports": {},
                "classes": [],
                "functions": [],
                "module_state": []
            }
            continue
    
    get_logger().info("Analysis pass complete", source=get_source())
    
    return atlas
