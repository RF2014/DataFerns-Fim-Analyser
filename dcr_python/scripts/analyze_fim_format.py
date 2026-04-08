"""Analyze FIM file format to understand universal structure"""
import re
from pathlib import Path

fim_path = r'C:\DCR4402\FIM\C01.fim'

with open(fim_path, 'r') as f:
    lines = f.readlines()

print("=== FIM FORMAT ANALYSIS ===\n")

# Line 0: Header
print("LINE 0 (Header):")
print(f"  Raw: {lines[0].rstrip()}")
tokens = re.findall(r"\d+", lines[0])
print(f"  Tokens: {tokens}")
print(f"  Interpretation:")
print(f"    - Position 5: Year = {tokens[5]}")
print(f"    - Position 6: Month = {tokens[6]}")
print(f"    - Position 7: Day = {tokens[7]}")
print(f"    - Position 8: Start Hour = {tokens[8]}")
print(f"    - Position 9: Start Minute = {tokens[9]}")
print(f"    - Position 10: Interval (HHMM) = {tokens[10]}")
print(f"    - Position 11: Num Sensors = {tokens[11]}")

# Line 1: Speed bin labels
print("\nLINE 1 (Speed Bins):")
speed_bins = re.findall(r"\d+", lines[1])
print(f"  Speed bins: {speed_bins}")
print(f"  Count: {len(speed_bins)} bins")

# Lines 2+: Data
print("\nDATA LINES:")
data_lines = lines[2:]
print(f"  Total data lines: {len(data_lines)}")

# Parse all data rows
all_data = []
for i, line in enumerate(data_lines):
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_data.append(values)
    elif i < 60 and any(v > 0 for v in (values or [])):
        print(f"  Line {i}: {len(values)} columns (expected 12): {values[:6]}")

print(f"  Valid data rows (12 columns): {len(all_data)}")

# Block structure
num_sensors = int(tokens[11])
rows_per_block = len(all_data) // num_sensors if num_sensors > 0 else 0

print(f"\nBLOCK STRUCTURE:")
print(f"  Num sensors/blocks: {num_sensors}")
print(f"  Total data rows: {len(all_data)}")
print(f"  Expected rows per block: {rows_per_block} (24h × 12 bins/h = 288)")

# Extract blocks
for bid in range(num_sensors):
    start = bid * rows_per_block
    end = start + rows_per_block
    if end <= len(all_data):
        block = all_data[start:end]
        block_total = sum(sum(row) for row in block)
        
        # First 144 rows = 12 hours
        first_12h = block[:144]
        col_sums_12h = [sum(row[i] for row in first_12h) for i in range(12)]
        
        print(f"\n  Block {bid} (rows {start}-{end-1}):")
        print(f"    24h total: {block_total}")
        print(f"    12h column sums: {col_sums_12h}")

print("\n=== UNIVERSAL FIM FORMAT ===")
print("1. Line 0: Header with date/time/num_sensors")
print("2. Line 1: 12 speed bin labels")
print("3. Lines 2+: Data in N blocks of 288 rows each")
print("   - Each block: one sensor × 12 speed bins")
print("   - Each row: 5-minute interval (12 rows/hour)")
print("   - Columns 0-11: Speed class counts (30-150 km/h)")
print("   - VL/PL must be deduced from column distribution")
