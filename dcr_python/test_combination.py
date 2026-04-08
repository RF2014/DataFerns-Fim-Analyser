#!/usr/bin/env python3
"""Check if sensors combine to form Sens1/Sens2"""
import sys
sys.path.insert(0, '.')

import re

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

print(f"Testing hypothesis: Sensors 0+1 = Sens1, Sensors 2+3 = Sens2\n")

for combo_name, sensor_ids in [("Sens 1", [0, 1]), ("Sens 2", [2, 3])]:
    total = 0
    for sid in sensor_ids:
        start = sid * rows_per_block
        end = start + min(144, rows_per_block)  # First 12 hours
        block = all_data[start:end]
        block_total = sum(sum(row) for row in block)
        total += block_total
        print(f"{combo_name}: Sensor {sid} = {block_total}")
    
    print(f"{combo_name} total: {total}")
    
    if combo_name == "Sens 1":
        expected = 17518
        expected_vl = 15662
        expected_pl = 1856
    else:
        expected = 15753
        expected_vl = 13586
        expected_pl = 2167
    
    print(f"  Expected: {expected} (VL={expected_vl}, PL={expected_pl})")
    print(f"  Error: {abs(total - expected)}\n")
