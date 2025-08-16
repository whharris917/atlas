"""
Code Standard Checker - Code Atlas

Detects and reports code standard violations, such as missing type hints,
to improve the accuracy of the analysis.
"""

import ast
from typing import List
from .utils import ViolationType, log_violation


class CodeStandardChecker:
    """Detects and reports code standard violations during analysis."""
    
    def check_function_type_hints(self, node: ast.FunctionDef, function_fqn: str) -> List[str]:
        """Check for missing type hints and report violations."""
        violations = []
        
        # Check parameter type hints
        for arg in node.args.args:
            if arg.arg != 'self' and not arg.annotation:
                violation = f"Missing type hint on parameter '{arg.arg}' in {function_fqn}"
                violations.append(violation)
                log_violation(
                    ViolationType.MISSING_PARAM_TYPE,
                    f"Parameter '{arg.arg}' in {function_fqn}",
                    f"Cannot infer type for variable '{arg.arg}' - method calls on this variable will fail"
                )
        
        # Check return type hint
        if not node.returns and node.name not in ['__init__', '__str__', '__repr__']:
            violation = f"Missing return type hint on function {function_fqn}"
            violations.append(violation)
            log_violation(
                ViolationType.MISSING_RETURN_TYPE,
                f"Function {function_fqn}",
                "Cannot infer return type - chained method calls may fail"
            )
        
        return violations
