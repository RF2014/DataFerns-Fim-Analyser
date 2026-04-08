"""
Test C01.fim mode detection
"""
import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
import re
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data\C01.fim'

# First, let's analyze the header
with open(path, 'r') as f:
    header = f.readline()

print('=== C01.fim Header Analysis ===')
print(f'Header: {header.strip()}')

tokens = [int(t) for t in re.findall(r"\d+", header) if t]
print(f'\nTokens: {tokens}')
print(f'Length: {len(tokens)}')

print('\n\nField positions:')
for i, val in enumerate(tokens):
    print(f'  Index {i}: {val}')

print('\n\nPattern analysis:')
print('Index 5-10: [year=2025, month=09, day=20, hour=10, minute=0, interval=60]')
print('Index 11: 4 (num_sensors?)')
print('Index 12: 1 (Mode?)')
print('\nIf index 12 is mode:')
print(f'  Header value: {tokens[12]}')
print(f'  Mode (value+1): {tokens[12] + 1}')

# Now parse with the updated parser
print('\n\n=== Parser Test ===')
df, meta = mod.parse_fim_file(path, interval_minutes=60)

MODE_DESCRIPTIONS = {
    1: "1 - TV Conf.",
    2: "2 - TV/PL",
    3: "3 - TV/PL",
    4: "4 - VL/PL",
}

if meta:
    print(f'Start: {meta.get("day"):02d}/{meta.get("month"):02d}/{meta.get("year")} at {meta.get("start_hour"):02d}:{meta.get("start_minute"):02d}')
    print(f'Interval: {meta.get("interval_minutes")} minutes')
    print(f'Sensors: {meta.get("num_sensors")}')
    if meta.get('mode') is not None:
        mode_num = meta['mode']
        mode_desc = MODE_DESCRIPTIONS.get(mode_num, f"Mode {mode_num}")
        print(f'Mode: {mode_desc}')
    else:
        print(f'Mode: Not detected')
    
    if df is not None:
        print(f'\nData rows: {len(df)}')
        print(f'Unique timestamps: {len(df["timestamp"].unique())}')
