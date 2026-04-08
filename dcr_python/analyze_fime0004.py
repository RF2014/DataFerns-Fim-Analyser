"""
Analyze FIME0004.FIM with 60-minute interval
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

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM'

# User provides the interval
USER_INTERVAL = 60  # minutes

print('=== FIME0004.FIM Analysis (60-minute interval) ===')

# Parse with user-provided interval
df, meta = mod.parse_fim_file(path, interval_minutes=USER_INTERVAL)

if df is not None and meta is not None:
    print('\n1. Start Date/Time (from FIM header):')
    start_date = f"{meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}"
    start_time = f"{meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}"
    print(f"   {start_date} at {start_time}")
    
    print(f'\n2. Measurement Frequency (user-provided):')
    print(f"   {USER_INTERVAL} minutes")
    
    print(f'\n3. Number of Measurements:')
    num_measurements = len(df['timestamp'].unique())
    print(f"   {num_measurements} unique timestamps")
    
    print(f'\n4. Calculated End Date/Time:')
    start_dt = datetime(
        meta.get('year'), meta.get('month'), meta.get('day'),
        meta.get('start_hour'), meta.get('start_minute')
    )
    
    # Calculate end time: start + (num_measurements - 1) * interval
    end_dt = start_dt + timedelta(minutes=USER_INTERVAL * (num_measurements - 1))
    
    print(f"   {end_dt.strftime('%d/%m/%Y at %H:%M')}")
    
    print(f'\n5. Campaign Duration:')
    duration = end_dt - start_dt
    hours = duration.total_seconds() / 3600
    days = hours / 24
    print(f"   {duration}")
    print(f"   {hours:.1f} hours ({days:.2f} days)")
    
    print(f'\n6. First 3 timestamps:')
    for ts in sorted(df['timestamp'].unique())[:3]:
        print(f"   {ts}")
    
    print(f'\n7. Last 3 timestamps:')
    for ts in sorted(df['timestamp'].unique())[-3:]:
        print(f"   {ts}")
    
    print(f'\n8. Metadata from header:')
    print(f"   Number of sensors: {meta.get('num_sensors')}")
    print(f"   Total data rows: {meta.get('num_data_rows')}")
    print(f"   Rows per block: {meta.get('rows_per_block')}")

else:
    print('Error: Could not parse file')
