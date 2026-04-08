#!/usr/bin/env python3
"""Test the flexible FIM parser."""
import pandas as pd
from src.core.fim_parser import parse_fim_file

fim_path = r'C:\DCR4402\FIM\C01.fim'
df, metadata = parse_fim_file(fim_path)

print('=== FIM Parser Results ===')
print('\nMetadata:')
for k, v in metadata.items():
    print(f'  {k}: {v}')

print(f'\nDataFrame shape: {df.shape}')
print(f'Columns: {list(df.columns)}')

# Filter for 10:00-22:00 window (12 hours from start)
start_time = df['timestamp'].min()
end_time = start_time + pd.Timedelta(hours=12)

start_str = start_time.strftime("%Y-%m-%d %H:%M")
end_str = end_time.strftime("%H:%M")
print(f'\n=== Campaign Window: {start_str} to {end_str} ===')

for sensor_id in sorted(df['sensor_id'].unique()):
    sensor_data = df[(df['sensor_id'] == sensor_id) & (df['timestamp'] >= start_time) & (df['timestamp'] < end_time)]
    
    vl = sensor_data[sensor_data['vehicle_class'] == 'VL']['count'].sum()
    pl = sensor_data[sensor_data['vehicle_class'] == 'PL']['count'].sum()
    total = vl + pl
    
    print(f'\nSensor {sensor_id}:')
    print(f'  VL: {vl:,}')
    print(f'  PL: {pl:,}')
    print(f'  Total: {total:,}')

print(f'\n=== Expected Campaign Totals ===')
print('Sens 1: VL=15,662  PL=1,856  Total=17,518')
print('Sens 2: VL=13,586  PL=2,167  Total=15,753')
print('Grand Total: 33,271')
