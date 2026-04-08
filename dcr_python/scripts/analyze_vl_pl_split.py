#!/usr/bin/env python3
"""Analyze FIM file to find optimal VL/PL column split."""
import re
from pathlib import Path

fim_path = r'C:\DCR4402\FIM\C01.fim'
with open(fim_path, 'r') as f:
    lines = f.readlines()

# Extract all data rows
all_rows = []
for line in lines[2:]:
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_rows.append(values)

# Extract 4 sensor blocks
sensor_blocks = {
    1: all_rows[50:338],      # Sensor 1
    2: all_rows[338:626],     # Sensor 2
    3: all_rows[626:914],     # Sensor 3
    4: all_rows[914:1154],    # Sensor 4
}

# For each sensor, calculate 10:00-22:00 window (first 144 rows = 12 hours)
print("Column sums for 10:00-22:00 window (144 rows per sensor):\n")

for sensor_id, block in sensor_blocks.items():
    window = block[:144]  # First 144 rows = 12 hours
    col_sums = [sum(row[i] for row in window) for i in range(12)]
    total = sum(col_sums)
    print(f"Sensor {sensor_id}: {col_sums} (total: {total})")

print("\n" + "="*70)
print("\nNow testing all possible VL/PL splits for each sensor pair:\n")

# Test all splits for Sensors 1+2 combined (expected Sens1: VL=15662, PL=1856)
print("SENSORS 1+2 (expected Sens1: VL=15662, PL=1856, Total=17518)")
print("-" * 70)

for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    # Combine sensors 1 and 2
    vl_total = 0
    pl_total = 0
    
    for block in [sensor_blocks[1][:144], sensor_blocks[2][:144]]:
        for row in block:
            vl_total += sum(row[i] for i in vl_cols)
            pl_total += sum(row[i] for i in pl_cols)
    
    vl_err = abs(vl_total - 15662)
    pl_err = abs(pl_total - 1856)
    combined_err = vl_err + pl_err
    
    if combined_err < 2000:  # Only show reasonable splits
        print(f"Split {vl_end}: VL={vl_total:,} (err {vl_err:,}), PL={pl_total:,} (err {pl_err:,}), combined err: {combined_err:,}")

print("\n" + "="*70)
print("\nSENSORS 3+4 (expected Sens2: VL=13586, PL=2167, Total=15753)")
print("-" * 70)

for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    # Combine sensors 3 and 4
    vl_total = 0
    pl_total = 0
    
    for block in [sensor_blocks[3][:144], sensor_blocks[4][:144]]:
        for row in block:
            vl_total += sum(row[i] for i in vl_cols)
            pl_total += sum(row[i] for i in pl_cols)
    
    vl_err = abs(vl_total - 13586)
    pl_err = abs(pl_total - 2167)
    combined_err = vl_err + pl_err
    
    if combined_err < 2000:  # Only show reasonable splits
        print(f"Split {vl_end}: VL={vl_total:,} (err {vl_err:,}), PL={pl_total:,} (err {pl_err:,}), combined err: {combined_err:,}")
