from src.core.fim_parser import parse_fim_file
from datetime import time

df, metadata = parse_fim_file('C:\\DCR4402\\FIM\\C01.fim')

if df is not None:
    print('=== Campaign Period Analysis (10:00-22:00) ===\n')
    
    # Filter for campaign hours (10:00-22:00)
    df['hour'] = df['timestamp'].dt.hour
    campaign_df = df[(df['hour'] >= 10) & (df['hour'] <= 22)]
    
    print(f'Campaign rows (10:00-22:00): {len(campaign_df)} out of {len(df)}')
    print(f'Expected: {4 * 12 * 12} rows (4 sensors × 12h × 12 rows/hour)')
    
    for sensor_id in sorted(df['sensor_id'].unique()):
        sensor_campaign = campaign_df[campaign_df['sensor_id'] == sensor_id]
        vl_total = sensor_campaign[sensor_campaign['vehicle_class'] == 'VL']['count'].sum()
        pl_total = sensor_campaign[sensor_campaign['vehicle_class'] == 'PL']['count'].sum()
        print(f'\nSensor {sensor_id}:')
        print(f'  VL: {vl_total}')
        print(f'  PL: {pl_total}')
        print(f'  Total: {vl_total + pl_total}')
    
    print(f'\n=== Expected Totals (from campaign data) ===')
    print(f'Sens 1: VL=15662, PL=1856, Total=17518')
    print(f'Sens 2: VL=13586, PL=2167, Total=15753')
else:
    print('✗ Parser failed')
