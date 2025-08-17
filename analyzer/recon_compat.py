"""
Reconnaissance Compatibility Layer - Code Atlas

Provides seamless switching between original and refactored reconnaissance implementations.
Part of the Phase 2 refactoring following the successful progressive migration pattern.
"""

import pathlib
from typing import Dict, List, Any, Optional


def get_recon_info() -> Dict[str, Any]:
    """Get information about available reconnaissance implementations."""
    try:
        from .visitors.recon_refactored import run_reconnaissance_pass_refactored
        refactored_available = True
    except ImportError:
        refactored_available = False
    
    try:
        from .recon import run_reconnaissance_pass
        original_available = True
    except ImportError:
        original_available = False
    
    return {
        "original_available": original_available,
        "refactored_available": refactored_available,
        "recommended": "refactored" if refactored_available else "original",
        "version": "2.0-recon-refactored" if refactored_available else "1.0-original"
    }


def run_reconnaissance_pass_compat(python_files: List[pathlib.Path], 
                                 use_refactored: Optional[bool] = None) -> Dict[str, Any]:
    """
    Run reconnaissance pass with compatibility layer.
    
    Args:
        python_files: List of Python files to analyze
        use_refactored: 
            - True: Force refactored implementation
            - False: Force original implementation  
            - None: Auto-detect best available implementation
    
    Returns:
        Dictionary containing reconnaissance data
    """
    info = get_recon_info()
    
    # Determine which implementation to use
    if use_refactored is None:
        # Auto-detect: prefer refactored if available
        use_refactored = info["refactored_available"]
    elif use_refactored and not info["refactored_available"]:
        print("[RECON_COMPAT] Warning: Refactored implementation requested but not available, falling back to original")
        use_refactored = False
    elif not use_refactored and not info["original_available"]:
        print("[RECON_COMPAT] Warning: Original implementation requested but not available, using refactored")
        use_refactored = True
    
    # Run the selected implementation
    if use_refactored:
        print("[RECON_COMPAT] Using refactored reconnaissance implementation")
        from .visitors.recon_refactored import run_reconnaissance_pass_refactored
        return run_reconnaissance_pass_refactored(python_files)
    else:
        print("[RECON_COMPAT] Using original reconnaissance implementation")
        from .recon import run_reconnaissance_pass
        return run_reconnaissance_pass(python_files)


# For backwards compatibility, expose the original interface
def run_reconnaissance_pass(python_files: List[pathlib.Path]) -> Dict[str, Any]:
    """
    Original reconnaissance pass interface.
    
    This function maintains the original API while automatically using
    the best available implementation.
    """
    return run_reconnaissance_pass_compat(python_files, use_refactored=None)
