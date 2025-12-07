#!/usr/bin/env python
"""Check code quality and save results."""
import subprocess
import sys

results = []

# Pylint
print("Running pylint...")
result = subprocess.run(
    [sys.executable, "-m", "pylint", "src/currate", "--fail-under=9.0"],
    capture_output=True,
    text=True
)
results.append("=" * 60)
results.append("PYLINT RESULTS")
results.append("=" * 60)
results.append(result.stdout if result.stdout else "No output")
results.append(result.stderr if result.stderr else "")
results.append(f"Exit code: {result.returncode}")

# Mypy
print("Running mypy...")
result = subprocess.run(
    [sys.executable, "-m", "mypy", "src/currate"],
    capture_output=True,
    text=True
)
results.append("\n" + "=" * 60)
results.append("MYPY RESULTS")
results.append("=" * 60)
results.append(result.stdout if result.stdout else "No output")
results.append(result.stderr if result.stderr else "")
results.append(f"Exit code: {result.returncode}")

# Black
print("Running black...")
result = subprocess.run(
    [sys.executable, "-m", "black", "--check", "src", "tests"],
    capture_output=True,
    text=True
)
results.append("\n" + "=" * 60)
results.append("BLACK RESULTS")
results.append("=" * 60)
results.append(result.stdout if result.stdout else "No output")
results.append(result.stderr if result.stderr else "")
results.append(f"Exit code: {result.returncode}")

# Save to file
output = "\n".join(results)
with open("quality_check_results.txt", "w", encoding="utf-8") as f:
    f.write(output)

print("\nResults saved to quality_check_results.txt")
print(output)
