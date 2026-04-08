import sys
sys.path.insert(0, 'src')
from core.fim_parser import parse_fim_file
from datetime import datetime, timedelta

# Test with C01.fim
file_path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim'
df, meta = parse_fim_file(file_path)

print('=== C01.fim Metadata ===')
print(f'Year: {meta["year"]}')
print(f'Month: {meta["month"]}')
print(f'Day: {meta["day"]}')
print(f'Start Hour: {meta["start_hour"]}')
print(f'Start Minute: {meta["start_minute"]}')
print(f'Interval (minutes): {meta["interval_minutes"]}')
print(f'Mode: {meta["mode"]}')
print(f'Num Sensors: {meta["num_sensors"]}')
print(f'Vehicle Classes: {df["vehicle_class"].nunique()}')
print(f'Directions: {df["direction"].nunique()}')
print(f'Unique Timestamps: {len(df["timestamp"].unique())}')

# Calculate dates
start_dt = datetime(meta['year'], meta['month'], meta['day'], meta['start_hour'], meta['start_minute'])
freq = meta['interval_minutes']
num_measurements = len(df['timestamp'].unique())
end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))

print(f'Start: {start_dt.strftime("%d/%m/%Y at %H:%M")}')
print(f'End: {end_dt.strftime("%d/%m/%Y at %H:%M")}')
print(f'Duration: {(end_dt - start_dt).days} days, {((end_dt - start_dt).seconds // 3600)} hours')

print('\n=== Mode Interpretation ===')
mode = meta['mode']
if mode == 2:
    print('Traffic Counts: Yes')
    print('Speed Measurement: No')
elif mode == 3:
    print('Traffic Counts: Yes')
    print('Speed Measurement: No')
elif mode == 4:
    print('Traffic Counts: Yes')
    print('Speed Measurement: Yes')
else:
    print('Traffic Counts: Unknown')
    print('Speed Measurement: Unknown')
