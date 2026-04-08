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
df, meta = mod.parse_fim_file(path)

print('=== FIME0003.FIM Analysis ===')
print(f"\nMetadata from header:")
print(f"  Start Date: {meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}")
print(f"  Start Time: {meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}")
print(f"  Interval: {meta.get('interval_minutes')} minutes")
print(f"  Number of sensors: {meta.get('num_sensors')}")

if df is not None:
    print(f"\nDataFrame analysis:")
    print(f"  Total rows: {len(df)}")
    print(f"  Rows per sensor: {len(df) // meta.get('num_sensors', 1)}")
    
    # Get time range from actual data
    timestamps = df['timestamp'].unique()
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    
    print(f"\nActual data timestamps:")
    print(f"  Start: {start_time}")
    print(f"  End: {end_time}")
    
    duration = end_time - start_time
    hours = duration.total_seconds() / 3600
    days = hours / 24
    
    print(f"\nDuration:")
    print(f"  {duration}")
    print(f"  {hours:.1f} hours")
    print(f"  {days:.1f} days")
    
    # Count unique timestamps
    num_measurements = len(timestamps)
    print(f"\nMeasurements:")
    print(f"  Total unique timestamps: {num_measurements}")
    print(f"  Interval from metadata: {meta.get('interval_minutes')} minutes")
    if num_measurements > 1:
        calc_interval = duration.total_seconds() / 60 / (num_measurements - 1)
        print(f"  Calculated interval: {calc_interval:.1f} minutes (avg)")
    
    print(f"\nFirst 5 timestamps:")
    for ts in sorted(timestamps)[:5]:
        print(f"  {ts}")
    
    print(f"\nLast 5 timestamps:")
    for ts in sorted(timestamps)[-5:]:
        print(f"  {ts}")

print("\n=== EXPECTED (from Excel files) ===")
print("  Start: 06/10/2025 at 15:00")
print("  End: 23/10/2025 at 13:00")
print("  Duration: ~17 days, 22 hours")
print("  Interval: 60 minutes")
