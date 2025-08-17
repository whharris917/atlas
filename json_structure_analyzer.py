#!/usr/bin/env python3
"""
JSON Structure Analyzer - Phase 3

Analyzes the actual JSON structure of the generated reports to understand
why the comparison is failing and what the real structure looks like.
"""

import json
import os
from typing import Dict, Any

def analyze_json_file(filepath: str, name: str) -> Dict[str, Any]:
    """Analyze the structure of a JSON file."""
    print(f"\n🔍 Analyzing {name}: {filepath}")
    print("=" * 50)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return {}
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Successfully loaded JSON")
        print(f"📊 File size: {os.path.getsize(filepath)} bytes")
        
        # Analyze top-level structure
        print(f"\n📋 Top-level keys:")
        for key in data.keys():
            value = data[key]
            if isinstance(value, dict):
                print(f"  📁 {key}: dict with {len(value)} items")
                # Show first few keys as examples
                if value:
                    sample_keys = list(value.keys())[:3]
                    print(f"    Sample keys: {sample_keys}")
            elif isinstance(value, list):
                print(f"  📋 {key}: list with {len(value)} items")
            else:
                print(f"  📄 {key}: {type(value).__name__} = {str(value)[:100]}")
        
        # Look for nested structures
        if 'recon_data' in data:
            print(f"\n🔍 Found recon_data structure:")
            recon = data['recon_data']
            for key in recon.keys():
                value = recon[key]
                if isinstance(value, dict):
                    print(f"    📁 recon_data.{key}: {len(value)} items")
                    if value:
                        sample_keys = list(value.keys())[:2]
                        print(f"      Sample: {sample_keys}")
        
        # Look for module-level data
        module_files = [k for k in data.keys() if k.endswith('.py')]
        if module_files:
            print(f"\n🔍 Found {len(module_files)} module files:")
            for module in module_files[:3]:  # Show first 3
                print(f"    📄 {module}")
                if isinstance(data[module], dict):
                    module_keys = list(data[module].keys())
                    print(f"      Keys: {module_keys}")
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def compare_structures(original: Dict[str, Any], refactored: Dict[str, Any]):
    """Compare the structures of original vs refactored output."""
    print(f"\n🔄 Comparing JSON Structures")
    print("=" * 40)
    
    if not original or not refactored:
        print("❌ Cannot compare - missing data")
        return
    
    # Compare top-level keys
    orig_keys = set(original.keys())
    refact_keys = set(refactored.keys())
    
    print(f"📊 Top-level key comparison:")
    print(f"  Original keys: {len(orig_keys)}")
    print(f"  Refactored keys: {len(refact_keys)}")
    
    common_keys = orig_keys & refact_keys
    only_orig = orig_keys - refact_keys
    only_refact = refact_keys - orig_keys
    
    if common_keys:
        print(f"  ✅ Common keys ({len(common_keys)}): {list(common_keys)[:5]}")
    if only_orig:
        print(f"  🔴 Only in original ({len(only_orig)}): {list(only_orig)}")
    if only_refact:
        print(f"  🔵 Only in refactored ({len(only_refact)}): {list(only_refact)}")
    
    # Deep comparison of common structures
    if 'recon_data' in common_keys:
        print(f"\n🔍 Comparing recon_data structures:")
        orig_recon = original['recon_data']
        refact_recon = refactored['recon_data']
        
        for section in ['classes', 'functions', 'external_classes']:
            if section in orig_recon and section in refact_recon:
                orig_count = len(orig_recon[section])
                refact_count = len(refact_recon[section])
                status = "✅" if orig_count == refact_count else "⚠️"
                print(f"    {status} {section}: orig={orig_count}, refact={refact_count}")
                
                # Show sample inheritance data for classes
                if section == 'classes' and orig_count > 0 and refact_count > 0:
                    print(f"      🔍 Sample class comparison:")
                    sample_class = list(orig_recon[section].keys())[0]
                    if sample_class in refact_recon[section]:
                        orig_parents = orig_recon[section][sample_class].get('parents', [])
                        refact_parents = refact_recon[section][sample_class].get('parents', [])
                        print(f"        {sample_class}:")
                        print(f"          Original parents: {orig_parents}")
                        print(f"          Refactored parents: {refact_parents}")

