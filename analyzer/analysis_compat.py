"""
Backward Compatibility Layer - Code Atlas

Provides backward compatibility for the existing Atlas codebase during refactoring.
This allows us to gradually migrate to the new architecture while maintaining
all existing functionality.
"""

import pathlib
from typing import Dict, List, Any

# Import the refactored components
try:
    from .visitors.analysis_refactored import RefactoredAnalysisVisitor, run_analysis_pass as refactored_run_analysis_pass
    from .utils.logger import set_global_log_level
    from .core.configuration import get_config, set_config, AnalysisConfig
    REFACTORED_AVAILABLE = True
except ImportError as e:
    # Fallback to original implementation if refactored components aren't available
    print(f"[COMPAT] Refactored components not available: {e}")
    REFACTORED_AVAILABLE = False

# Import original components as fallback
if not REFACTORED_AVAILABLE:
    from .analysis import AnalysisVisitor, run_analysis_pass as original_run_analysis_pass
    from .utils import LOG_LEVEL


class CompatibilityAnalysisVisitor:
    """
    Compatibility wrapper that can use either the original or refactored visitor.
    This allows us to test the refactored code while maintaining backward compatibility.
    """
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str, use_refactored: bool = True):
        self.use_refactored = use_refactored and REFACTORED_AVAILABLE
        
        if self.use_refactored:
            print(f"[COMPAT] Using REFACTORED visitor for {module_name}")
            self.visitor = RefactoredAnalysisVisitor(recon_data, module_name)
        else:
            print(f"[COMPAT] Using ORIGINAL visitor for {module_name}")
            # Import here to avoid circular imports
            from .analysis import AnalysisVisitor
            self.visitor = AnalysisVisitor(recon_data, module_name)
    
    def visit(self, tree):
        """Delegate to the underlying visitor."""
        return self.visitor.visit(tree)
    
    @property
    def module_report(self):
        """Get the module report from the underlying visitor."""
        return self.visitor.module_report


def run_analysis_pass_compat(python_files: List[pathlib.Path], recon_data: Dict[str, Any], 
                             use_refactored: bool = None) -> Dict[str, Any]:
    """
    Compatibility wrapper for run_analysis_pass that can use either implementation.
    
    Args:
        python_files: List of Python files to analyze
        recon_data: Reconnaissance data from first pass
        use_refactored: If True, use refactored implementation. If None, auto-detect.
        
    Returns:
        Analysis results dictionary
    """
    # Auto-detect if not specified
    if use_refactored is None:
        use_refactored = REFACTORED_AVAILABLE
    
    # Apply backward compatibility for configuration
    if use_refactored and REFACTORED_AVAILABLE:
        # Set up configuration for refactored code
        config = get_config()
        
        # Apply any legacy configuration
        try:
            from .utils import LOG_LEVEL
            config.log_level = LOG_LEVEL
            set_global_log_level(LOG_LEVEL)
        except ImportError:
            pass
        
        print("=== USING REFACTORED ANALYSIS PASS ===")
        return refactored_run_analysis_pass(python_files, recon_data)
    else:
        print("=== USING ORIGINAL ANALYSIS PASS ===")
        from .analysis import run_analysis_pass as original_run_analysis_pass
        return original_run_analysis_pass(python_files, recon_data)


def initialize_atlas_config(log_level: int = 3, **config_overrides) -> None:
    """
    Initialize Atlas configuration for both old and new systems.
    
    Args:
        log_level: Logging level (0-3)
        **config_overrides: Additional configuration overrides
    """
    if REFACTORED_AVAILABLE:
        # Configure refactored system
        config = AnalysisConfig(log_level=log_level, **config_overrides)
        set_config(config)
        set_global_log_level(log_level)
        print(f"[CONFIG] Initialized refactored configuration (log_level={log_level})")
    else:
        # Configure original system
        from . import utils
        utils.LOG_LEVEL = log_level
        print(f"[CONFIG] Initialized original configuration (log_level={log_level})")


def get_atlas_info() -> Dict[str, Any]:
    """Get information about the current Atlas configuration."""
    info = {
        "refactored_available": REFACTORED_AVAILABLE,
        "version": "refactored" if REFACTORED_AVAILABLE else "original",
        "recommended": "refactored" if REFACTORED_AVAILABLE else "original"
    }
    
    if REFACTORED_AVAILABLE:
        config = get_config()
        info.update({
            "log_level": config.log_level,
            "emit_detection_enabled": config.emit_detection_enabled,
            "decorator_analysis_enabled": config.decorator_analysis_enabled,
            "external_libraries_count": len(config.external_libraries)
        })
    else:
        try:
            from .utils import LOG_LEVEL
            info["log_level"] = LOG_LEVEL
        except ImportError:
            info["log_level"] = "unknown"
    
    return info


# Backward compatibility aliases
def create_analysis_visitor(recon_data: Dict[str, Any], module_name: str):
    """Create an analysis visitor using the best available implementation."""
    return CompatibilityAnalysisVisitor(recon_data, module_name, use_refactored=True)


# Test function to validate compatibility
def test_compatibility(sample_code: str = None) -> Dict[str, Any]:
    """
    Test both original and refactored implementations to ensure compatibility.
    
    Returns:
        Dictionary with test results
    """
    if sample_code is None:
        sample_code = '''
def test_function():
    """Test function for compatibility testing."""
    print("Hello, World!")
    return 42

class TestClass:
    def method(self):
        return test_function()
'''
    
    import ast
    
    # Mock recon data for testing
    mock_recon_data = {
        "classes": {},
        "functions": {},
        "state": {},
        "external_classes": {},
        "external_functions": {}
    }
    
    results = {
        "original_available": True,
        "refactored_available": REFACTORED_AVAILABLE,
        "test_results": {}
    }
    
    try:
        tree = ast.parse(sample_code)
        
        # Test original implementation
        try:
            from .analysis import AnalysisVisitor
            original_visitor = AnalysisVisitor(mock_recon_data, "test_module")
            original_visitor.visit(tree)
            results["test_results"]["original"] = {
                "success": True,
                "classes_found": len(original_visitor.module_report["classes"]),
                "functions_found": len(original_visitor.module_report["functions"])
            }
        except Exception as e:
            results["test_results"]["original"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test refactored implementation
        if REFACTORED_AVAILABLE:
            try:
                refactored_visitor = RefactoredAnalysisVisitor(mock_recon_data, "test_module")
                refactored_visitor.visit(tree)
                results["test_results"]["refactored"] = {
                    "success": True,
                    "classes_found": len(refactored_visitor.module_report["classes"]),
                    "functions_found": len(refactored_visitor.module_report["functions"])
                }
            except Exception as e:
                results["test_results"]["refactored"] = {
                    "success": False,
                    "error": str(e)
                }
        else:
            results["test_results"]["refactored"] = {
                "success": False,
                "error": "Refactored implementation not available"
            }
    
    except Exception as e:
        results["parse_error"] = str(e)
    
    return results


if __name__ == "__main__":
    # Run compatibility test
    print("=== Atlas Compatibility Test ===")
    
    info = get_atlas_info()
    print(f"Atlas Version: {info['version']}")
    print(f"Refactored Available: {info['refactored_available']}")
    
    test_results = test_compatibility()
    print(f"\nTest Results:")
    for impl, result in test_results["test_results"].items():
        status = "PASS" if result["success"] else "FAIL"
        print(f"  {impl.upper()}: {status}")
        if not result["success"]:
            print(f"    Error: {result['error']}")
        elif "classes_found" in result:
            print(f"    Classes: {result['classes_found']}, Functions: {result['functions_found']}")
