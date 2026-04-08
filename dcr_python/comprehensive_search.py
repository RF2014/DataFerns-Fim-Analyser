import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'

print('=== Comprehensive search: all column splits + sensor combinations ===\n')

best_error = 999999
best_config = None

# Try all column splits
for split_at in range(1, 12):
    vl_cols = list(range(split_at))
    
    df, meta = mod.parse_fim_file(path, vl_pl_mapping={'columns': vl_cols})
    if df is None:
        continue
    
    # Test: Sensors 1 and 3 as Sens1 and Sens2
    sens1_df = df[df['sensor_id'] == 1]
    sens2_df = df[df['sensor_id'] == 3]
    
    sens1_vl = sens1_df[sens1_df['vehicle_class'] == 'VL']['count'].sum()
    sens1_pl = sens1_df[sens1_df['vehicle_class'] == 'PL']['count'].sum()
    sens2_vl = sens2_df[sens2_df['vehicle_class'] == 'VL']['count'].sum()
    sens2_pl = sens2_df[sens2_df['vehicle_class'] == 'PL']['count'].sum()
    
    error = abs(sens1_vl - 1406) + abs(sens1_pl - 37) + abs(sens2_vl - 1481) + abs(sens2_pl - 44)
    
    if error < best_error:
        best_error = error
        best_config = {
            'split': split_at,
            'vl_cols': vl_cols,
            'sens1_vl': sens1_vl,
            'sens1_pl': sens1_pl,
            'sens2_vl': sens2_vl,
            'sens2_pl': sens2_pl,
            'error': error
        }

print(f"Best configuration found:")
print(f"  VL columns: {best_config['vl_cols']}")
print(f"  Split at column: {best_config['split']}")
print(f"\nResults (Sensor 1 = Sens 1, Sensor 3 = Sens 2):")
print(f"  Sens 1: VL={best_config['sens1_vl']}, PL={best_config['sens1_pl']} (expected: VL=1406, PL=37)")
print(f"  Sens 2: VL={best_config['sens2_vl']}, PL={best_config['sens2_pl']} (expected: VL=1481, PL=44)")
print(f"  Total error: {best_config['error']}")

if best_config['error'] < 20:
    print("\n✓ EXCELLENT MATCH!")
elif best_config['error'] < 100:
    print("\n✓ GOOD MATCH!")
else:
    print("\n✗ No perfect match found")
