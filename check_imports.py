#!/usr/bin/env python
"""Check if modules can be imported."""
import sys
import traceback

results = []

modules_to_check = [
    "src.currate.cache",
    "src.currate.cbr_parser",
    "src.currate.currency_converter",
    "src.currate.gui",
    "src.currate.main",
]

for module_name in modules_to_check:
    try:
        __import__(module_name)
        results.append(f"✅ {module_name}: OK")
    except Exception as e:
        results.append(f"❌ {module_name}: {type(e).__name__}: {str(e)}")
        results.append(traceback.format_exc())

output = "\n".join(results)
print(output)

try:
    with open("import_check.txt", "w", encoding="utf-8") as f:
        f.write(output)
    print("\n\nOutput written to import_check.txt")
except Exception as e:
    print(f"\n\nCouldn't write file: {e}")
