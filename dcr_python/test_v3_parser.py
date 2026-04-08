from src.core.fim_parser import parse_fim_file

df, metadata = parse_fim_file('C:\\DCR4402\\FIM\\C01.fim')

if df is not None:
    print('✓ Parser successful')
    print(f'  Rows: {len(df)}')
    num_sensors = metadata.get('num_sensors', 'unknown')
    print(f'  Sensors detected: {num_sensors}')
    rows_per_block = metadata.get('rows_per_block', 'unknown')
    print(f'  Rows per block: {rows_per_block}')
    year = metadata.get('year')
    month = metadata.get('month')
    day = metadata.get('day')
    print(f'  Date: {year}-{month}-{day}')
    start_hour = metadata.get('start_hour')
    start_minute = metadata.get('start_minute')
    print(f'  Start time: {start_hour}:{start_minute:02d}')
    vl_cols = metadata.get('vl_columns')
    pl_cols = metadata.get('pl_columns')
    print(f'  VL columns: {vl_cols}')
    print(f'  PL columns: {pl_cols}')
    print(f'\nDataFrame shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    print(f'\nFirst 10 rows:')
    print(df.head(10))
    print(f'\nSensors in data: {sorted(df["sensor_id"].unique())}')
    print(f'Directions: {df["direction"].unique()}')
    print(f'Vehicle classes: {df["vehicle_class"].unique()}')
    
    # Validate data
    print(f'\n=== Data Validation ===')
    for sensor_id in sorted(df['sensor_id'].unique()):
        sensor_df = df[df['sensor_id'] == sensor_id]
        vl_total = sensor_df[sensor_df['vehicle_class'] == 'VL']['count'].sum()
        pl_total = sensor_df[sensor_df['vehicle_class'] == 'PL']['count'].sum()
        print(f'Sensor {sensor_id}: VL={vl_total}, PL={pl_total}, Total={vl_total + pl_total}')
else:
    print('✗ Parser failed')
