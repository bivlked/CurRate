#!/usr/bin/env python
"""Quick test runner."""
import subprocess
import sys

try:
    # Try to run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=line", "-x"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Write output
    with open("quick_test_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Exit Code: {result.returncode}\n\n")
        f.write("=== STDOUT ===\n")
        f.write(result.stdout if result.stdout else "No stdout\n")
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr if result.stderr else "No stderr\n")
    
    print(f"Done. Exit code: {result.returncode}")
    print("Output written to quick_test_output.txt")
    
except Exception as e:
    with open("quick_test_error.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {str(e)}\n")
        f.write(f"Type: {type(e).__name__}\n")
    print(f"Error occurred: {e}")
