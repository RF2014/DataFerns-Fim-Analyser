"""
Analyze FIM files to deduce mode from structure
"""
import sys
for mod in list(sys.modules.keys()):
    if 'fim_parser' in mod or mod.startswith('src'):
        del sys.modules[mod]

import importlib.util
import re
spec = importlib.util.spec_from_file_location('fp', 'src/core/fim_parser.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

files = [
    ('C01.fim', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim'),
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM'),
]

print('=' * 80)
print('FIM FILE STRUCTURE ANALYSIS - MODE DEDUCTION')
print('=' * 80)

for filename, path in files:
    with open(path, 'r') as f:
        lines = f.readlines()
    
    print(f'\n{filename}:')
    
    # Parse header
    header = lines[0].strip()
    tokens = [int(t) for t in re.findall(r"\d+", header) if t]
    print(f'  Header tokens: {tokens}')
    
    # Count data rows (lines with exactly 12 values)
    data_rows = []
    for line in lines[2:]:
        values = [int(t) for t in re.findall(r"\d+", line) if t]
        if len(values) == 12:
            data_rows.append(values)
    
    print(f'  Total data rows: {len(data_rows)}')
    
    # Analyze data distribution across columns
    if data_rows:
        # Sum each column
        col_sums = [0] * 12
        for row in data_rows:
            for i in range(12):
                col_sums[i] += row[i]
        
        total = sum(col_sums)
        print(f'  Total vehicle count: {total}')
        print(f'  Column sums: {col_sums}')
        
        # Check distribution patterns
        first_two = sum(col_sums[0:2])
        last_ten = sum(col_sums[2:12])
        
        print(f'\n  Distribution analysis:')
        print(f'    Columns 0-1 (speed 30-40): {first_two} ({100*first_two/total:.1f}%)')
        print(f'    Columns 2-11 (speed 50-150): {last_ten} ({100*last_ten/total:.1f}%)')
        
        # Check if distribution is roughly even (Mode 4) or skewed (Mode 3)
        # Mode 4 (Speed): All 12 columns have significant counts (speed distribution)
        # Mode 3 (VL/PL): Columns might be split by vehicle class
        
        non_zero_cols = sum(1 for s in col_sums if s > 0)
        print(f'    Non-zero columns: {non_zero_cols}/12')
        
        # Calculate variation coefficient
        import statistics
        if non_zero_cols > 1:
            non_zero_values = [s for s in col_sums if s > 0]
            avg = statistics.mean(non_zero_values)
            stdev = statistics.stdev(non_zero_values) if len(non_zero_values) > 1 else 0
            cv = (stdev / avg) * 100 if avg > 0 else 0
            print(f'    Coefficient of variation: {cv:.1f}%')
            
            # Mode 4: Speed data typically has lower CV (more even distribution)
            # Mode 3: VL/PL might have higher CV if grouped
            if cv < 80:
                print(f'    → Suggests Mode 4 (Speed - more even distribution)')
            else:
                print(f'    → Suggests Mode 3 (VL/PL - uneven distribution)')

print('\n' + '=' * 80)
print('\nKNOWN INFORMATION:')
print('  C01.fim: Mode 4 - Speed on both directions, 12 speed classes')
print('  FIME0003/0004: Mode 3 - VL/PL simple counts on two directions')
print('=' * 80)
