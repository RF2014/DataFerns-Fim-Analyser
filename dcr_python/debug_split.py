#!/usr/bin/env python3
"""Debug VL/PL split deduction"""
import sys
sys.path.insert(0, '.')

import re
from pathlib import Path

fim_path = r'C:\DCR4402\FIM\C01.fim'

with open(fim_path, 'r') as f:
    lines = f.readlines()

# Parse data
all_data = []
for line in lines[2:]:
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_data.append(values)

num_sensors = 4
rows_per_block = len(all_data) // num_sensors

print(f"Total data rows: {len(all_data)}")
print(f"Rows per block: {rows_per_block}")
print(f"Num sensors: {num_sensors}\n")

# Test deduction for each block
for sensor_id in range(num_sensors):
    start = sensor_id * rows_per_block
    end = start + rows_per_block
    block = all_data[start:end]
    
    # Column sums for 12-hour window (144 rows)
    col_sums_12h = [sum(block[i][j] for i in range(144)) for j in range(12)]
    total_12h = sum(col_sums_12h)
    
    print(f"Sensor {sensor_id} (12h window, rows {start}-{start+143}):")
    print(f"  Column sums: {col_sums_12h}")
    print(f"  Total: {total_12h}")
    
    # Try all possible splits
    print(f"  Testing splits:")
    best_split = 1
    best_score = float('-inf')
    
    for split_col in range(1, 11):
        vl_sum = sum(col_sums_12h[:split_col])
        pl_sum = sum(col_sums_12h[split_col:])
        vl_pct = vl_sum / total_12h if total_12h > 0 else 0
        
        # Score based on VL percentage being in "reasonable" range
        if 0.75 <= vl_pct <= 0.95:
            score = vl_pct
        else:
            score = -abs(vl_pct - 0.85)
        
        status = ""
        if split_col == best_split or score > best_score:
            if score > best_score:
                best_score = score
                best_split = split_col
            status = " <- BEST"
        
        print(f"    Col {split_col:2d}: VL={vl_sum:5d} ({vl_pct*100:5.1f}%), PL={pl_sum:5d}, score={score:.3f}{status}")
    
    print(f"  CHOSEN SPLIT: columns 0-{best_split-1} = VL, {best_split}-11 = PL\n")
