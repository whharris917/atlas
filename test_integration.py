#!/usr/bin/env python3
"""
Integration Test Script - Atlas Refactoring

Test refactored code against the actual stress test files to ensure
it produces identical output to the gold standard.
"""

import json
import sys
import pathlib
from typing import Dict, Any, List

def find_stress_test_files() -> List[pathlib.Path]:
    """Find the stress test Python files."""
    current_dir = pathlib.Path.cwd()
    
    stress_test_files = [
        "admin_manager.py",
        "database_manager.py", 
        "decorators.py",
        "event_validator.py",
        "inheritence_complex.py",
        "proxy_handler.py",
        "session_manager.py",
        "socketio_events.py"
    ]
    
    found_files = []
    for filename in stress_test_files:
        file_path = current_dir / filename
        if file_path.exists():
            found_files.append(file_path)
        else:
            print(f"⚠️  Stress test file not found: {filename}")
    
    return found_files

def load_gold_standard() -> Dict[str, Any]:
    """Load the gold standard report for comparison."""
    gold_standard_path = pathlib.Path("code_atlas_report_gold_standard.json")
    
    if not gold_standard_path.exists():
        print(f"⚠️  Gold standard file not found: {gold_standard_path}")
        return None
    
    try:
        with open(gold_standard_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load gold standard: {e}")
        return None

def run_full_analysis(python_files: List[pathlib.Path], use_refactored: bool = True) -> Dict[str, Any]:
    """Run full two-pass analysis."""
    try:
        # Import components
        from analyzer.recon import run_reconnaissance_pass
        from analyzer.analysis_compat import run_analysis_pass_compat
        
        print(f"Running analysis on {len(python_files)} files...")
        for f in python_files:
            print(f"  - {f.name}")
        
        # Two-pass analysis
        print("\nPhase 1: Reconnaissance...")
        recon_data = run_reconnaissance_pass(python_files)
        
        print("Phase 2: Analysis...")
        atlas_data = run_analysis_pass_compat(python_files, recon_data, use_refactored=use_refactored)
        
        return {
            "success": True,
            "recon_data": recon_data,
            "atlas": atlas_data,
            "error": None
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "recon_data": None,
            "atlas": None,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def compare_with_gold_standard(result: Dict[str, Any], gold_standard: Dict[str, Any]) -> Dict[str, Any]:
    """Compare analysis result with gold standard."""
    comparison = {
        "identical": False,
        "differences": [],
        "statistics": {}
    }
    
    if not result["success"]:
        comparison["differences"].append(f"Analysis failed: {result['error']}")
        return comparison
    
    # Compare atlas data
    result_atlas = result["atlas"]
    gold_atlas = gold_standard["atlas"]
    
    # Check files
    result_files = set(result_atlas.keys())
    gold_files = set(gold_atlas.keys())
    
    if result_files != gold_files:
        comparison["differences"].append(f"File mismatch: {result_files} vs {gold_files}")
    
    # Compare each file
    for filename in result_files & gold_files:
        result_file = result_atlas[filename]
        gold_file = gold_atlas[filename]
        
        # Count key elements
        result_stats = {
            "classes": len(result_file.get("classes", [])),
            "functions": len(result_file.get("functions", [])),
            "imports": len(result_file.get("imports", {})),
            "module_state": len(result_file.get("module_state", []))
        }
        
        gold_stats = {
            "classes": len(gold_file.get("classes", [])),
            "functions": len(gold_file.get("functions", [])),
            "imports": len(gold_file.get("imports", {})),
            "module_state": len(gold_file.get("module_state", []))
        }
        
        comparison["statistics"][filename] = {
            "result": result_stats,
            "gold": gold_stats
        }
        
        # Check for differences
        for key in result_stats:
            if result_stats[key] != gold_stats[key]:
                comparison["differences"].append(
                    f"{filename}.{key}: {result_stats[key]} vs {gold_stats[key]} (gold)"
                )
        
        # Count function calls and emits
        result_calls = 0
        result_emits = 0
        gold_calls = 0
        gold_emits = 0
        
        def count_calls_in_functions(funcs):
            calls = 0
            emits = 0
            for func in funcs:
                func_calls = func.get("calls", [])
                calls += len(func_calls)
                emits += len([call for call in func_calls if "::" in call])
            return calls, emits
        
        def count_calls_in_classes(classes):
            calls = 0
            emits = 0
            for cls in classes:
                methods = cls.get("methods", [])
                c, e = count_calls_in_functions(methods)
                calls += c
                emits += e
            return calls, emits
        
        # Count in result
        c, e = count_calls_in_functions(result_file.get("functions", []))
        result_calls += c
        result_emits += e
        
        c, e = count_calls_in_classes(result_file.get("classes", []))
        result_calls += c
        result_emits += e
        
        # Count in gold standard
        c, e = count_calls_in_functions(gold_file.get("functions", []))
        gold_calls += c
        gold_emits += e
        
        c, e = count_calls_in_classes(gold_file.get("classes", []))
        gold_calls += c
        gold_emits += e
        
        comparison["statistics"][filename]["calls"] = {
            "result": {"total": result_calls, "emits": result_emits},
            "gold": {"total": gold_calls, "emits": gold_emits}
        }
        
        if result_calls != gold_calls:
            comparison["differences"].append(
                f"{filename} total calls: {result_calls} vs {gold_calls} (gold)"
            )
        
        if result_emits != gold_emits:
            comparison["differences"].append(
                f"{filename} emit calls: {result_emits} vs {gold_emits} (gold)"
            )
    
    # Check if identical
    if not comparison["differences"]:
        comparison["identical"] = True
    
    return comparison

def test_integration():
    """Main integration test."""
    print("=== Atlas Integration Test ===")
    print("Testing refactored code against stress test files and gold standard\n")
    
    # Find stress test files
    print("1. Finding stress test files...")
    stress_files = find_stress_test_files()
    
    if not stress_files:
        print("❌ No stress test files found!")
        return False
    
    print(f"   Found {len(stress_files)} stress test files")
    
    # Load gold standard
    print("\n2. Loading gold standard...")
    gold_standard = load_gold_standard()
    
    if not gold_standard:
        print("❌ Could not load gold standard!")
        return False
    
    print("   ✓ Gold standard loaded")
    
    # Run refactored analysis
    print("\n3. Running refactored analysis...")
    result = run_full_analysis(stress_files, use_refactored=True)
    
    if not result["success"]:
        print(f"❌ Refactored analysis failed!")
        print(f"Error: {result['error']}")
        if result.get("traceback"):
            print(f"Traceback:\n{result['traceback']}")
        return False
    
    print("   ✓ Refactored analysis completed")
    
    # Compare with gold standard
    print("\n4. Comparing with gold standard...")
    comparison = compare_with_gold_standard(result, gold_standard)
    
    if comparison["identical"]:
        print("   🎉 Results are IDENTICAL to gold standard!")
        
        # Show summary statistics
        print("\n   Summary statistics:")
        total_classes = 0
        total_functions = 0
        total_calls = 0
        total_emits = 0
        
        for filename, stats in comparison["statistics"].items():
            result_stats = stats["result"]
            call_stats = stats["calls"]["result"]
            
            total_classes += result_stats["classes"]
            total_functions += result_stats["functions"]
            total_calls += call_stats["total"]
            total_emits += call_stats["emits"]
            
            print(f"     {filename}: {result_stats['classes']} classes, {result_stats['functions']} functions, {call_stats['total']} calls, {call_stats['emits']} emits")
        
        print(f"\n   Totals: {total_classes} classes, {total_functions} functions, {total_calls} calls, {total_emits} emits")
        
        return True
    
    else:
        print("   ⚠️  Results differ from gold standard:")
        for diff in comparison["differences"]:
            print(f"     - {diff}")
        
        # Show detailed comparison
        print("\n   Detailed comparison:")
        for filename, stats in comparison["statistics"].items():
            result_stats = stats["result"]
            gold_stats = stats["gold"]
            result_calls = stats["calls"]["result"]
            gold_calls = stats["calls"]["gold"]
            
            print(f"\n     {filename}:")
            print(f"       Classes: {result_stats['classes']} vs {gold_stats['classes']} (gold)")
            print(f"       Functions: {result_stats['functions']} vs {gold_stats['functions']} (gold)")
            print(f"       Calls: {result_calls['total']} vs {gold_calls['total']} (gold)")
            print(f"       Emits: {result_calls['emits']} vs {gold_calls['emits']} (gold)")
        
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
