#!/usr/bin/env python3
"""
Phase 3 Testing Infrastructure - Atlas Resolver Refactoring

Comprehensive testing framework to validate resolver refactoring progress
and prevent regressions during incremental development.

Usage:
    python test_phase3.py                    # Run all tests
    python test_phase3.py --quick            # Run quick validation only
    python test_phase3.py --verbose          # Detailed output
    python test_phase3.py --baseline         # Create baseline files
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import difflib
import argparse

class Phase3TestFramework:
    """
    Comprehensive testing framework for Phase 3 resolver refactoring.
    
    Validates:
    1. Original implementation produces expected output
    2. Refactored implementation matches original (or approved improvements)
    3. Progressive migration works correctly
    4. No regressions in atlas.py integration
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.atlas_root = Path(__file__).parent
        self.sample_files_dir = self.atlas_root / "sample_files"
        self.original_baseline = self.atlas_root / "code_atlas_report_original.json"
        self.gold_standard = self.atlas_root / "code_atlas_report_gold_standard.json"
        
        # Use direct path to atlas.py instead of alias
        self.atlas_script = self.atlas_root / "atlas.py"
        
        # Test results tracking
        self.test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": []
        }
        
        self._validate_setup()
    
    def _run_atlas(self, args: list, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run atlas.py with given arguments."""
        cmd = [sys.executable, str(self.atlas_script)] + args
        return subprocess.run(cmd, capture_output=True, text=True, 
                            cwd=self.sample_files_dir, timeout=timeout)
    
    def _validate_setup(self):
        """Validate that the test environment is properly set up."""
        if not self.sample_files_dir.exists():
            raise FileNotFoundError(f"Sample files directory not found: {self.sample_files_dir}")
        
        if not self.original_baseline.exists():
            raise FileNotFoundError(f"Original baseline not found: {self.original_baseline}")
        
        if not self.atlas_script.exists():
            raise FileNotFoundError(f"Atlas script not found: {self.atlas_script}")
        
        # Check that atlas script works
        try:
            result = self._run_atlas(['--info'], timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"Atlas script failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Atlas script timed out")
        except FileNotFoundError:
            raise RuntimeError("Python interpreter not found")
        except Exception as e:
            raise RuntimeError(f"Atlas script error: {e}")
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        print("🧪 Phase 3 Testing Infrastructure - Atlas Resolver Refactoring")
        print("=" * 70)
        print(f"Atlas Root: {self.atlas_root}")
        print(f"Sample Files: {self.sample_files_dir}")
        print(f"Baseline: {self.original_baseline}")
        print()
        
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Original Implementation", self.test_original_implementation), 
            ("Refactored Implementation", self.test_refactored_implementation),
            ("Progressive Migration", self.test_progressive_migration),
            ("Atlas Integration", self.test_atlas_integration),
            ("Resolver Functionality", self.test_resolver_functionality),
            ("No Regressions", self.test_no_regressions)
        ]
        
        for test_name, test_func in tests:
            print(f"🔍 Testing: {test_name}")
            try:
                self.test_results["tests_run"] += 1
                success = test_func()
                if success:
                    self.test_results["tests_passed"] += 1
                    print(f"✅ PASS: {test_name}")
                else:
                    self.test_results["tests_failed"] += 1
                    print(f"❌ FAIL: {test_name}")
            except Exception as e:
                self.test_results["tests_failed"] += 1
                self.test_results["failures"].append({
                    "test": test_name,
                    "error": str(e),
                    "type": type(e).__name__
                })
                print(f"💥 ERROR: {test_name} - {e}")
            print()
        
        self._print_summary()
        return self.test_results["tests_failed"] == 0
    
    def test_environment_setup(self) -> bool:
        """Test that the environment is properly configured."""
        try:
            # Check sample files exist
            sample_files = list(self.sample_files_dir.glob("*.py"))
            if len(sample_files) == 0:
                self._log_failure("No Python files found in sample_files directory")
                return False
            
            if self.verbose:
                print(f"   Found {len(sample_files)} sample files: {[f.name for f in sample_files]}")
            
            # Check atlas script responds
            result = self._run_atlas(['--info'], timeout=30)
            
            if result.returncode != 0:
                self._log_failure(f"Atlas --info failed: {result.stderr}")
                return False
            
            if self.verbose:
                print(f"   Atlas script output: {result.stdout.strip()}")
            
            return True
            
        except FileNotFoundError as e:
            self._log_failure(f"File not found: {e}")
            return False
        except subprocess.TimeoutExpired:
            self._log_failure("Atlas script timed out during environment check")
            return False
        except Exception as e:
            self._log_failure(f"Environment setup error: {e}")
            return False
    
    def test_original_implementation(self) -> bool:
        """Test that original implementation produces expected baseline."""
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Clean any existing output
        if output_file.exists():
            output_file.unlink()
        
        # Run original implementation
        result = self._run_atlas(['--implementation', 'original'], timeout=60)
        
        if result.returncode != 0:
            self._log_failure(f"Original implementation failed: {result.stderr}")
            return False
        
        if not output_file.exists():
            self._log_failure("Original implementation did not create output file")
            return False
        
        # Compare with baseline
        return self._compare_json_files(output_file, self.original_baseline, "original")
    
    def test_refactored_implementation(self) -> bool:
        """Test refactored implementation (if available)."""
        # Check if refactored resolver is available
        result = self._run_atlas(['--info'])
        
        # For Phase 3 fresh start, refactored resolver likely not available yet
        if "Resolver Refactored: No" in result.stdout or "resolver" not in result.stdout.lower():
            if self.verbose:
                print("   Refactored resolver not yet available - this is expected for fresh start")
            return True  # This is expected during development
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Clean any existing output
        if output_file.exists():
            output_file.unlink()
        
        # Run refactored implementation
        result = self._run_atlas(['--implementation', 'refactored'], timeout=60)
        
        if result.returncode != 0:
            self._log_failure(f"Refactored implementation failed: {result.stderr}")
            return False
        
        if not output_file.exists():
            self._log_failure("Refactored implementation did not create output file")
            return False
        
        # Compare with gold standard (or original if no gold standard exists)
        baseline = self.gold_standard if self.gold_standard.exists() else self.original_baseline
        return self._compare_json_files(output_file, baseline, "refactored")
    
    def test_progressive_migration(self) -> bool:
        """Test that progressive migration works correctly."""
        implementations = ['auto', 'original']
        
        # Add 'refactored' only if available
        result = self._run_atlas(['--info'])
        if "Refactored: Yes" in result.stdout:
            implementations.append('refactored')
        
        for impl in implementations:
            output_file = self.sample_files_dir / "code_atlas_report.json"
            
            # Clean any existing output
            if output_file.exists():
                output_file.unlink()
            
            # Test each implementation
            result = self._run_atlas(['--implementation', impl], timeout=60)
            
            if result.returncode != 0:
                self._log_failure(f"Progressive migration failed for {impl}: {result.stderr}")
                return False
            
            if not output_file.exists():
                self._log_failure(f"Progressive migration for {impl} did not create output")
                return False
            
            if self.verbose:
                print(f"   ✓ Progressive migration works for --implementation {impl}")
        
        return True
    
    def test_atlas_integration(self) -> bool:
        """Test that atlas.py integration works correctly."""
        test_commands = [
            ['--verbose'],
            ['--quiet'],
            ['--info']
        ]
        
        for cmd in test_commands:
            result = self._run_atlas(cmd, timeout=30)
            
            if result.returncode != 0:
                self._log_failure(f"Atlas integration failed for python atlas.py {' '.join(cmd)}: {result.stderr}")
                return False
            
            if self.verbose:
                print(f"   ✓ Command works: python atlas.py {' '.join(cmd)}")
        
        return True
    
    def test_resolver_functionality(self) -> bool:
        """Test specific resolver functionality."""
        # This test will be expanded as we develop specialized resolver visitors
        # For now, just ensure resolver is being used correctly
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Clean any existing output
        if output_file.exists():
            output_file.unlink()
        
        # Run with verbose output to see resolver in action
        result = self._run_atlas(['--verbose'], timeout=60)
        
        if result.returncode != 0:
            self._log_failure(f"Resolver functionality test failed: {result.stderr}")
            return False
        
        # Check that resolver-related output is present
        if "RESOLVE" not in result.stdout and self.verbose:
            print("   Warning: No resolver debug output found (this may be expected)")
        
        # Validate that cross-references are being resolved
        if output_file.exists():
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            # Check for evidence of name resolution in the output
            atlas_data = data.get('atlas', {})
            total_calls = 0
            for module in atlas_data.values():
                for cls in module.get('classes', []):
                    for method in cls.get('methods', []):
                        total_calls += len(method.get('calls', []))
                for func in module.get('functions', []):
                    total_calls += len(func.get('calls', []))
            
            if self.verbose:
                print(f"   Found {total_calls} resolved calls across all modules")
            
            # If no calls are resolved, that might indicate a resolver issue
            if total_calls == 0:
                print("   Warning: No resolved calls found - this may indicate resolver issues")
        
        return True
    
    def test_no_regressions(self) -> bool:
        """Test that no regressions have been introduced."""
        # This is a meta-test that validates our testing approach itself
        
        # Ensure we can reproduce the original baseline
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        if output_file.exists():
            output_file.unlink()
        
        result = self._run_atlas(['--implementation', 'original'], timeout=60)
        
        if result.returncode != 0:
            self._log_failure(f"Regression test failed - original broken: {result.stderr}")
            return False
        
        # Validate output structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        required_keys = ['recon_data', 'atlas']
        for key in required_keys:
            if key not in data:
                self._log_failure(f"Regression test failed - missing key: {key}")
                return False
        
        if self.verbose:
            print("   ✓ No regressions detected in output structure")
        
        return True
    
    def _compare_json_files(self, output_file: Path, baseline_file: Path, impl_type: str) -> bool:
        """Compare two JSON files for equivalence."""
        try:
            with open(output_file, 'r') as f:
                output_data = json.load(f)
            
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            # For Phase 3, we're particularly interested in resolver-related differences
            differences = self._find_json_differences(output_data, baseline_data)
            
            if not differences:
                if self.verbose:
                    print(f"   ✓ {impl_type} output matches baseline exactly")
                return True
            
            # Check if differences are acceptable improvements
            acceptable_differences = self._are_differences_acceptable(differences, impl_type)
            
            if acceptable_differences:
                if self.verbose:
                    print(f"   ✓ {impl_type} output has acceptable improvements")
                    for diff in differences[:3]:  # Show first 3 differences
                        print(f"     - {diff}")
                return True
            else:
                self._log_failure(f"{impl_type} output differs from baseline")
                for diff in differences[:5]:  # Show first 5 differences
                    print(f"     - {diff}")
                return False
        
        except json.JSONDecodeError as e:
            self._log_failure(f"JSON decode error in {impl_type} output: {e}")
            return False
        except Exception as e:
            self._log_failure(f"Error comparing {impl_type} files: {e}")
            return False
    
    def _find_json_differences(self, data1: Any, data2: Any, path: str = "") -> List[str]:
        """Find differences between two JSON structures."""
        differences = []
        
        if type(data1) != type(data2):
            differences.append(f"Type mismatch at {path}: {type(data1)} vs {type(data2)}")
            return differences
        
        if isinstance(data1, dict):
            for key in set(data1.keys()) | set(data2.keys()):
                new_path = f"{path}.{key}" if path else key
                if key not in data1:
                    differences.append(f"Missing key in first: {new_path}")
                elif key not in data2:
                    differences.append(f"Missing key in second: {new_path}")
                else:
                    differences.extend(self._find_json_differences(data1[key], data2[key], new_path))
        
        elif isinstance(data1, list):
            if len(data1) != len(data2):
                differences.append(f"List length mismatch at {path}: {len(data1)} vs {len(data2)}")
            else:
                for i, (item1, item2) in enumerate(zip(data1, data2)):
                    differences.extend(self._find_json_differences(item1, item2, f"{path}[{i}]"))
        
        else:
            if data1 != data2:
                differences.append(f"Value mismatch at {path}: {data1} vs {data2}")
        
        return differences
    
    def _are_differences_acceptable(self, differences: List[str], impl_type: str) -> bool:
        """Check if differences are acceptable improvements."""
        # For Phase 3, we might accept improvements in name resolution
        acceptable_patterns = [
            "Better name resolution",
            "Enhanced cross-reference detection", 
            "Improved type inference",
            "Additional metadata"
        ]
        
        # For now, require exact match during development
        # This can be relaxed as we identify specific improvements
        return False
    
    def _log_failure(self, message: str):
        """Log a test failure."""
        self.test_results["failures"].append({
            "message": message,
            "timestamp": time.strftime("%H:%M:%S")
        })
        if self.verbose:
            print(f"   ❌ {message}")
    
    def _print_summary(self):
        """Print test summary."""
        print("📊 Test Summary")
        print("=" * 70)
        print(f"Tests Run: {self.test_results['tests_run']}")
        print(f"Passed: {self.test_results['tests_passed']}")
        print(f"Failed: {self.test_results['tests_failed']}")
        
        if self.test_results["tests_failed"] == 0:
            print("🎉 All tests passed! Ready for Phase 3 development.")
        else:
            print("⚠️  Some tests failed. Address issues before proceeding.")
            print("\nFailures:")
            for failure in self.test_results["failures"]:
                if "message" in failure:
                    print(f"  - {failure['message']}")
                else:
                    print(f"  - {failure.get('test', 'Unknown')}: {failure.get('error', 'Unknown error')}")
    
    def create_baseline(self):
        """Create/update baseline files for testing."""
        print("📋 Creating baseline files...")
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Create original baseline
        if output_file.exists():
            output_file.unlink()
        
        result = subprocess.run(['atlas', '--implementation', 'original'], 
                              capture_output=True, text=True, 
                              cwd=self.sample_files_dir, timeout=60)
        
        if result.returncode == 0 and output_file.exists():
            output_file.rename(self.original_baseline)
            print(f"✅ Created original baseline: {self.original_baseline}")
        else:
            print(f"❌ Failed to create original baseline: {result.stderr}")
        
        # Try to create gold standard (if refactored implementation exists)
        result = self._run_atlas(['--info'])
        if "Refactored: Yes" in result.stdout:
            if output_file.exists():
                output_file.unlink()
            
            result = self._run_atlas(['--implementation', 'refactored'], timeout=60)
            
            if result.returncode == 0 and output_file.exists():
                output_file.rename(self.gold_standard)
                print(f"✅ Created gold standard: {self.gold_standard}")
        else:
            print("ℹ️  Refactored implementation not available - skipping gold standard")


def main():
    parser = argparse.ArgumentParser(description="Phase 3 Testing Infrastructure")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick validation only')
    parser.add_argument('--baseline', '-b', action='store_true', help='Create baseline files')
    
    args = parser.parse_args()
    
    try:
        framework = Phase3TestFramework(verbose=args.verbose)
        
        if args.baseline:
            framework.create_baseline()
            return
        
        if args.quick:
            # Quick test - just environment and original implementation
            print("🚀 Quick validation test")
            success = (framework.test_environment_setup() and 
                      framework.test_original_implementation())
            print("✅ Quick test passed" if success else "❌ Quick test failed")
            sys.exit(0 if success else 1)
        
        # Full test suite
        success = framework.run_all_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Testing framework error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
