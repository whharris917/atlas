# test_import.py
try:
    from analyzer.visitors.recon_refactored import run_reconnaissance_pass_refactored
    print("✅ Import successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
