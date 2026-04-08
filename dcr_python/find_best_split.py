import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'

print('=== Testing different VL/PL column mappings ===\n')

# Expected totals: Sens1 VL=1406 PL=37, Sens2 VL=1481 PL=44
# Total: VL=2887, PL=81

mappings = [
    ([0, 1], 'Default: cols 0-1 = VL'),
    ([2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'Inverted: cols 2-11 = VL'),
    ([0], 'cols 0 = VL'),
    ([1], 'cols 1 = VL'),
    ([0, 1, 2], 'cols 0-2 = VL'),
]

for vl_cols, desc in mappings:
    df, meta = mod.parse_fim_file(path, vl_pl_mapping={'columns': vl_cols})
    if df is None:
        continue
    
    total = df.groupby('vehicle_class')['count'].sum()
    vl_total = total.get('VL', 0)
    pl_total = total.get('PL', 0)
    
    # Calculate error from expected
    error = abs(vl_total - 2887) + abs(pl_total - 81)
    
    print(f'{desc}')
    print(f'  VL={vl_total}, PL={pl_total} (error: {error})')
    
    if error < 10:
        print('  ✓ MATCH!')
        # Show per-sensor breakdown
        summary = df.groupby(['sensor_id', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
        print('  Per sensor:')
        print(summary)
    print()

print('\n=== EXPECTED ===')
print('Total: VL=2887, PL=81')
print('Sens 1: VL=1406, PL=37')
print('Sens 2: VL=1481, PL=44')
