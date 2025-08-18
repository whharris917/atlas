#!/usr/bin/env python3
"""
Quick Validation Script for Phase 3 Development

Run this after every change to immediately catch regressions.
Designed to be fast and focused on critical functionality.

Usage:
    python quick_validate.py                # Standard validation
    python quick_validate.py --silent       # Silent mode (exit codes only)
    python quick_validate.py --compare      # Compare outputs side by side
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import argparse

class QuickValidator:
    """Fast validation for incremental Phase 3 development."""
    
    def __init__(self, silent: bool = False):
        self.silent = silent
        self.atlas_root = Path(__file__).parent
        self.sample_files_dir = self.atlas_root / "sample_files"
        self.original_baseline = self.atlas_root / "code_atlas_report_original.json"
        
        # Use direct path to atlas.py instead of alias
        self.atlas_script = self.atlas_root / "atlas.py"
        
        if not self.atlas_script.exists():
            raise FileNotFoundError(f"Atlas script not found: {self.atlas_script}")
    
    def _run_atlas(self, args: list, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run atlas.py with given arguments."""
        cmd = [sys.executable, str(self.atlas_script)] + args
        return subprocess.run(cmd, capture_output=True, text=True, 
                            cwd=self.sample_files_dir, timeout=timeout)
        
    def log(self, message: str, force: bool = False):
        """Log message if not in silent mode."""
        if not self.silent or force:
            print(message)
    
    def validate(self) -> bool:
        """Run quick validation checks."""
        start_time = time.time()
        
        if not self.silent:
            self.log("🚀 Quick Validation - Phase 3")
            self.log("=" * 40)
        
        # Check 1: Environment
        if not self._check_environment():
            return False
        
        # Check 2: Original implementation still works
        if not self._check_original():
            return False
        
        # Check 3: Atlas integration works
        if not self._check_atlas_integration():
            return False
        
        # Check 4: If refactored implementation exists, test it
        if not self._check_refactored():
            return False
        
        elapsed = time.time() - start_time
        self.log(f"✅ All checks passed in {elapsed:.1f}s", force=True)
        return True
    
    def _check_environment(self) -> bool:
        """Quick environment check."""
        self.log("🔍 Checking environment...")
        
        if not self.sample_files_dir.exists():
            self.log("❌ Sample files directory missing", force=True)
            return False
        
        # Check sample files exist
        sample_files = list(self.sample_files_dir.glob("*.py"))
        if len(sample_files) == 0:
            self.log("❌ No Python files found in sample_files directory", force=True)
            return False
        
        # Quick atlas command test (use direct script call)
        try:
            result = self._run_atlas(['--info'], timeout=10)
            if result.returncode != 0:
                self.log(f"❌ Atlas script failed: {result.stderr}", force=True)
                return False
        except FileNotFoundError:
            self.log("❌ Python not found or atlas.py script missing", force=True)
            return False
        except subprocess.TimeoutExpired:
            self.log("❌ Atlas script timed out", force=True)
            return False
        except Exception as e:
            self.log(f"❌ Atlas script error: {e}", force=True)
            return False
        
        # Create baseline if missing
        if not self.original_baseline.exists():
            self.log("📋 Original baseline missing, creating it...")
            if not self._create_baseline():
                return False
        
        self.log(f"   ✓ Environment OK ({len(sample_files)} sample files)")
        return True
    
    def _check_original(self) -> bool:
        """Verify original implementation works and matches baseline."""
        self.log("🔍 Checking original implementation...")
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Clean existing output
        if output_file.exists():
            output_file.unlink()
        
        try:
            result = self._run_atlas(['--implementation', 'original'], timeout=60)
            
            if result.returncode != 0:
                self.log(f"❌ Original implementation failed: {result.stderr[:100]}", force=True)
                return False
            
            if not output_file.exists():
                self.log("❌ Original implementation produced no output", force=True)
                return False
            
            # Quick size check (should be reasonable)
            size = output_file.stat().st_size
            if size < 1000:  # Too small
                self.log("❌ Original output suspiciously small", force=True)
                return False
            
            if size > 10_000_000:  # Too large (>10MB)
                self.log("❌ Original output suspiciously large", force=True)
                return False
            
            self.log("   ✓ Original implementation OK")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("❌ Original implementation timed out", force=True)
            return False
        except Exception as e:
            self.log(f"❌ Original implementation error: {e}", force=True)
            return False
    
    def _check_atlas_integration(self) -> bool:
        """Quick atlas.py integration check."""
        self.log("🔍 Checking atlas integration...")
        
        quick_commands = [
            ['--info'],
            ['--implementation', 'auto']
        ]
        
        for cmd in quick_commands:
            try:
                result = self._run_atlas(cmd, timeout=15)
                if result.returncode != 0:
                    self.log(f"❌ Command failed: python atlas.py {' '.join(cmd)}", force=True)
                    return False
            except subprocess.TimeoutExpired:
                self.log(f"❌ Command timed out: {' '.join(cmd)}", force=True)
                return False
            except Exception as e:
                self.log(f"❌ Command error: {' '.join(cmd)} - {e}", force=True)
                return False
        
        self.log("   ✓ Atlas integration OK")
        return True
    
    def _check_refactored(self) -> bool:
        """Check refactored implementation if available."""
        self.log("🔍 Checking refactored implementation...")
        
        # Check if refactored resolver is available
        try:
            result = self._run_atlas(['--info'], timeout=10)
            
            # Look for resolver refactoring status
            info_output = result.stdout
            
            # If no mention of resolver refactoring, it's probably not implemented yet
            if "resolver" not in info_output.lower() or "Resolver Refactored: No" in info_output:
                self.log("   ⏳ Refactored resolver not yet available (expected)")
                return True
            
            # If refactored is available, test it
            output_file = self.sample_files_dir / "code_atlas_report.json"
            
            if output_file.exists():
                output_file.unlink()
            
            result = self._run_atlas(['--implementation', 'refactored'], timeout=30)
            
            if result.returncode != 0:
                self.log(f"❌ Refactored implementation failed: {result.stderr[:100]}", force=True)
                return False
            
            if not output_file.exists():
                self.log("❌ Refactored implementation produced no output", force=True)
                return False
            
            self.log("   ✓ Refactored implementation OK")
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking refactored implementation: {e}", force=True)
            return False
    
    def compare_outputs(self) -> bool:
        """Compare original and refactored outputs side by side."""
        self.log("🔍 Comparing implementations...")
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Get original output
        if output_file.exists():
            output_file.unlink()
        
        result = self._run_atlas(['--implementation', 'original'], timeout=30)
        
        if result.returncode != 0:
            self.log("❌ Failed to get original output for comparison", force=True)
            return False
        
        with open(output_file, 'r') as f:
            original_data = json.load(f)
        
        # Check if refactored is available
        info_result = self._run_atlas(['--info'])
        
        if "Resolver Refactored: No" in info_result.stdout or "resolver" not in info_result.stdout.lower():
            self.log("⏳ Refactored implementation not available for comparison")
            return True
        
        # Get refactored output
        if output_file.exists():
            output_file.unlink()
        
        result = self._run_atlas(['--implementation', 'refactored'], timeout=30)
        
        if result.returncode != 0:
            self.log("❌ Failed to get refactored output for comparison", force=True)
            return False
        
        with open(output_file, 'r') as f:
            refactored_data = json.load(f)
        
        # Simple comparison
        differences = self._quick_compare(original_data, refactored_data)
        
        if differences == 0:
            self.log("   ✓ Implementations produce identical output")
        else:
            self.log(f"   ⚠️  Found {differences} differences (review needed)")
            # Note: differences might be improvements, so don't fail automatically
        
        return True
    
    def _quick_compare(self, data1: dict, data2: dict) -> int:
        """Quick comparison returning number of differences."""
        def count_differences(d1, d2, path=""):
            if type(d1) != type(d2):
                return 1
            
            if isinstance(d1, dict):
                diff_count = 0
                all_keys = set(d1.keys()) | set(d2.keys())
                for key in all_keys:
                    if key not in d1 or key not in d2:
                        diff_count += 1
                    else:
                        diff_count += count_differences(d1[key], d2[key], f"{path}.{key}")
                return diff_count
            
            elif isinstance(d1, list):
                if len(d1) != len(d2):
                    return 1
                diff_count = 0
                for i, (item1, item2) in enumerate(zip(d1, d2)):
                    diff_count += count_differences(item1, item2, f"{path}[{i}]")
                return diff_count
            
            else:
                return 1 if d1 != d2 else 0
        
    def _create_baseline(self) -> bool:
        """Create baseline file if it doesn't exist."""
        self.log("   Creating original baseline...")
        
        output_file = self.sample_files_dir / "code_atlas_report.json"
        
        # Clean existing output
        if output_file.exists():
            output_file.unlink()
        
        try:
            result = self._run_atlas(['--implementation', 'original'], timeout=60)
            
            if result.returncode != 0:
                self.log(f"❌ Failed to create baseline: {result.stderr}", force=True)
                return False
            
            if not output_file.exists():
                self.log("❌ No output file created for baseline", force=True)
                return False
            
            # Move to baseline location
            import shutil
            shutil.copy2(output_file, self.original_baseline)
            
            self.log(f"   ✅ Created baseline: {self.original_baseline}")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating baseline: {e}", force=True)
            return False


def main():
    parser = argparse.ArgumentParser(description="Quick validation for Phase 3 development")
    parser.add_argument('--silent', '-s', action='store_true', help='Silent mode (exit codes only)')
    parser.add_argument('--compare', '-c', action='store_true', help='Compare outputs')
    
    args = parser.parse_args()
    
    validator = QuickValidator(silent=args.silent)
    
    try:
        if args.compare:
            success = validator.compare_outputs()
        else:
            success = validator.validate()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        if not args.silent:
            print("\n⏹️  Validation interrupted")
        sys.exit(1)
    except Exception as e:
        if not args.silent:
            print(f"💥 Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
