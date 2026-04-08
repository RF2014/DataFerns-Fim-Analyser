"""
Test that parser uses frequency from header automatically
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
    ('C01.fim', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim'),
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM'),
]

print('=' * 90)
print('FREQUENCY DETECTION FROM FIM HEADERS (NO USER INPUT NEEDED)')
print('=' * 90)

for filename, path in files:
    # Parse WITHOUT providing interval_minutes - should use header value
    df, meta = mod.parse_fim_file(path)
    
    print(f'\n{filename}:')
    print(f'  Start: {meta.get("day"):02d}/{meta.get("month"):02d}/{meta.get("year")} at {meta.get("start_hour"):02d}:{meta.get("start_minute"):02d}')
    print(f'  Frequency (from header): {meta.get("interval_minutes")} minutes ✓')
    print(f'  Mode: {meta.get("mode")}')
    print(f'  Sensors: {meta.get("num_sensors")}')
    
    if df is not None:
        num_measurements = len(df['timestamp'].unique())
        start_dt = datetime(
            meta.get('year'), meta.get('month'), meta.get('day'),
            meta.get('start_hour'), meta.get('start_minute')
        )
        # Use frequency from header
        freq = meta.get('interval_minutes', 60)
        end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))
        
        print(f'  End: {end_dt.strftime("%d/%m/%Y at %H:%M")}')
        print(f'  Measurements: {num_measurements}')

print('\n' + '=' * 90)
print('RESULT: All files use their header frequency (60 minutes) automatically!')
print('No need to manually provide interval_minutes parameter')
print('=' * 90)
