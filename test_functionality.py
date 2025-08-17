#!/usr/bin/env python3
"""
Functionality Test Script - Atlas Refactoring

Test that refactored code produces identical results to original code.
Run this after import test passes.
"""

import ast
import json
import sys
import tempfile
import pathlib
from typing import Dict, Any

def create_test_file() -> pathlib.Path:
    """Create a test Python file with various patterns."""
    test_code = '''
"""Test module for Atlas functionality testing."""

import threading
from flask_socketio import SocketIO, emit

# Module state
SAMPLE_DATA = {"key": "value"}
socketio_instance = SocketIO()

class TestClass:
    """Test class with various patterns."""
    
    def __init__(self, data: dict):
        self.data = data
        self.thread_pool = threading.ThreadPoolExecutor()
    
    def emit_event(self, event_name: str, data: dict) -> None:
        """Method with SocketIO emit call."""
        socketio_instance.emit(event_name, data, room='admin')
        emit(f'{event_name}_processed', {'status': 'complete'})
    
    def process_data(self) -> dict:
        """Method accessing module state."""
        return SAMPLE_DATA

def standalone_function(param: str) -> str:
    """Standalone function."""
    result = TestClass({'test': param})
    result.emit_event('test_event', {'data': param})
    return result.process_data()

# Nested function
def outer_function():
    def inner_function():
        return "nested"
    return inner_function()
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        return pathlib.Path(f.name)

def run_original_analysis(test_file: pathlib.Path) -> Dict[str, Any]:
    """Run analysis using original implementation."""
    try:
        from analyzer.recon import run_reconnaissance_pass
        from analyzer.analysis import run_analysis_pass
        
        # Run two-pass analysis
        recon_data = run_reconnaissance_pass([test_file])
        atlas_data = run_analysis_pass([test_file], recon_data)
        
        return {
            "success": True,
            "recon_data": recon_data,
            "atlas_data": atlas_data,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "recon_data": None,
            "atlas_data": None,
            "error": str(e)
        }

def run_refactored_analysis(test_file: pathlib.Path) -> Dict[str, Any]:
    """Run analysis using refactored implementation."""
    try:
        from analyzer.analysis_compat import run_analysis_pass_compat
        from analyzer.recon import run_reconnaissance_pass
        
        # Run reconnaissance with original (not yet refactored)
        recon_data = run_reconnaissance_pass([test_file])
        
        # Run analysis with refactored code
        atlas_data = run_analysis_pass_compat([test_file], recon_data, use_refactored=True)
        
        return {
            "success": True,
            "recon_data": recon_data,
            "atlas_data": atlas_data,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "recon_data": None,
            "atlas_data": None,
            "error": str(e)
        }

def compare_results(original: Dict[str, Any], refactored: Dict[str, Any]) -> Dict[str, Any]:
    """Compare results from original and refactored implementations."""
    comparison = {
        "identical": False,
        "differences": [],
        "statistics": {}
    }
    
    if not original["success"] or not refactored["success"]:
        comparison["differences"].append("One or both analyses failed")
        return comparison
    
    # Compare atlas data (the main output)
    orig_atlas = original["atlas_data"]
    refact_atlas = refactored["atlas_data"]
    
    # Check if we have the same files
    orig_files = set(orig_atlas.keys())
    refact_files = set(refact_atlas.keys())
    
    if orig_files != refact_files:
        comparison["differences"].append(f"Different files analyzed: {orig_files} vs {refact_files}")
        return comparison
    
    # Compare each file's analysis
    for filename in orig_files:
        orig_file_data = orig_atlas[filename]
        refact_file_data = refact_atlas[filename]
        
        # Compare key metrics
        orig_stats = {
            "classes": len(orig_file_data.get("classes", [])),
            "functions": len(orig_file_data.get("functions", [])),
            "module_state": len(orig_file_data.get("module_state", []))
        }
        
        refact_stats = {
            "classes": len(refact_file_data.get("classes", [])),
            "functions": len(refact_file_data.get("functions", [])),
            "module_state": len(refact_file_data.get("module_state", []))
        }
        
        comparison["statistics"][filename] = {
            "original": orig_stats,
            "refactored": refact_stats
        }
        
        # Check for differences
        for key in orig_stats:
            if orig_stats[key] != refact_stats[key]:
                comparison["differences"].append(
                    f"{filename}.{key}: {orig_stats[key]} vs {refact_stats[key]}"
                )
        
        # Count total function calls and emit calls
        orig_calls = 0
        orig_emits = 0
        refact_calls = 0
        refact_emits = 0
        
        # Count in functions
        for func in orig_file_data.get("functions", []):
            orig_calls += len(func.get("calls", []))
            orig_emits += len([call for call in func.get("calls", []) if "::" in call])
        
        for func in refact_file_data.get("functions", []):
            refact_calls += len(func.get("calls", []))
            refact_emits += len([call for call in func.get("calls", []) if "::" in call])
        
        # Count in class methods
        for cls in orig_file_data.get("classes", []):
            for method in cls.get("methods", []):
                orig_calls += len(method.get("calls", []))
                orig_emits += len([call for call in method.get("calls", []) if "::" in call])
        
        for cls in refact_file_data.get("classes", []):
            for method in cls.get("methods", []):
                refact_calls += len(method.get("calls", []))
                refact_emits += len([call for call in method.get("calls", []) if "::" in call])
        
        comparison["statistics"][filename]["call_counts"] = {
            "original": {"total_calls": orig_calls, "emit_calls": orig_emits},
            "refactored": {"total_calls": refact_calls, "emit_calls": refact_emits}
        }
        
        if orig_calls != refact_calls:
            comparison["differences"].append(
                f"{filename} total calls: {orig_calls} vs {refact_calls}"
            )
        
        if orig_emits != refact_emits:
            comparison["differences"].append(
                f"{filename} emit calls: {orig_emits} vs {refact_emits}"
            )
    
    # If no differences found, mark as identical
    if not comparison["differences"]:
        comparison["identical"] = True
    
    return comparison

def test_functionality():
    """Main functionality test."""
    print("=== Atlas Functionality Test ===")
    
    # Create test file
    print("\n1. Creating test file...")
    test_file = create_test_file()
    print(f"   Created: {test_file}")
    
    try:
        # Run original analysis
        print("\n2. Running original analysis...")
        original_result = run_original_analysis(test_file)
        if original_result["success"]:
            print("    Original analysis completed")
        else:
            print(f"   Original analysis failed: {original_result['error']}")
            return False
        
        # Run refactored analysis
        print("\n3. Running refactored analysis...")
        refactored_result = run_refactored_analysis(test_file)
        if refactored_result["success"]:
            print("   Refactored analysis completed")
        else:
            print(f"   Refactored analysis failed: {refactored_result['error']}")
            return False
        
        # Compare results
        print("\n4. Comparing results...")
        comparison = compare_results(original_result, refactored_result)
        
        if comparison["identical"]:
            print("   Results are IDENTICAL!")
            
            # Show statistics
            for filename, stats in comparison["statistics"].items():
                print(f"\n   {filename} statistics:")
                orig = stats["original"]
                print(f"     Classes: {orig['classes']}, Functions: {orig['functions']}, State: {orig['module_state']}")
                
                if "call_counts" in stats:
                    calls = stats["call_counts"]["original"]
                    print(f"     Total calls: {calls['total_calls']}, Emit calls: {calls['emit_calls']}")
            
            return True
        else:
            print("     Results have differences:")
            for diff in comparison["differences"]:
                print(f"     - {diff}")
            
            # Still show statistics for debugging
            for filename, stats in comparison["statistics"].items():
                print(f"\n   {filename} comparison:")
                orig = stats["original"]
                refact = stats["refactored"]
                print(f"     Classes: {orig['classes']} vs {refact['classes']}")
                print(f"     Functions: {orig['functions']} vs {refact['functions']}")
                print(f"     State: {orig['module_state']} vs {refact['module_state']}")
                
                if "call_counts" in stats:
                    orig_calls = stats["call_counts"]["original"]
                    refact_calls = stats["call_counts"]["refactored"]
                    print(f"     Total calls: {orig_calls['total_calls']} vs {refact_calls['total_calls']}")
                    print(f"     Emit calls: {orig_calls['emit_calls']} vs {refact_calls['emit_calls']}")
            
            return False
    
    finally:
        # Cleanup
        try:
            test_file.unlink()
            print(f"\n   Cleaned up test file: {test_file}")
        except:
            pass

if __name__ == "__main__":
    success = test_functionality()
    sys.exit(0 if success else 1)
