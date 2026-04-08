"""
Inspect raw FIM file structure to understand format and find time information
"""
import sys

fim_file = "C:\\DCR4402\\FIM\\C01.fim"

try:
    with open(fim_file, 'r', encoding='utf-8', errors='replace') as f:
        # Read first 30 lines to see structure
        print("=== RAW FIM FILE STRUCTURE (first 30 lines) ===\n")
        for i, line in enumerate(f):
            if i >= 30:
                break
            print(f"Line {i+1}: {repr(line)}")
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)
