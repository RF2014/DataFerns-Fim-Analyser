"""
Test corrected logic: user provides interval, parser calculates end date
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

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'

# User provides the interval (e.g., 60 minutes as stated in Excel files)
USER_INTERVAL = 60  # minutes

print('=== CORRECTED LOGIC TEST ===')
print(f'User-provided interval: {USER_INTERVAL} minutes')
print()

# Parse with user-provided interval
df, meta = mod.parse_fim_file(path, interval_minutes=USER_INTERVAL)

if df is not None and meta is not None:
    print('1. Start Date/Time (from FIM header):')
    start_date = f"{meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}"
    start_time = f"{meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}"
    print(f"   {start_date} at {start_time}")
    
    print(f'\n2. Measurement Frequency (user-provided):')
    print(f"   {USER_INTERVAL} minutes")
    
    print(f'\n3. Number of Measurements (from data):')
    num_measurements = len(df['timestamp'].unique())
    print(f"   {num_measurements} unique timestamps")
    
    print(f'\n4. Calculated End Date/Time:')
    start_dt = datetime(
        meta.get('year'), meta.get('month'), meta.get('day'),
        meta.get('start_hour'), meta.get('start_minute')
    )
    
    # Calculate end time: start + (num_measurements - 1) * interval
    # Note: -1 because first measurement is at t=0
    end_dt = start_dt + timedelta(minutes=USER_INTERVAL * (num_measurements - 1))
    
    print(f"   {end_dt.strftime('%d/%m/%Y at %H:%M')}")
    
    print(f'\n5. Campaign Duration:')
    duration = end_dt - start_dt
    hours = duration.total_seconds() / 3600
    days = hours / 24
    print(f"   {duration}")
    print(f"   {hours:.1f} hours ({days:.2f} days)")
    
    print(f'\n6. First 5 timestamps (with {USER_INTERVAL}-min intervals):')
    for ts in sorted(df['timestamp'].unique())[:5]:
        print(f"   {ts}")
    
    print(f'\n7. Last 5 timestamps:')
    for ts in sorted(df['timestamp'].unique())[-5:]:
        print(f"   {ts}")
    
    print('\n=== COMPARISON WITH EXPECTED ===')
    print('Expected (from Excel):')
    print('  Start: 06/10/2025 at 15:00')
    print('  End: 23/10/2025 at 13:00')
    print('  Interval: 60 minutes')
    print('  Duration: ~17 days, 22 hours')
    
    # Calculate expected number of measurements
    expected_start = datetime(2025, 10, 6, 15, 0)
    expected_end = datetime(2025, 10, 23, 13, 0)
    expected_duration = expected_end - expected_start
    expected_num = int(expected_duration.total_seconds() / 60 / USER_INTERVAL) + 1
    
    print(f'\nExpected number of measurements: {expected_num}')
    print(f'Actual number in file: {num_measurements}')
    print(f'Difference: {expected_num - num_measurements} measurements missing')
    print(f'\nConclusion: FIME0003.FIM contains only partial campaign data')
    print(f'            ({num_measurements}/{expected_num} measurements = {100*num_measurements/expected_num:.1f}%)')

else:
    print('Error: Could not parse file')
