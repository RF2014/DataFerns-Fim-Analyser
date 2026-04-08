import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'

print('=== Testing sensor pairing strategies ===\n')

# Try treating sensors 1+2 as Sens1, sensors 3+4 as Sens2
# With inverted mapping (cols 2-11 = VL)
df, meta = mod.parse_fim_file(path, vl_pl_mapping={'columns': list(range(2,12))})

# Group by sensor pairs
df['sensor_pair'] = df['sensor_id'].apply(lambda x: 'Sens 1' if x <= 2 else 'Sens 2')

print('Strategy: 1+2=Sens1, 3+4=Sens2, cols 2-11=VL')
summary = df.groupby(['sensor_pair', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
print(summary)

# Also show individual sensors
print('\nIndividual sensors (cols 2-11=VL):')
summary2 = df.groupby(['sensor_id', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
print(summary2)

total = df.groupby('vehicle_class')['count'].sum()
print(f"\nTotal: VL={total.get('VL',0)}, PL={total.get('PL',0)}")
print('\nExpected:')
print('Sens 1: VL=1406, PL=37')
print('Sens 2: VL=1481, PL=44')
print('Total: VL=2887, PL=81')
