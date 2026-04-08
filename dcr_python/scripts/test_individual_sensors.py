#!/usr/bin/env python3
"""Test individual sensor matching."""
import re

fim_path = r'C:\DCR4402\FIM\C01.fim'
with open(fim_path, 'r') as f:
    lines = f.readlines()

all_rows = []
for line in lines[2:]:
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_rows.append(values)

# Extract sensor blocks (10:00-22:00 = first 144 rows)
blocks = {
    1: all_rows[50:194],      # Sensor 1, 144 rows
    2: all_rows[338:482],     # Sensor 2, 144 rows
    3: all_rows[626:770],     # Sensor 3, 144 rows
    4: all_rows[914:1058],    # Sensor 4, 144 rows
}

expected = {
    'Sens1': {'VL': 15662, 'PL': 1856, 'Total': 17518},
    'Sens2': {'VL': 13586, 'PL': 2167, 'Total': 15753},
}

print("Testing each sensor individually with columns 0-1=VL, 2-11=PL:\n")

for sensor_id, block in blocks.items():
    vl_total = sum(sum(row[i] for i in range(2)) for row in block)
    pl_total = sum(sum(row[i] for i in range(2, 12)) for row in block)
    total = vl_total + pl_total
    
    print(f"Sensor {sensor_id}:")
    print(f"  VL: {vl_total:,} | PL: {pl_total:,} | Total: {total:,}")
    
    # Check against expected values
    for expected_name, expected_vals in expected.items():
        vl_err = abs(vl_total - expected_vals['VL'])
        pl_err = abs(pl_total - expected_vals['PL'])
        combined_err = vl_err + pl_err
        if combined_err < 3000:
            print(f"    -> Close to {expected_name}! (VL err: {vl_err:,}, PL err: {pl_err:,}, combined: {combined_err:,})")
    print()

print("\nLet me also check if Sensor 1 alone matches Sens1:\n")
for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    vl_total = sum(sum(row[i] for i in vl_cols) for row in blocks[1])
    pl_total = sum(sum(row[i] for i in pl_cols) for row in blocks[1])
    
    vl_err = abs(vl_total - 15662)
    pl_err = abs(pl_total - 1856)
    combined_err = vl_err + pl_err
    
    if combined_err < 2000:
        print(f"Split {vl_end}: VL={vl_total:,} (err {vl_err:,}), PL={pl_total:,} (err {pl_err:,}), combined: {combined_err:,}")

print("\nAnd Sensor 3 alone for Sens2:\n")
for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    vl_total = sum(sum(row[i] for i in vl_cols) for row in blocks[3])
    pl_total = sum(sum(row[i] for i in pl_cols) for row in blocks[3])
    
    vl_err = abs(vl_total - 13586)
    pl_err = abs(pl_total - 2167)
    combined_err = vl_err + pl_err
    
    if combined_err < 2000:
        print(f"Split {vl_end}: VL={vl_total:,} (err {vl_err:,}), PL={pl_total:,} (err {pl_err:,}), combined: {combined_err:,}")
