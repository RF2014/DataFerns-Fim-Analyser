import sys
# Remove any cached modules
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
spec = importlib.util.spec_from_file_location('fim_parser_fresh', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'
df, meta = mod.parse_fim_file(path)

print('=== EXTRACTED FROM FRESH LOAD ===')
print(f"Date: {meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}")
print(f"Time: {meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}")
print(f"Interval: {meta.get('interval_minutes')} min")
print(f"Sensors: {meta.get('num_sensors')}")

print('\n=== EXPECTED ===')
print('Date: 06/10/2025')
print('Time: 15:00')
print('Interval: 60 min')

if df is not None:
    summary = df.groupby(['sensor_id', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
    total = df.groupby('vehicle_class')['count'].sum()
    print(f"\nTotal VL: {total.get('VL', 0)}, PL: {total.get('PL', 0)}")
    print("Expected: VL=2887, PL=81")
