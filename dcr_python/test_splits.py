#!/usr/bin/env python3
"""Test column-based splitting within sensor pairs"""
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

rows_per_block = len(all_data) // 4

print("Testing: Each sensor has fixed VL/PL split\n")

# Hypothesis: columns 0-1 are always VL, 2-11 are always PL
for sensor_id in [0, 1, 2, 3]:
    start = sensor_id * rows_per_block
    end = start + min(144, rows_per_block)
    block = all_data[start:end]
    
    vl_sum = sum(sum(row[i] for i in range(2)) for row in block)
    pl_sum = sum(sum(row[i] for i in range(2, 12)) for row in block)
    total = vl_sum + pl_sum
    
    print(f"Sensor {sensor_id}: VL={vl_sum}, PL={pl_sum}, Total={total} ({vl_sum/total*100:.1f}% VL)")

print("\nCombining by hypothesis:")
s1_vl = all_data[0:144]
s1_vl_total = sum(sum(row[i] for i in range(2)) for row in s1_vl)
s1_pl = all_data[0:144]
s1_pl_total = sum(sum(row[i] for i in range(2, 12)) for row in s1_pl)
print(f"Sens 1 (Sensor 0 only): VL={s1_vl_total}, PL={s1_pl_total} vs Expected: VL=15662, PL=1856")
print(f"  Error: VL={abs(s1_vl_total-15662)}, PL={abs(s1_pl_total-1856)}")

# Try: Sensor 0 col 0 = VL, rest = PL
s1_vl_alt = sum(row[0] for row in all_data[0:144])
s1_pl_alt = sum(sum(row[1:12]) for row in all_data[0:144])
print(f"\nAlt: Sensor 0 col[0]=VL, rest=PL: VL={s1_vl_alt}, PL={s1_pl_alt} vs Expected: VL=15662, PL=1856")
print(f"  Error: VL={abs(s1_vl_alt-15662)}, PL={abs(s1_pl_alt-1856)}")

# Try: Sensor 0+1 cols [0-1] = VL, rest = PL
s1_vl_combo = sum(sum(row[i] for i in range(2)) for block in [all_data[0:144], all_data[287:287+144]] for row in block)
s1_pl_combo = sum(sum(row[i] for i in range(2, 12)) for block in [all_data[0:144], all_data[287:287+144]] for row in block)
print(f"\nCombo: Sensor 0+1 cols[0-1]=VL, rest=PL: VL={s1_vl_combo}, PL={s1_pl_combo} vs Expected: VL=15662, PL=1856")
print(f"  Error: VL={abs(s1_vl_combo-15662)}, PL={abs(s1_pl_combo-1856)}")
