#!/usr/bin/env python3
"""Find optimal VL/PL column split."""
import re

fim_path = r'C:\DCR4402\FIM\C01.fim'
with open(fim_path, 'r') as f:
    lines = f.readlines()

all_rows = []
for line in lines[2:]:
    values = [int(t) for t in re.findall(r"\d+", line) if t]
    if len(values) == 12:
        all_rows.append(values)

# Extract sensor blocks
blocks = {
    1: all_rows[50:338][:144],
    2: all_rows[338:626][:144],
    3: all_rows[626:914][:144],
    4: all_rows[914:1154][:144],
}

print("Testing all VL/PL splits for Sensors 1+2:\n")
print("Split | VL Total | VL Error | PL Total | PL Error | Combined Error")
print("-" * 70)

best_s12 = None
best_s12_err = float('inf')

for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    vl_total = sum(sum(row[i] for i in vl_cols) for row in blocks[1] + blocks[2])
    pl_total = sum(sum(row[i] for i in pl_cols) for row in blocks[1] + blocks[2])
    
    vl_err = abs(vl_total - 15662)
    pl_err = abs(pl_total - 1856)
    combined_err = vl_err + pl_err
    
    print(f"{vl_end:5} | {vl_total:8} | {vl_err:8} | {pl_total:8} | {pl_err:8} | {combined_err:,}")
    
    if combined_err < best_s12_err:
        best_s12_err = combined_err
        best_s12 = vl_end

print(f"\nBest split for Sens1 (1+2): columns 0-{best_s12-1} = VL, {best_s12}-11 = PL (error: {best_s12_err})")

print("\n\nTesting all VL/PL splits for Sensors 3+4:\n")
print("Split | VL Total | VL Error | PL Total | PL Error | Combined Error")
print("-" * 70)

best_s34 = None
best_s34_err = float('inf')

for vl_end in range(1, 12):
    vl_cols = list(range(vl_end))
    pl_cols = list(range(vl_end, 12))
    
    vl_total = sum(sum(row[i] for i in vl_cols) for row in blocks[3] + blocks[4])
    pl_total = sum(sum(row[i] for i in pl_cols) for row in blocks[3] + blocks[4])
    
    vl_err = abs(vl_total - 13586)
    pl_err = abs(pl_total - 2167)
    combined_err = vl_err + pl_err
    
    print(f"{vl_end:5} | {vl_total:8} | {vl_err:8} | {pl_total:8} | {pl_err:8} | {combined_err:,}")
    
    if combined_err < best_s34_err:
        best_s34_err = combined_err
        best_s34 = vl_end

print(f"\nBest split for Sens2 (3+4): columns 0-{best_s34-1} = VL, {best_s34}-11 = PL (error: {best_s34_err})")
