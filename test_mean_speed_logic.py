"""
Debug script to trace page 4 mean speed calculation logic
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dcr_python', 'src'))

from core.fim_parser import parse_fim_file
from datetime import datetime, timedelta
import numpy as np

# Load a test file
test_file = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\GUI\test_files\FIM_E0001.dat'

if os.path.exists(test_file):
    print(f"Loading: {test_file}\n")
    df, metadata = parse_fim_file(test_file)
    
    print("=== METADATA KEYS ===")
    print(f"Keys in metadata: {list(metadata.keys())}\n")
    
    print("=== KEY VALUES ===")
    print(f"num_sensors: {metadata.get('num_sensors')}")
    print(f"rows_per_block: {metadata.get('rows_per_block')}")
    print(f"num_data_rows: {metadata.get('num_data_rows')}")
    print(f"speed_bin_centers: {metadata.get('speed_bin_centers')}")
    print(f"freq: {metadata.get('freq')}")
    print(f"sensor_map: {metadata.get('sensor_map')}\n")
    
    raw_data = metadata.get('raw_data', [])
    sensor_map = metadata.get('sensor_map', {})
    speed_bin_centers = metadata.get('speed_bin_centers', [])
    num_sensors = metadata.get('num_sensors', 0)
    rows_per_block = metadata.get('rows_per_block', 0)
    freq = metadata.get('freq', 15)
    
    print(f"raw_data length: {len(raw_data)}")
    if raw_data:
        print(f"First 3 rows of raw_data:")
        for i, row in enumerate(raw_data[:3]):
            print(f"  Row {i}: {row}")
    
    print(f"\nDataFrame shape: {df.shape}")
    print(f"DataFrame columns: {list(df.columns)}")
    print(f"DataFrame head:\n{df.head(10)}\n")
    
    # Now test the mean speed calculation logic
    print("=== TESTING MEAN SPEED CALCULATION ===\n")
    
    analysis_start_dt = datetime(
        metadata['year'], metadata['month'], metadata['day'],
        metadata['start_hour'], metadata['start_minute']
    )
    
    print(f"Analysis start: {analysis_start_dt}")
    print(f"Frequency (minutes): {freq}\n")
    
    # Test the current logic
    vl_numerator = np.zeros(24)
    vl_denominator = np.zeros(24)
    pl_numerator = np.zeros(24)
    pl_denominator = np.zeros(24)
    
    print(f"Processing {num_sensors} sensors with {rows_per_block} rows each:")
    for sensor_id in range(num_sensors):
        start_row = sensor_id * rows_per_block
        end_row = min(start_row + rows_per_block, len(raw_data))
        
        if start_row >= len(raw_data):
            break
        
        block = raw_data[start_row:end_row]
        sensor_info = sensor_map.get(sensor_id, {})
        vehicle_class = sensor_info.get('class', 'ALL')
        
        print(f"  Sensor {sensor_id}: class={vehicle_class}, rows={len(block)}")
        
        # Just process first 3 rows
        for row_idx, row_vals in enumerate(block[:3]):
            timestamp = analysis_start_dt + timedelta(minutes=freq * row_idx)
            hour = timestamp.hour
            
            print(f"    Row {row_idx}: time={timestamp.strftime('%H:%M')}, hour={hour}")
            print(f"      Bin values: {row_vals}")
            print(f"      Speed centers: {speed_bin_centers}")
            
            row_total = 0
            for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                count = int(row_vals[i]) if i < len(row_vals) else 0
                speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                row_total += count
                
                if vehicle_class == 'VL' or vehicle_class == 'ALL':
                    vl_numerator[hour] += count * speed_center
                    vl_denominator[hour] += count
                if vehicle_class == 'PL' or vehicle_class == 'ALL':
                    pl_numerator[hour] += count * speed_center
                    pl_denominator[hour] += count
            
            print(f"      Total count in row: {row_total}")
    
    print(f"\nVL mean by hour (first 6 hours):")
    for hour in range(6):
        if vl_denominator[hour] > 0:
            mean = vl_numerator[hour] / vl_denominator[hour]
            print(f"  Hour {hour:02d}: numerator={vl_numerator[hour]:.0f}, count={vl_denominator[hour]:.0f}, mean={mean:.1f} km/h")
        else:
            print(f"  Hour {hour:02d}: NO DATA")
    
    print(f"\nPL mean by hour (first 6 hours):")
    for hour in range(6):
        if pl_denominator[hour] > 0:
            mean = pl_numerator[hour] / pl_denominator[hour]
            print(f"  Hour {hour:02d}: numerator={pl_numerator[hour]:.0f}, count={pl_denominator[hour]:.0f}, mean={mean:.1f} km/h")
        else:
            print(f"  Hour {hour:02d}: NO DATA")

else:
    print(f"Test file not found: {test_file}")
    print("Please ensure the file exists or adjust the path.")
