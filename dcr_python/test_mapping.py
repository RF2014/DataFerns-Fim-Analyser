import importlib.util
spec=importlib.util.spec_from_file_location('fp','src/core/fim_parser.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path=r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'
df, meta = mod.parse_fim_file(path)

print('=== METADATA EXTRACTED ===')
print(f"Date: {meta.get('day'):02d}/{meta.get('month'):02d}/{meta.get('year')}")
print(f"Time: {meta.get('start_hour'):02d}:{meta.get('start_minute'):02d}")
print(f"Interval: {meta.get('interval_minutes')} min")
print(f"Sensors: {meta.get('num_sensors')}")

print('\n=== EXPECTED ===')
print('Date: 06/10/2025')
print('Time: 15:00')
print('Interval: 60 min')

if df is not None:
    print(f'\n=== DataFrame ===')
    print(f'Shape: {df.shape}')
    
    summary = df.groupby(['sensor_id', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
    print('\nTotals by sensor (default VL=cols 0-1):')
    print(summary)
    
    total = df.groupby('vehicle_class')['count'].sum()
    print('\nTotal:')
    print(f'  VL (Light): {total.get("VL", 0)}')
    print(f'  PL (Heavy): {total.get("PL", 0)}')
    
    print('\n=== EXPECTED ===')
    print('Sens 1: VL=1406, PL=37')
    print('Sens 2: VL=1481, PL=44')
    print('Total: VL=2887, PL=81')
