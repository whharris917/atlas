"""
Code Standard Checker - Code Atlas

Detects and reports code standard violations, such as missing type hints,
to improve the accuracy of the analysis.
"""

import ast
import inspect
from typing import List

from .utils import ViolationType
from .logger import get_logger, LogContext, AnalysisPhase, LogLevel


class CodeStandardChecker:
    """Detects and reports code standard violations during analysis."""
    
    def __init__(self):
        self.violation_count = 0
        self._log(LogLevel.DEBUG, "Code standard checker initialized")
    
    def _log(self, level: LogLevel, message: str, **extra):
        """Consolidated logging with automatic source detection and context."""
        try:
            source_frame = inspect.currentframe().f_back
            source_function = f"{self.__class__.__name__}.{source_frame.f_code.co_name}"
        except Exception:
            source_function = f"{self.__class__.__name__}.unknown"
        
        context = LogContext(
            module="code_checker",
            phase=AnalysisPhase.VALIDATION,
            source=source_function,
            extra=extra
        )
        
        getattr(get_logger(__name__), level.name.lower())(message, context=context)
    
    def check_function_type_hints(self, node: ast.FunctionDef, function_fqn: str) -> List[str]:
        """Check for missing type hints and report violations."""
        violations = []
        
        self._log(LogLevel.TRACE, f"Checking type hints for function: {function_fqn}",
                 function=function_fqn, arg_count=len(node.args.args))
        
        # Check parameter type hints
        missing_param_hints = 0
        for arg in node.args.args:
            if arg.arg != 'self' and not arg.annotation:
                violation = f"Missing type hint on parameter '{arg.arg}' in {function_fqn}"
                violations.append(violation)
                missing_param_hints += 1
                
                self._log_violation(
                    ViolationType.MISSING_PARAM_TYPE,
                    f"Parameter '{arg.arg}' in {function_fqn}",
                    f"Cannot infer type for variable '{arg.arg}' - method calls on this variable will fail",
                    function_fqn
                )
        
        # Check return type hint
        has_return_hint = bool(node.returns)
        if not has_return_hint and node.name not in ['__init__', '__str__', '__repr__']:
            violation = f"Missing return type hint on function {function_fqn}"
            violations.append(violation)
            
            self._log_violation(
                ViolationType.MISSING_RETURN_TYPE,
                f"Function {function_fqn}",
                "Cannot infer return type - chained method calls may fail",
                function_fqn
            )
        
        if violations:
            self._log(LogLevel.INFO, f"Found {len(violations)} type hint violations in {function_fqn}",
                     function=function_fqn, violation_count=len(violations),
                     missing_param_hints=missing_param_hints, missing_return_hint=not has_return_hint)
            self.violation_count += len(violations)
        else:
            self._log(LogLevel.TRACE, f"No type hint violations found in {function_fqn}",
                     function=function_fqn)
        
        return violations
    
    def _log_violation(self, violation_type: str, details: str, impact: str, function_fqn: str) -> None:
        """Log code standard violations using centralized logging."""
        self._log(LogLevel.WARNING, f"Code violation - {violation_type}: {details}",
                 violation_type=violation_type, impact=impact, 
                 action_required="Add appropriate type annotation", function=function_fqn)
    
    def get_violation_summary(self) -> dict:
        """Get summary of all violations found."""
        summary = {
            'total_violations': self.violation_count,
            'has_violations': self.violation_count > 0
        }
        
        if self.violation_count > 0:
            self._log(LogLevel.INFO, f"Code standard checker summary: {self.violation_count} violations found",
                     **summary)
        else:
            self._log(LogLevel.INFO, "Code standard checker summary: No violations found",
                     **summary)
        
        return summary
