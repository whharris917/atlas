"""
Code Standard Checker - Code Atlas

Detects and reports code standard violations, such as missing type hints,
to improve the accuracy of the analysis.
"""

import ast
from typing import List

from .utils import ViolationType
from .logger import get_logger, LogContext, AnalysisPhase

logger = get_logger(__name__)


class CodeStandardChecker:
    """Detects and reports code standard violations during analysis."""
    
    def __init__(self):
        self.violation_count = 0
        logger.debug("Code standard checker initialized",
                    context=LogContext(phase=AnalysisPhase.VALIDATION))
    
    def check_function_type_hints(self, node: ast.FunctionDef, function_fqn: str) -> List[str]:
        """Check for missing type hints and report violations."""
        violations = []
        
        logger.trace(f"Checking type hints for function: {function_fqn}",
                    context=LogContext(phase=AnalysisPhase.VALIDATION,
                                     function=function_fqn,
                                     extra={'arg_count': len(node.args.args)}))
        
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
            logger.info(f"Found {len(violations)} type hint violations in {function_fqn}",
                       context=LogContext(phase=AnalysisPhase.VALIDATION,
                                        function=function_fqn,
                                        extra={'violation_count': len(violations),
                                               'missing_param_hints': missing_param_hints,
                                               'missing_return_hint': not has_return_hint}))
            self.violation_count += len(violations)
        else:
            logger.trace(f"No type hint violations found in {function_fqn}",
                        context=LogContext(phase=AnalysisPhase.VALIDATION,
                                         function=function_fqn))
        
        return violations
    
    def _log_violation(self, violation_type: str, details: str, impact: str, function_fqn: str) -> None:
        """Log code standard violations using centralized logging."""
        logger.warning(f"Code violation - {violation_type}: {details}",
                      context=LogContext(phase=AnalysisPhase.VALIDATION,
                                        function=function_fqn,
                                        extra={'violation_type': violation_type,
                                               'impact': impact,
                                               'action_required': 'Add appropriate type annotation'}))
    
    def get_violation_summary(self) -> dict:
        """Get summary of all violations found."""
        summary = {
            'total_violations': self.violation_count,
            'has_violations': self.violation_count > 0
        }
        
        if self.violation_count > 0:
            logger.info(f"Code standard checker summary: {self.violation_count} violations found",
                       context=LogContext(phase=AnalysisPhase.VALIDATION,
                                        extra=summary))
        else:
            logger.info("Code standard checker summary: No violations found",
                       context=LogContext(phase=AnalysisPhase.VALIDATION,
                                        extra=summary))
        
        return summary
