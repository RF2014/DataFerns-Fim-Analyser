"""
Calculate duration of FIM files
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
print('FIM FILE DURATION ANALYSIS')
print('=' * 90)

for filename, path in files:
    df, meta = mod.parse_fim_file(path)
    
    if df is not None and meta is not None:
        start_dt = datetime(
            meta.get('year'), meta.get('month'), meta.get('day'),
            meta.get('start_hour'), meta.get('start_minute')
        )
        
        num_measurements = len(df['timestamp'].unique())
        freq = meta.get('interval_minutes', 60)
        end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))
        
        duration = end_dt - start_dt
        total_hours = duration.total_seconds() / 3600
        total_days = total_hours / 24
        
        print(f'\n{filename}:')
        start_str = start_dt.strftime('%d/%m/%Y at %H:%M')
        end_str = end_dt.strftime('%d/%m/%Y at %H:%M')
        print(f'  Start: {start_str}')
        print(f'  End:   {end_str}')
        print(f'  Duration: {total_days:.1f} days ({int(total_hours)} hours)')
        print(f'  Measurements: {num_measurements}')

print('\n' + '=' * 90)
