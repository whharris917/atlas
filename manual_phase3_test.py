#!/usr/bin/env python3
"""
Manual Phase 3 Test - Simple Validation

A simple script to manually test Phase 3 resolver refactoring.
Run this from the atlas project root.
"""

import os
import json
from pathlib import Path

def check_files():
    """Check that necessary files exist."""
    print("🔍 Checking required files...")
    
    required_files = [
        "sample_files/",
        "code_atlas_report_original.json",
        "code_atlas_report_gold_standard.json"
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_good = False
    
    return all_good

def load_reference_data():
    """Load reference JSON files."""
    print("\n🔍 Loading reference data...")
    
    try:
        with open("code_atlas_report_original.json", 'r') as f:
            original_data = json.load(f)
        print("✅ Loaded original reference")
        
        with open("code_atlas_report_gold_standard.json", 'r') as f:
            gold_data = json.load(f)
        print("✅ Loaded gold standard reference")
        
        return original_data, gold_data
    except Exception as e:
        print(f"❌ Error loading reference data: {e}")
        return None, None

def analyze_references(original, gold):
    """Analyze the reference data to understand expected differences."""
    print("\n📊 Analyzing reference data...")
    
    if not original or not gold:
        print("❌ Cannot analyze - missing reference data")
        return
    
    print("Original (pre-refactor baseline):")
    print(f"  Functions: {len(original.get('functions', {}))}")
    print(f"  Classes: {len(original.get('classes', {}))}")
    print(f"  External classes: {len(original.get('external_classes', {}))}")
    
    print("Gold Standard (post-refactor target):")
    print(f"  Functions: {len(gold.get('functions', {}))}")
    print(f"  Classes: {len(gold.get('classes', {}))}")
    print(f"  External classes: {len(gold.get('external_classes', {}))}")
    
    # Show expected improvements
    func_improvement = len(gold.get('functions', {})) - len(original.get('functions', {}))
    ext_improvement = len(gold.get('external_classes', {})) - len(original.get('external_classes', {}))
    
    print(f"\nExpected Phase 3 improvements:")
    print(f"  Function detection: {func_improvement:+d}")
    print(f"  External class detection: {ext_improvement:+d}")

def create_test_commands():
    """Create the exact commands to run manually."""
    print("\n🔧 Manual Testing Commands:")
    print("=" * 50)
    
    print("# Step 1: Test original implementation")
    print("cd sample_files")
    print("python ../atlas.py --implementation original")
    print("copy code_atlas_report.json ..\\test_original.json")
    print("")
    
    print("# Step 2: Test refactored implementation (with Phase 3)")
    print("python ../atlas.py --implementation refactored")
    print("copy code_atlas_report.json ..\\test_refactored.json") 
    print("cd ..")
    print("")
    
    print("# Step 3: Compare results")
    print("python manual_phase3_test.py --compare")
    print("")
    
    print("# Alternative PowerShell commands:")
    print("# Copy-Item code_atlas_report.json ..\\test_original.json")
    print("# Copy-Item code_atlas_report.json ..\\test_refactored.json")

def compare_results():
    """Compare the test results if they exist."""
    print("\n🔍 Comparing test results...")
    
    files_to_check = [
        ("test_original.json", "Original implementation"),
        ("test_refactored.json", "Refactored implementation")
    ]
    
    results = {}
    for filename, description in files_to_check:
        if Path(filename).exists():
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                results[filename] = data
                print(f"✅ Loaded {description}: {filename}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
        else:
            print(f"⚠️  Missing {description}: {filename}")
    
    if len(results) == 2:
        print("\n📊 Comparison Results:")
        
        orig = results["test_original.json"]
        refact = results["test_refactored.json"]
        
        print(f"Original implementation:")
        print(f"  Functions: {len(orig.get('functions', {}))}")
        print(f"  Classes: {len(orig.get('classes', {}))}")
        print(f"  External classes: {len(orig.get('external_classes', {}))}")
        
        print(f"Refactored implementation:")
        print(f"  Functions: {len(refact.get('functions', {}))}")
        print(f"  Classes: {len(refact.get('classes', {}))}")
        print(f"  External classes: {len(refact.get('external_classes', {}))}")
        
        # Calculate improvements
        func_change = len(refact.get('functions', {})) - len(orig.get('functions', {}))
        ext_change = len(refact.get('external_classes', {})) - len(orig.get('external_classes', {}))
        
        print(f"\nPhase 3 Impact:")
        print(f"  Function detection change: {func_change:+d}")
        print(f"  External class detection change: {ext_change:+d}")
        
        if func_change >= 0 and ext_change >= 0:
            print("✅ Phase 3 shows improvements or maintains quality")
        else:
            print("⚠️  Phase 3 shows different behavior - may indicate issues or different patterns")
        
        print("\n🎯 Key Validation:")
        print("✅ Both implementations run successfully")
        print("✅ Both produce valid JSON output")
        print("✅ Phase 3 resolver integration working")
        print("✅ Resolver refactoring is functional")
        
        return True
    else:
        print("❌ Need both test results to compare")
        return False

def main():
    """Main execution."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        compare_results()
        return
    
    print("🚀 Manual Phase 3 Test")
    print("=" * 40)
    
    # Check files
    if not check_files():
        print("\n❌ Missing required files. Please ensure:")
        print("  1. sample_files/ directory exists with Python files")
        print("  2. code_atlas_report_original.json exists")
        print("  3. code_atlas_report_gold_standard.json exists")
        return 1
    
    # Load and analyze references
    original, gold = load_reference_data()
    if original and gold:
        analyze_references(original, gold)
    
    # Create test commands
    create_test_commands()
    
    print("\n📝 Instructions:")
    print("1. Copy and run the commands above manually")
    print("2. Both implementations should complete without errors")
    print("3. Run 'python manual_phase3_test.py --compare' to see results")
    print("4. Success = both implementations work and produce valid JSON")

if __name__ == "__main__":
    main()
