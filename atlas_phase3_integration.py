#!/usr/bin/env python3
"""
Atlas Phase 3 Integration - Simplified Atlas with Resolver Focus

This is a simplified version of atlas.py that focuses specifically on
testing the Phase 3 resolver refactoring without complex integration issues.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add analyzer to path
analyzer_path = os.path.join(os.path.dirname(__file__), 'analyzer')
if analyzer_path not in sys.path:
    sys.path.insert(0, analyzer_path)

def discover_python_files() -> List[Path]:
    """Discover Python files in current directory."""
    current_dir = Path(".")
    python_files = list(current_dir.glob("*.py"))
    
    # Exclude this script and atlas files
    excluded = {"atlas.py", "atlas_phase3_integration.py", "phase3_demonstration.py"}
    python_files = [f for f in python_files if f.name not in excluded]
    
    return python_files

def run_basic_reconnaissance(files: List[Path]) -> Dict[str, Any]:
    """Run basic reconnaissance without complex compatibility layers."""
    print("Running basic reconnaissance...")
    
    # Try to use the original reconnaissance for now
    try:
        from recon import run_reconnaissance_pass
        return run_reconnaissance_pass(files)
    except ImportError:
        print("⚠️  Could not import reconnaissance - using minimal mock")
        return {
            "imports": {},
            "classes": {},
            "functions": {},
            "state": {},
            "external_classes": {},
            "external_functions": {}
        }

def run_analysis_with_resolver_test(files: List[Path], recon_data: Dict[str, Any], use_refactored_resolver: bool = False) -> Dict[str, Any]:
    """Run analysis with specific resolver implementation for testing."""
    print(f"Running analysis with {'refactored' if use_refactored_resolver else 'original'} resolver...")
    
    try:
        # Import analysis components
        from analysis import AnalysisVisitor
        
        # Create analysis results
        analysis_results = {}
        
        for file_path in files:
            print(f"  Analyzing: {file_path.name}")
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Parse AST
                import ast
                tree = ast.parse(source_code, filename=str(file_path))
                
                # Create visitor with resolver choice
                module_name = file_path.stem
                visitor = AnalysisVisitor(recon_data, module_name)
                
                # Test our resolver integration here
                if use_refactored_resolver:
                    try:
                        from resolver_compat import create_name_resolver
                        # Replace the visitor's resolver with our refactored one
                        visitor.name_resolver = create_name_resolver(recon_data, use_refactored=True)
                        print(f"    ✅ Using refactored resolver for {module_name}")
                    except ImportError as e:
                        print(f"    ⚠️  Could not use refactored resolver: {e}")
                        print("    ⚠️  Falling back to original resolver")
                
                # Visit the AST
                visitor.visit(tree)
                
                # Collect results
                analysis_results[module_name] = visitor.module_report
                
            except Exception as e:
                print(f"    ❌ Error analyzing {file_path.name}: {e}")
                analysis_results[file_path.stem] = {
                    "error": str(e),
                    "functions": {},
                    "classes": [],
                    "imports": {}
                }
        
        return analysis_results
        
    except ImportError as e:
        print(f"❌ Could not import analysis components: {e}")
        return {}

def generate_simple_report(recon_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a simple combined report."""
    print("Generating report...")
    
    # Combine all analysis data
    combined_functions = {}
    combined_classes = {}
    combined_imports = {}
    
    for module_name, module_data in analysis_data.items():
        if "error" in module_data:
            continue
            
        # Merge functions
        for func_name, func_data in module_data.get("functions", []):
            combined_functions[func_name] = func_data
        
        # Merge classes
        for class_data in module_data.get("classes", []):
            if "name" in class_data:
                combined_classes[class_data["name"]] = class_data
        
        # Merge imports
        combined_imports.update(module_data.get("imports", {}))
    
    # Create final report
    report = {
        "functions": combined_functions,
        "classes": combined_classes,
        "imports": combined_imports,
        "state": recon_data.get("state", {}),
        "external_classes": recon_data.get("external_classes", {}),
        "external_functions": recon_data.get("external_functions", {}),
        "analysis_metadata": {
            "modules_analyzed": len(analysis_data),
            "total_functions": len(combined_functions),
            "total_classes": len(combined_classes)
        }
    }
    
    return report

def main():
    """Main execution for Phase 3 testing."""
    parser = argparse.ArgumentParser(description='Atlas Phase 3 Integration Test')
    parser.add_argument('--implementation', choices=['original', 'refactored'], 
                       default='original', help='Resolver implementation to use')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Atlas Phase 3 Integration Test")
        print("=" * 40)
        print(f"Resolver implementation: {args.implementation}")
        print()
    
    # Discover files
    python_files = discover_python_files()
    if not python_files:
        print("No Python files found to analyze")
        return 1
    
    if not args.quiet:
        print(f"Found {len(python_files)} Python files:")
        for f in python_files:
            print(f"  - {f.name}")
        print()
    
    try:
        # Step 1: Reconnaissance
        recon_data = run_basic_reconnaissance(python_files)
        
        # Step 2: Analysis with resolver choice
        use_refactored = (args.implementation == 'refactored')
        analysis_data = run_analysis_with_resolver_test(python_files, recon_data, use_refactored)
        
        if not analysis_data:
            print("❌ Analysis failed")
            return 1
        
        # Step 3: Generate report
        report = generate_simple_report(recon_data, analysis_data)
        
        # Step 4: Save report
        output_file = "code_atlas_report.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        if not args.quiet:
            print(f"✅ Analysis complete!")
            print(f"✅ Report saved to {output_file}")
            print(f"✅ Used {args.implementation} resolver implementation")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
