"""
Test mode detection in FIM parser
"""
import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

files = [
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM'),
]

print('=== Mode Detection Test ===\n')

# Mode descriptions
MODE_DESCRIPTIONS = {
    1: "1 - TV Conf.",
    2: "2 - ?",
    3: "3 - TV/PL",
    4: "4 - VL/PL",
    11: "11 - PL Conf.",
}

for filename, path in files:
    df, meta = mod.parse_fim_file(path, interval_minutes=60)
    
    print(f'{filename}:')
    if meta and meta.get('mode') is not None:
        mode_num = meta['mode']
        mode_desc = MODE_DESCRIPTIONS.get(mode_num, f"Mode {mode_num}")
        print(f'  Mode: {mode_desc}')
    else:
        print(f'  Mode: Not detected')
    
    print(f'  Start: {meta.get("day"):02d}/{meta.get("month"):02d}/{meta.get("year")} at {meta.get("start_hour"):02d}:{meta.get("start_minute"):02d}')
    print(f'  Interval: {meta.get("interval_minutes")} minutes')
    print(f'  Sensors: {meta.get("num_sensors")}')
    print()
