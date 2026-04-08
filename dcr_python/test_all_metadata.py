import sys
sys.path.insert(0, 'src')
from core.fim_parser import parse_fim_file
from datetime import datetime, timedelta

files = [
    (r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim', 'C01.fim'),
    (r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM', 'FIME0003.FIM'),
    (r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM', 'FIME0004.FIM'),
    (r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM', 'MIX02.FIM'),
]

for file_path, file_name in files:
    try:
        df, meta = parse_fim_file(file_path)
        
        print(f'\n=== {file_name} ===')
        print(f'Start Date/Time: {meta["day"]:02d}/{meta["month"]:02d}/{meta["year"]} at {meta["start_hour"]:02d}:{meta["start_minute"]:02d}')
        
        # Calculate end date
        start_dt = datetime(meta['year'], meta['month'], meta['day'], meta['start_hour'], meta['start_minute'])
        freq = meta['interval_minutes']
        num_measurements = len(df['timestamp'].unique())
        end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))
        print(f'End Date/Time: {end_dt.strftime("%d/%m/%Y at %H:%M")}')
        
        # Frequency
        print(f'Frequency: {freq} minutes')
        
        # Mode interpretation
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
        
        # Vehicle classes and directions
        print(f'Vehicle Classes: {df["vehicle_class"].nunique()}')
        print(f'Directions: {len(df["direction"].unique())}')
        print(f'Mode: {mode}')
        print(f'Duration: {(end_dt - start_dt).days} days, {((end_dt - start_dt).seconds // 3600)} hours')
        print(f'Total Measurements: {num_measurements}')
        
    except Exception as e:
        print(f'\n=== {file_name} ===')
        print(f'ERROR: {str(e)}')
