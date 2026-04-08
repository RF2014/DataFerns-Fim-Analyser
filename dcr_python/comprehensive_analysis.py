"""
Comprehensive FIM analysis with mode-specific mapping strategy
"""
import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
import re
from datetime import datetime, timedelta
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

files = [
    ('C01.fim', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim', 4),
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM', 3),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM', 3),
]

MODE_DESCRIPTIONS = {
    3: "Mode 3 - VL/PL comptages simple sur deux sens",
    4: "Mode 4 - Vitesse sur les deux sens, 12 classe de vitesse",
}

SPEED_CLASSES = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150]

print('=' * 90)
print('FIM FILES - COMPREHENSIVE MAPPING ANALYSIS')
print('=' * 90)

for filename, path, expected_mode in files:
    print(f'\n{filename}:')
    print('-' * 90)
    
    # Parse with parser
    df, meta = mod.parse_fim_file(path, interval_minutes=60)
    
    # Extract header info
    with open(path, 'r') as f:
        lines = f.readlines()
    
    header = lines[0].strip()
    tokens = [int(t) for t in re.findall(r"\d+", header) if t]
    
    # Count data rows
    data_rows = []
    for line in lines[2:]:
        values = [int(t) for t in re.findall(r"\d+", line) if t]
        if len(values) == 12:
            data_rows.append(values)
    
    # Get mode from metadata
    detected_mode = meta.get('mode') if meta else None
    
    print(f'Detected Mode: {detected_mode} - {MODE_DESCRIPTIONS.get(detected_mode, "Unknown")}')
    print(f'Expected Mode: {expected_mode} - {MODE_DESCRIPTIONS.get(expected_mode, "Unknown")}')
    
    # Metadata
    if meta:
        start_date = f"{meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}"
        start_time = f"{meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}"
        print(f'\nMetadata:')
        print(f'  Start Date/Time: {start_date} at {start_time}')
        print(f'  Frequency: 60 minutes')
        print(f'  Num Sensors: {meta.get("num_sensors")}')
        print(f'  Num Data Rows: {meta.get("num_data_rows")}')
        
        if df is not None:
            num_measurements = len(df['timestamp'].unique())
            start_dt = datetime(
                meta.get('year'), meta.get('month'), meta.get('day'),
                meta.get('start_hour'), meta.get('start_minute')
            )
            end_dt = start_dt + timedelta(minutes=60 * (num_measurements - 1))
            print(f'  End Date/Time:   {end_dt.strftime("%d/%m/%Y at %H:%M")}')
            print(f'  Measurements: {num_measurements}')
    
    # Data analysis
    if data_rows:
        col_sums = [0] * 12
        for row in data_rows:
            for i in range(12):
                col_sums[i] += row[i]
        
        total = sum(col_sums)
        print(f'\nData Distribution ({total} total vehicles):')
        
        if detected_mode == 3:
            # Mode 3: VL/PL mapping
            pl_sum = sum(col_sums[0:2])
            vl_sum = sum(col_sums[2:12])
            print(f'  Columns 0-1 (PL - Heavy): {pl_sum} ({100*pl_sum/total:.1f}%)')
            print(f'  Columns 2-11 (VL - Light): {vl_sum} ({100*vl_sum/total:.1f}%)')
            print(f'\nMapping Strategy for Mode 3:')
            print(f'  Vehicle Class 1 (VL - Light vehicles): Sum of columns 2-11')
            print(f'  Vehicle Class 2 (PL - Heavy vehicles): Sum of columns 0-1')
            
        elif detected_mode == 4:
            # Mode 4: Speed classes mapping
            print(f'  Column assignments (Speed classes in km/h):')
            for i in range(12):
                print(f'    Column {i:2d}: {SPEED_CLASSES[i]:3d} km/h -> {col_sums[i]:6d} ({100*col_sums[i]/total:5.1f}%)')
            print(f'\nMapping Strategy for Mode 4:')
            print(f'  Keep all 12 columns representing speed classes 30-150 km/h')
            print(f'  Data represents vehicle distribution by speed and direction')

print('\n' + '=' * 90)
print('NEXT STEP: Apply mode-specific mapping to create vehicle class aggregations')
print('=' * 90)
