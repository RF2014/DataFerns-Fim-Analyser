"""Verify FIME0001.FIM metadata and TMJ values"""
import sys
sys.path.insert(0, 'src')
import pandas as pd
from core.fim_parser import parse_fim_file
from datetime import datetime, timedelta

path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0001.FIM'
df, meta = parse_fim_file(path)

print('Header metadata:')
print(f'  Year: {meta.get("year")}')
print(f'  Month: {meta.get("month")}')
print(f'  Day: {meta.get("day")}')
print(f'  Start hour: {meta.get("start_hour")}')
print(f'  Start minute: {meta.get("start_minute")}')
print(f'  Interval: {meta.get("interval_minutes")} minutes')
print(f'  Num sensors: {meta.get("num_sensors")}')
print(f'  Rows per block: {meta.get("rows_per_block")}')

start_dt = datetime(meta['year'], meta['month'], meta['day'], 
                    meta['start_hour'], meta['start_minute'])
num_measurements = len(df['timestamp'].unique())
end_dt = start_dt + timedelta(minutes=meta['interval_minutes'] * (num_measurements - 1))

print(f'\nStart datetime: {start_dt.strftime("%d/%m/%Y at %H:%M")}')
print(f'End datetime: {end_dt.strftime("%d/%m/%Y at %H:%M")}')
print(f'Total measurements: {num_measurements}')
print(f'Directions: {list(df["direction"].unique())}')

df = df.copy()
df['date'] = df['timestamp'].dt.date
tbl = df.groupby(['direction', 'vehicle_class', 'date'])['count'].sum().groupby(['direction', 'vehicle_class']).mean()

print(f'\nTMJ (daily averages):')
print(tbl)

# Speed measurement check
bins = meta.get('speed_bins', [])
raw = meta.get('raw_data', [])
print(f'\nSpeed bins: {bins}')
print(f'Speed measurement available: {"Yes" if (len(bins) >= 4 and max(bins) >= 80 and raw) else "No"}')