def check_inheritance_fix():
    """Check if the inheritance fix was applied correctly."""
    print(f"\n🔍 Checking Inheritance Fix Results")
    print("=" * 40)
    
    files_to_check = [
        ("code_atlas_report_original.json", "Original"),
        ("code_atlas_report_refactored.json", "Refactored")
    ]
    
    for filepath, name in files_to_check:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if 'recon_data' in data and 'classes' in data['recon_data']:
                    classes = data['recon_data']['classes']
                    
                    # Look for Enum classes
                    enum_classes = [k for k, v in classes.items() if 'Enum' in v.get('parents', [])]
                    abc_classes = [k for k, v in classes.items() if 'ABC' in v.get('parents', [])]
                    protocol_classes = [k for k, v in classes.items() if 'Protocol' in v.get('parents', [])]
                    
                    print(f"\n📊 {name} inheritance analysis:")
                    print(f"  🔢 Enum classes: {len(enum_classes)}")
                    print(f"  🔧 ABC classes: {len(abc_classes)}")
                    print(f"  📋 Protocol classes: {len(protocol_classes)}")
                    
                    if enum_classes:
                        print(f"    Sample Enum: {enum_classes[0]} -> {classes[enum_classes[0]]['parents']}")
                    if abc_classes:
                        print(f"    Sample ABC: {abc_classes[0]} -> {classes[abc_classes[0]]['parents']}")
                
            except Exception as e:
                print(f"❌ Error analyzing {name}: {e}")

def main():
    """Main analysis."""
    print("🚀 JSON Structure Analysis - Phase 3 Debug")
    print("=" * 60)
    
    # Analyze each file
    original_data = analyze_json_file("code_atlas_report_original.json", "Original Implementation")
    refactored_data = analyze_json_file("code_atlas_report_refactored.json", "Refactored Implementation")
    gold_data = analyze_json_file("code_atlas_report_gold_standard.json", "Gold Standard")
    reference_data = analyze_json_file("code_atlas_report_original.json", "Original Reference")
    
    # Compare structures
    if original_data and refactored_data:
        compare_structures(original_data, refactored_data)
    
    # Check inheritance fix
    check_inheritance_fix()
    
    # Final assessment
    print(f"\n🎯 ASSESSMENT:")
    print("=" * 30)
    
    if original_data and refactored_data:
        print("✅ Both implementations generated valid JSON")
        print("✅ Can analyze structure differences")
        
        # Quick inheritance check
        orig_classes = original_data.get('recon_data', {}).get('classes', {})
        refact_classes = refactored_data.get('recon_data', {}).get('classes', {})
        
        if orig_classes and refact_classes:
            # Look for inheritance preservation
            orig_enum_count = sum(1 for c in orig_classes.values() if 'Enum' in c.get('parents', []))
            refact_enum_count = sum(1 for c in refact_classes.values() if 'Enum' in c.get('parents', []))
            
            if orig_enum_count > 0 and refact_enum_count > 0:
                print("✅ Inheritance fix appears to be working!")
                print(f"   Enum classes: orig={orig_enum_count}, refact={refact_enum_count}")
            elif orig_enum_count > 0 and refact_enum_count == 0:
                print("❌ Inheritance fix may not be fully applied")
                print(f"   Enum classes: orig={orig_enum_count}, refact={refact_enum_count}")
            else:
                print("⚠️  No Enum classes found to test inheritance fix")
    else:
        print("❌ Cannot perform full analysis - missing data")

if __name__ == "__main__":
    main()
