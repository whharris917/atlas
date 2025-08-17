#!/usr/bin/env python3
"""
Compare Atlas outputs to find differences between pre/post refactor.
"""

import json
import sys
from typing import Dict, Any, List
from pathlib import Path

def load_json_report(filepath: str) -> Dict[str, Any]:
    """Load Atlas JSON report."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def compare_atlas_data(data1: Dict[str, Any], data2: Dict[str, Any], name1: str, name2: str):
    """Compare two Atlas data structures in detail."""
    print(f"=== Comparing {name1} vs {name2} ===\n")
    
    # Compare top-level structure
    atlas1 = data1.get('atlas', {})
    atlas2 = data2.get('atlas', {})
    
    files1 = set(atlas1.keys())
    files2 = set(atlas2.keys())
    
    if files1 != files2:
        print(f"❌ Different files analyzed:")
        print(f"   {name1}: {files1}")
        print(f"   {name2}: {files2}")
        return
    
    print(f"✓ Same files analyzed: {len(files1)} files\n")
    
    # Compare each file
    for filename in sorted(files1):
        print(f"📁 Comparing {filename}:")
        file1 = atlas1[filename]
        file2 = atlas2[filename]
        
        # Compare high-level counts
        counts1 = {
            'classes': len(file1.get('classes', [])),
            'functions': len(file1.get('functions', [])),
            'imports': len(file1.get('imports', {})),
            'module_state': len(file1.get('module_state', []))
        }
        
        counts2 = {
            'classes': len(file2.get('classes', [])),
            'functions': len(file2.get('functions', [])),
            'imports': len(file2.get('imports', {})),
            'module_state': len(file2.get('module_state', []))
        }
        
        if counts1 != counts2:
            print(f"   ❌ Count differences:")
            for key in counts1:
                if counts1[key] != counts2[key]:
                    print(f"      {key}: {counts1[key]} vs {counts2[key]}")
        else:
            print(f"   ✓ Same counts: {counts1}")
        
        # Compare function calls in detail
        calls1 = extract_all_calls(file1)
        calls2 = extract_all_calls(file2)
        
        if calls1 != calls2:
            print(f"   ❌ Function call differences:")
            only_in_1 = calls1 - calls2
            only_in_2 = calls2 - calls1
            
            if only_in_1:
                print(f"      Only in {name1}: {sorted(only_in_1)}")
            if only_in_2:
                print(f"      Only in {name2}: {sorted(only_in_2)}")
        else:
            print(f"   ✓ Same function calls: {len(calls1)} total")
        
        # Compare imports
        imports1 = file1.get('imports', {})
        imports2 = file2.get('imports', {})
        
        if imports1 != imports2:
            print(f"   ❌ Import differences:")
            print(f"      {name1}: {imports1}")
            print(f"      {name2}: {imports2}")
        else:
            print(f"   ✓ Same imports")
        
        print()

def extract_all_calls(file_data: Dict[str, Any]) -> set:
    """Extract all function calls from a file's analysis data."""
    calls = set()
    
    # Extract from functions
    for func in file_data.get('functions', []):
        calls.update(func.get('calls', []))
    
    # Extract from class methods
    for cls in file_data.get('classes', []):
        for method in cls.get('methods', []):
            calls.update(method.get('calls', []))
    
    return calls

def main():
    """Main comparison function."""
    print("=== Atlas Output Comparison Tool ===\n")
    
    # Look for common output files
    pre_refactor_files = [
        "code_atlas_report_pre_refactor.json",
        "code_atlas_report_original.json", 
        "code_atlas_report_backup.json",
        "code_atlas_report_old.json"
    ]
    
    post_refactor_files = [
        "code_atlas_report.json",
        "code_atlas_report_new.json",
        "code_atlas_report_refactored.json"
    ]
    
    pre_file = None
    post_file = None
    
    # Find pre-refactor file
    for filename in pre_refactor_files:
        if Path(filename).exists():
            pre_file = filename
            break
    
    # Find post-refactor file  
    for filename in post_refactor_files:
        if Path(filename).exists():
            post_file = filename
            break
    
    if not pre_file or not post_file:
        print("Please create comparison files by running:")
        print("1. Run original Atlas and rename output: mv code_atlas_report.json code_atlas_report_pre_refactor.json")
        print("2. Run refactored Atlas: atlas --implementation original")
        print("3. Run this comparison script again")
        return
    
    print(f"Comparing:")
    print(f"  Pre-refactor:  {pre_file}")
    print(f"  Post-refactor: {post_file}")
    print()
    
    # Load both files
    data1 = load_json_report(pre_file)
    data2 = load_json_report(post_file)
    
    if not data1 or not data2:
        print("Failed to load one or both files!")
        return
    
    # Compare them
    compare_atlas_data(data1, data2, "Pre-refactor", "Post-refactor")

if __name__ == "__main__":
    main()
