"""
Analysis Pass - Code Atlas

Contains the AnalysisVisitor, the central dispatcher for the second pass of
the analysis. This visitor coordinates a set of specialized analyzer components
to resolve relationships, track calls, and build the final analysis report.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional

from .resolver import NameResolver
from .type_inference import TypeInferenceEngine
from .symbol_table import SymbolTableManager
from .code_checker import CodeStandardChecker
from .call_analyzer import CallAnalyzer
from .function_analyzer import FunctionAnalyzer
from .assignment_analyzer import AssignmentAnalyzer
from .state_access_analyzer import StateAccessAnalyzer
from .utils import EXTERNAL_LIBRARY_ALLOWLIST, get_source
from .logger import get_logger, LogLevel


class AnalysisVisitor(ast.NodeVisitor):
    """Enhanced analysis visitor with automatic context propagation to logger."""
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str):
        self.recon_data = recon_data
        self.import_map = {}
        
        # Initialize logger first
        self.logger = get_logger()
        
        # Initialize tracked attributes (triggers context update via properties)
        self._module_name = None
        self._current_class = None
        self._current_function_fqn = None
        
        # Set initial values through properties to trigger context updates
        self.module_name = module_name
        self.current_class = None
        self.current_function_fqn = None
        
        # Core components
        self.name_resolver = NameResolver(recon_data)
        self.type_inference = TypeInferenceEngine(recon_data)
        self.symbol_manager = SymbolTableManager()
        self.code_checker = CodeStandardChecker()
        
        # Specialized analyzer components for delegation
        self.call_analyzer = CallAnalyzer(recon_data, self)
        self.function_analyzer = FunctionAnalyzer(recon_data, self)
        self.assignment_analyzer = AssignmentAnalyzer(recon_data, self)
        self.state_analyzer = StateAccessAnalyzer(recon_data, self)
        
        # Context tracking
        self.current_function_report = None
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
    
    @property
    def module_name(self):
        return self._module_name
    
    @module_name.setter
    def module_name(self, value):
        self._module_name = value
        self._update_logger_context()
    
    @property
    def current_class(self):
        return self._current_class
    
    @current_class.setter
    def current_class(self, value):
        self._current_class = value
        self._update_logger_context()
    
    @property
    def current_function_fqn(self):
        return self._current_function_fqn
    
    @current_function_fqn.setter
    def current_function_fqn(self, value):
        self._current_function_fqn = value
        self._update_logger_context()
    
    def _update_logger_context(self):
        """Update logger context with automatic indentation whenever tracked attributes change."""
        self.logger.module = self.module_name
        self.logger.class_name = self.current_class
        self.logger.function = self.current_function_fqn

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
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if self.current_function_report and call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    def _log_code_violation(self, violation_type: str, details: str, impact: str):
        """Log code standard violations using centralized logging."""
        self._log(LogLevel.WARNING, f"Code violation - {violation_type}: {details}", extra={'impact': impact, 'violation_type': violation_type})
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        # Reset context for clean module analysis
        self.current_class = None
        self.current_function_fqn = None

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
        """Process class definitions."""
        class_fqn = f"{self.module_name}.{node.name}"
        self._log(LogLevel.DEBUG, f"Analyzing class: {node.name}")
        
        class_report = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "methods": []
        }
        
        old_class = self.current_class
        self.current_class = class_fqn  # This triggers logger context update
        self.symbol_manager.enter_class_scope()
        
        try:
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_report = self.function_analyzer.analyze_function(child)
                    class_report["methods"].append(method_report)
        finally:
            self.current_class = old_class  # This triggers logger context update
            self.symbol_manager.exit_class_scope()
        
        self.module_report["classes"].append(class_report)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and handle nested functions properly."""
        if not self.current_class:
            # Top-level function
            self._log(LogLevel.DEBUG, f"Analyzing function: {node.name}")
            function_report = self.function_analyzer.analyze_function(node)
            self.module_report["functions"].append(function_report)
        
        # Nested functions are now handled entirely within FunctionAnalyzer.
        # Class methods are handled by visit_ClassDef.
    
    def visit_Call(self, node: ast.Call):
        self.call_analyzer.analyze_call(node)
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
        
            # RESET CONTEXT after module analysis completes
            get_logger().reset_context()

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
