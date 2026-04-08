"""
Test mode detection for all FIM files
"""
import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
from datetime import datetime, timedelta
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

files = [
    ('C01.fim', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data\C01.fim', 60),
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM', 60),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM', 60),
]

MODE_DESCRIPTIONS = {
    1: "1 - TV Conf.",
    2: "2 - TV/PL",
    3: "3 - TV/PL",
    4: "4 - VL/PL",
    11: "11 - PL Conf.",
}

print('=' * 70)
print('FIM FILES ANALYSIS - MODE DETECTION')
print('=' * 70)

for filename, path, interval in files:
    df, meta = mod.parse_fim_file(path, interval_minutes=interval)
    
    print(f'\n{filename}:')
    print(f'  Start: {meta.get("day"):02d}/{meta.get("month"):02d}/{meta.get("year")} at {meta.get("start_hour"):02d}:{meta.get("start_minute"):02d}')
    
    # Calculate end date
    if df is not None:
        num_measurements = len(df['timestamp'].unique())
        start_dt = datetime(
            meta.get('year'), meta.get('month'), meta.get('day'),
            meta.get('start_hour'), meta.get('start_minute')
        )
        end_dt = start_dt + timedelta(minutes=interval * (num_measurements - 1))
        print(f'  End:   {end_dt.strftime("%d/%m/%Y at %H:%M")}')
    
    print(f'  Interval: {interval} minutes')
    print(f'  Sensors: {meta.get("num_sensors")}')
    
    if meta.get('mode') is not None:
        mode_num = meta['mode']
        mode_desc = MODE_DESCRIPTIONS.get(mode_num, f"Mode {mode_num}")
        print(f'  Mode: {mode_desc}')
    else:
        print(f'  Mode: Not detected')
    
    if df is not None:
        print(f'  Measurements: {len(df["timestamp"].unique())}')

print('\n' + '=' * 70)
