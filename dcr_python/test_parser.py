#!/usr/bin/env python3
"""Test the flexible FIM parser"""
import sys
sys.path.insert(0, '.')

import pandas as pd
from src.core.fim_parser import parse_fim_file

fim_path = r'C:\DCR4402\FIM\C01.fim'
print(f"Parsing: {fim_path}\n")

df, metadata = parse_fim_file(fim_path)

if df is None:
    print("Error: Failed to parse FIM file")
    sys.exit(1)

print("=== PARSE RESULT ===")
print(f"Metadata: {metadata}")
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst 20 rows:")
print(df.head(20))

# Validate
print("\n=== VALIDATION (10:00-22:00, 12 hours) ===")
start_time = df['timestamp'].min()
end_time = start_time + pd.Timedelta(hours=12)

results = {}
for direction in ['Sens 1', 'Sens 2']:
    for vclass in ['VL', 'PL']:
        subset = df[(df['direction'] == direction) & 
                    (df['vehicle_class'] == vclass) &
                    (df['timestamp'] >= start_time) & 
                    (df['timestamp'] < end_time)]
        total = subset['count'].sum()
        key = direction + '_' + vclass
        results[key] = total
        print(f"{direction} {vclass}: {total}")

print("\nExpected:")
print("Sens 1 VL: 15662, Sens 1 PL: 1856")
print("Sens 2 VL: 13586, Sens 2 PL: 2167")

print("\nErrors:")
s1_vl_err = abs(results.get('Sens 1_VL', 0) - 15662)
s1_pl_err = abs(results.get('Sens 1_PL', 0) - 1856)
s2_vl_err = abs(results.get('Sens 2_VL', 0) - 13586)
s2_pl_err = abs(results.get('Sens 2_PL', 0) - 2167)
print(f"Sens 1 VL error: {s1_vl_err}")
print(f"Sens 1 PL error: {s1_pl_err}")
print(f"Sens 2 VL error: {s2_vl_err}")
print(f"Sens 2 PL error: {s2_pl_err}")
print(f"Total error: {s1_vl_err + s1_pl_err + s2_vl_err + s2_pl_err}")
