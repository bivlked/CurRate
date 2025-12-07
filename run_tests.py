#!/usr/bin/env python
"""Скрипт для запуска тестов и записи результата в файл."""
import subprocess
import sys

def main():
    """Запуск pytest и запись результата."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    output = f"Exit Code: {result.returncode}\n\n"
    output += "=== STDOUT ===\n"
    output += result.stdout
    output += "\n\n=== STDERR ===\n"
    output += result.stderr
    
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Tests completed with exit code: {result.returncode}")
    print(f"Output written to test_output.txt")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())


