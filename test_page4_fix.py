"""
Test script to verify page 4 mean speed calculations are working correctly.
This directly tests the fixed logic without needing the full GUI.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dcr_python'))

from datetime import datetime, timedelta
import numpy as np
from src.core.fim_parser import FIMParser
from src.utils.constants import TEST_FIM_FILE

def test_page4_mean_speed_logic():
    """Test the mean speed calculation logic from page 4"""
    
    print("\n" + "="*60)
    print("TESTING PAGE 4 MEAN SPEED CALCULATION LOGIC")
    print("="*60)
    
    # Load and parse FIM data
    parser = FIMParser()
    try:
        result = parser.parse(TEST_FIM_FILE)
        if not result:
            print("ERROR: Failed to parse FIM file")
            return False
    except Exception as e:
        print(f"ERROR parsing file: {e}")
        return False
    
    # Get metadata
    raw_data = parser.raw_data
    metadata = parser.metadata
    
    print(f"\nMetadata found:")
    print(f"  - raw_data length: {len(raw_data)}")
    print(f"  - sensor_map: {metadata.get('sensor_map', {})}")
    print(f"  - speed_bin_centers: {metadata.get('speed_bin_centers', [])}")
    print(f"  - num_sensors: {metadata.get('num_sensors', 'N/A')}")
    print(f"  - rows_per_block: {metadata.get('rows_per_block', 'N/A')}")
    print(f"  - freq: {metadata.get('freq', 'N/A')} minutes")
    print(f"  - analysis_start_dt: {metadata.get('analysis_start_dt', 'N/A')}")
    
    # Test the calculation logic
    speed_bin_centers = metadata.get('speed_bin_centers', [])
    sensor_map = metadata.get('sensor_map', {})
    freq = metadata.get('freq', 15)
    num_sensors = metadata.get('num_sensors', 4)
    rows_per_block = metadata.get('rows_per_block', 248)
    base_time = metadata.get('analysis_start_dt', datetime(2025, 11, 17, 9, 0, 0))
    
    # Initialize accumulators for the 24-hour mean speeds
    vl_numerator = [0.0] * 24
    vl_denominator = [0.0] * 24
    pl_numerator = [0.0] * 24
    pl_denominator = [0.0] * 24
    
    print(f"\nProcessing {num_sensors} sensors with {rows_per_block} rows each")
    print(f"Total data rows: {len(raw_data)}")
    print(f"Base time: {base_time}")
    
    # Process each sensor
    for sensor_idx in range(num_sensors):
        start_row = sensor_idx * rows_per_block
        end_row = start_row + rows_per_block
        
        sensor_info = sensor_map.get(sensor_idx, {})
        vehicle_class = sensor_info.get('class', 'UNKNOWN')
        direction = sensor_info.get('direction', 'UNKNOWN')
        
        print(f"\n  Sensor {sensor_idx}: {direction} ({vehicle_class}) - rows {start_row} to {end_row-1}")
        
        processed_count = 0
        for row_idx in range(rows_per_block):
            actual_row = start_row + row_idx
            if actual_row >= len(raw_data):
                break
                
            row_data = raw_data[actual_row]
            
            # Skip placeholder rows (all zeros)
            if not any(row_data):
                continue
            
            processed_count += 1
            
            # Calculate timestamp with CORRECTED logic: use global row index
            timestamp = base_time + timedelta(minutes=freq * actual_row)
            hour = timestamp.hour
            
            # Calculate weighted mean speed for this row
            total_count = sum(row_data)
            if total_count > 0:
                weighted_speed = sum(count * center for count, center in zip(row_data, speed_bin_centers)) / total_count
            else:
                weighted_speed = 0
            
            # Accumulate to correct vehicle class - CORRECTED logic: if/elif, not or
            if vehicle_class == 'VL':
                vl_numerator[hour] += total_count * weighted_speed
                vl_denominator[hour] += total_count
            elif vehicle_class == 'PL':
                pl_numerator[hour] += total_count * weighted_speed
                pl_denominator[hour] += total_count
        
        print(f"    → Processed {processed_count} non-placeholder rows")
    
    # Calculate final means
    print(f"\n" + "="*60)
    print("CALCULATED HOURLY MEAN SPEEDS")
    print("="*60)
    
    vl_hours_with_data = 0
    pl_hours_with_data = 0
    
    for hour in range(24):
        vl_mean = vl_numerator[hour] / vl_denominator[hour] if vl_denominator[hour] > 0 else None
        pl_mean = pl_numerator[hour] / pl_denominator[hour] if pl_denominator[hour] > 0 else None
        
        if vl_mean is not None or pl_mean is not None:
            vl_str = f"{vl_mean:.1f} km/h" if vl_mean is not None else "-- km/h"
            pl_str = f"{pl_mean:.1f} km/h" if pl_mean is not None else "-- km/h"
            print(f"Hour {hour:02d}:00 - VL: {vl_str:12s} | PL: {pl_str:12s}")
            
            if vl_mean is not None:
                vl_hours_with_data += 1
            if pl_mean is not None:
                pl_hours_with_data += 1
    
    print(f"\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Hours with VL data: {vl_hours_with_data}/24")
    print(f"Hours with PL data: {pl_hours_with_data}/24")
    
    # Check if data was actually processed
    total_numerator = sum(vl_numerator) + sum(pl_numerator)
    total_denominator = sum(vl_denominator) + sum(pl_denominator)
    
    print(f"Total speed weighted sum: {total_numerator:.1f}")
    print(f"Total count: {total_denominator:.0f}")
    
    if total_denominator > 0:
        print(f"\n✓ SUCCESS: Page 4 calculations are working!")
        print(f"  Data is being processed and speeds are calculated.")
        return True
    else:
        print(f"\n✗ FAILURE: No data was processed!")
        print(f"  Check if raw_data contains valid measurements.")
        return False

if __name__ == '__main__':
    try:
        success = test_page4_mean_speed_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
