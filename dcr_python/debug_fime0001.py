"""Debug FIME0001 structure to understand bi-directional layout"""
import sys
sys.path.insert(0, 'src')
import re

path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0001.FIM'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print(f"\nLine 0 (header): {lines[0].strip()}")
print(f"Line 1 (bins): {lines[1].strip()}")

# Extract all data rows
all_data = []
for i, line in enumerate(lines[2:], start=2):
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_data.append((i, values))

print(f"\nTotal data rows with 12 values: {len(all_data)}")
print(f"\nFirst 5 data rows:")
for idx, vals in all_data[:5]:
    print(f"  Line {idx}: {vals}")

print(f"\nLast 5 data rows:")
for idx, vals in all_data[-5:]:
    print(f"  Line {idx}: {vals}")

# Check for patterns suggesting direction split
if len(all_data) >= 2:
    half = len(all_data) // 2
    print(f"\n--- Checking for bi-directional split at row {half} ---")
    print(f"Rows 0-{half-1} sum: {sum(sum(v) for _, v in all_data[:half])}")
    print(f"Rows {half}-{len(all_data)-1} sum: {sum(sum(v) for _, v in all_data[half:])}")
    
    # Check columns for VL/PL patterns
    first_half = all_data[:half]
    second_half = all_data[half:]
    
    # Sum cols 0-1 (VL) and 2-11 (PL) for each half
    fh_vl = sum(vals[0] + vals[1] for _, vals in first_half)
    fh_pl = sum(sum(vals[2:12]) for _, vals in first_half)
    sh_vl = sum(vals[0] + vals[1] for _, vals in second_half)
    sh_pl = sum(sum(vals[2:12]) for _, vals in second_half)
    
    print(f"\nFirst half (rows 0-{half-1}):")
    print(f"  VL (cols 0-1): {fh_vl}, avg/day: {fh_vl/6:.1f}")
    print(f"  PL (cols 2-11): {fh_pl}, avg/day: {fh_pl/6:.1f}")
    
    print(f"\nSecond half (rows {half}-{len(all_data)-1}):")
    print(f"  VL (cols 0-1): {sh_vl}, avg/day: {sh_vl/6:.1f}")
    print(f"  PL (cols 2-11): {sh_pl}, avg/day: {sh_pl/6:.1f}")
