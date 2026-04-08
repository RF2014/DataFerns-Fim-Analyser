"""
Debug: Check what's in current_metadata when page 4 is called
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dcr_python', 'src'))

# This script will be used to inject debug output into fim_loader

debug_code = '''
# DEBUG: Add this to the beginning of _add_mean_speed_analysis_page_to_pdf method
print("\\n=== DEBUG PAGE 4 MEAN SPEED ===")
meta = self.current_metadata
print(f"meta type: {type(meta)}")
print(f"meta keys: {list(meta.keys()) if meta else 'NONE'}")
raw_data = meta.get('raw_data', []) if meta else []
sensor_map = meta.get('sensor_map', {}) if meta else {}
num_sensors = meta.get('num_sensors', 0) if meta else 0
rows_per_block = meta.get('rows_per_block', 0) if meta else 0
speed_bin_centers = meta.get('speed_bin_centers', []) if meta else []
freq = meta.get('freq', 15) if meta else 15

print(f"raw_data: {'EMPTY' if not raw_data else f'{len(raw_data)} rows'}")
print(f"sensor_map: {sensor_map}")
print(f"num_sensors: {num_sensors}")
print(f"rows_per_block: {rows_per_block}")
print(f"speed_bin_centers: {speed_bin_centers}")
print(f"freq: {freq}")
print(f"analysis_start_dt: {self.analysis_start_dt}")
print(f"Condition check (raw_data and sensor_map and speed_bin_centers): {bool(raw_data and sensor_map and speed_bin_centers)}")
if raw_data:
    print(f"First raw_data row: {raw_data[0]}")
    print(f"Type of first row: {type(raw_data[0])}")
'''

print("Debug code to add to _add_mean_speed_analysis_page_to_pdf:")
print(debug_code)
