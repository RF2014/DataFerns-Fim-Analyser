"""Test the flexible FIM parser"""
import pandas as pd
from src.core.fim_parser import parse_fim_file

fim_path = r'C:\DCR4402\FIM\C01.fim'
df, metadata = parse_fim_file(fim_path)

print('=== PARSE RESULT ===')
print(f'Metadata: year={metadata["year"]}, month={metadata["month"]}, day={metadata["day"]}')
print(f'Start: {metadata["start_hour"]:02d}:{metadata["start_minute"]:02d}, Sensors: {metadata["num_sensors"]}')
print(f'\nDataFrame shape: {df.shape}')
print(f'Columns: {list(df.columns)}')

# Validate against expected campaign totals
print('\n=== VALIDATION (10:00-22:00, 12 hours) ===')
start_time = df['timestamp'].min()
end_time = start_time + pd.Timedelta(hours=12)

for direction in ['Sens 1', 'Sens 2']:
    for vclass in ['VL', 'PL']:
        subset = df[(df['direction'] == direction) & 
                    (df['vehicle_class'] == vclass) &
                    (df['timestamp'] >= start_time) & 
                    (df['timestamp'] < end_time)]
        total = subset['count'].sum()
        print(f'{direction} {vclass}: {total}')

# Expected:
# Sens 1 VL: 15662, Sens 1 PL: 1856
# Sens 2 VL: 13586, Sens 2 PL: 2167
print('\nExpected:')
print('Sens 1 VL: 15662, Sens 1 PL: 1856')
print('Sens 2 VL: 13586, Sens 2 PL: 2167')
