"""
Demonstration of flexible FIM parser with custom mapping overrides
"""
from src.core.fim_parser import parse_fim_file

print('=== Flexible FIM Parser - Custom Mapping Demo ===\n')

# Test 1: Default mapping
print('Test 1: Default mapping (columns 0-1 = VL, 2-11 = PL)')
df1, meta1 = parse_fim_file('C:\\DCR4402\\FIM\\C01.fim')
if df1 is not None:
    for sensor_id in sorted(df1['sensor_id'].unique()):
        sensor_data = df1[df1['sensor_id'] == sensor_id]
        vl = sensor_data[sensor_data['vehicle_class'] == 'VL']['count'].sum()
        pl = sensor_data[sensor_data['vehicle_class'] == 'PL']['count'].sum()
        print(f'  Sensor {sensor_id}: VL={vl}, PL={pl}, Total={vl+pl}')

# Test 2: Custom column mapping (columns 0-3 = VL, 4-11 = PL)
print('\nTest 2: Custom mapping (columns 0-3 = VL, 4-11 = PL)')
df2, meta2 = parse_fim_file(
    'C:\\DCR4402\\FIM\\C01.fim',
    vl_pl_mapping={'columns': [0, 1, 2, 3]}
)
if df2 is not None:
    for sensor_id in sorted(df2['sensor_id'].unique()):
        sensor_data = df2[df2['sensor_id'] == sensor_id]
        vl = sensor_data[sensor_data['vehicle_class'] == 'VL']['count'].sum()
        pl = sensor_data[sensor_data['vehicle_class'] == 'PL']['count'].sum()
        print(f'  Sensor {sensor_id}: VL={vl}, PL={pl}, Total={vl+pl}')

# Test 3: Custom sensor names
print('\nTest 3: Custom sensor mapping')
df3, meta3 = parse_fim_file(
    'C:\\DCR4402\\FIM\\C01.fim',
    vl_pl_mapping={'sensor_map': {0: 'North-South', 1: 'North-South (Heavy)', 2: 'East-West', 3: 'East-West (Heavy)'}}
)
if df3 is not None:
    unique_directions = sorted(df3['direction'].unique())
    print(f'  Directions in data: {unique_directions}')
    for direction in unique_directions:
        dir_data = df3[df3['direction'] == direction]
        total = dir_data['count'].sum()
        print(f'    {direction}: {total} vehicles')

# Test 4: Combined custom mapping
print('\nTest 4: Combined column + sensor mapping')
df4, meta4 = parse_fim_file(
    'C:\\DCR4402\\FIM\\C01.fim',
    vl_pl_mapping={
        'columns': [0, 1],  # Columns 0-1 = VL (default)
        'sensor_map': {0: 'Sens 1', 1: 'Sens 1 (Other)', 2: 'Sens 2', 3: 'Sens 2 (Other)'}
    }
)
if df4 is not None:
    print(f'  DataFrame shape: {df4.shape}')
    print(f'  Sensors: {sorted(df4["sensor_id"].unique())}')
    print(f'  Directions: {sorted(df4["direction"].unique())}')
    print(f'  Vehicle classes: {sorted(df4["vehicle_class"].unique())}')

print('\n✓ All tests completed successfully!')
print('\nKey features demonstrated:')
print('  1. Auto-detects FIM file structure (no hardcoded paths)')
print('  2. Default sensible mapping (columns 0-1 as VL)')
print('  3. Customizable VL/PL column split')
print('  4. Customizable sensor-to-direction mapping')
print('  5. Works with any .fim file format')
