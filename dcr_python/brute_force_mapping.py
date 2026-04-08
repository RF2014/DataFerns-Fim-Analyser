#!/usr/bin/env python3
"""Brute force test all possible sensor-to-Sens mappings"""
import sys
sys.path.insert(0, '.')

import re
from itertools import combinations, permutations

fim_path = r'C:\DCR4402\FIM\C01.fim'

with open(fim_path, 'r') as f:
    lines = f.readlines()

# Parse data
all_data = []
for line in lines[2:]:
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_data.append(values)

rows_per_block = len(all_data) // 4

# Extract 12-hour blocks for each sensor
sensor_data_12h = {}
for sid in range(4):
    start = sid * rows_per_block
    end = start + min(144, rows_per_block)
    sensor_data_12h[sid] = all_data[start:end]

# Expected targets
targets = {
    'Sens1': {'vl': 15662, 'pl': 1856},
    'Sens2': {'vl': 13586, 'pl': 2167}
}

print("Searching for best sensor mapping...\n")

# Test: Split each sensor by columns
best_error = float('inf')
best_config = None

for split_col in range(1, 11):
    # Try: Sensor 0+1 VL/PL, Sensor 2+3 VL/PL (with same column split)
    for sens1_src_vl in range(4):
        for sens1_src_pl in range(4):
            if sens1_src_vl == sens1_src_pl:
                continue
            for sens2_src_vl in range(4):
                for sens2_src_pl in range(4):
                    if sens2_src_vl == sens2_src_pl:
                        continue
                    
                    # All sources must be different (simple case)
                    sources = {sens1_src_vl, sens1_src_pl, sens2_src_vl, sens2_src_pl}
                    if len(sources) != 4:
                        continue
                    
                    # Calculate totals
                    s1_vl = sum(sum(row[i] for i in range(split_col)) for row in sensor_data_12h[sens1_src_vl])
                    s1_pl = sum(sum(row[i] for i in range(split_col, 12)) for row in sensor_data_12h[sens1_src_pl])
                    s2_vl = sum(sum(row[i] for i in range(split_col)) for row in sensor_data_12h[sens2_src_vl])
                    s2_pl = sum(sum(row[i] for i in range(split_col, 12)) for row in sensor_data_12h[sens2_src_pl])
                    
                    # Calculate error
                    error = (
                        abs(s1_vl - targets['Sens1']['vl']) +
                        abs(s1_pl - targets['Sens1']['pl']) +
                        abs(s2_vl - targets['Sens2']['vl']) +
                        abs(s2_pl - targets['Sens2']['pl'])
                    )
                    
                    if error < best_error:
                        best_error = error
                        best_config = {
                            'split_col': split_col,
                            'Sens1_VL_from': sens1_src_vl,
                            'Sens1_PL_from': sens1_src_pl,
                            'Sens2_VL_from': sens2_src_vl,
                            'Sens2_PL_from': sens2_src_pl,
                            'Sens1_VL': s1_vl,
                            'Sens1_PL': s1_pl,
                            'Sens2_VL': s2_vl,
                            'Sens2_PL': s2_pl,
        'error': error
                        }

print(f"Best mapping found with error: {best_config['error']}\n")
print(f"Column split at: {best_config['split_col']} (cols 0-{best_config['split_col']-1}=VL, {best_config['split_col']}-11=PL)")
print(f"Sens 1 VL from Sensor {best_config['Sens1_VL_from']}: {best_config['Sens1_VL']} (expected 15662, error {abs(best_config['Sens1_VL']-15662)})")
print(f"Sens 1 PL from Sensor {best_config['Sens1_PL_from']}: {best_config['Sens1_PL']} (expected 1856, error {abs(best_config['Sens1_PL']-1856)})")
print(f"Sens 2 VL from Sensor {best_config['Sens2_VL_from']}: {best_config['Sens2_VL']} (expected 13586, error {abs(best_config['Sens2_VL']-13586)})")
print(f"Sens 2 PL from Sensor {best_config['Sens2_PL_from']}: {best_config['Sens2_PL']} (expected 2167, error {abs(best_config['Sens2_PL']-2167)})")
