import sys
import re
sys.path.insert(0, 'src')

file_path_c01 = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim'
with open(file_path_c01, 'r') as f:
    header_c01 = f.readline()

print(f'C01 header: {repr(header_c01)}')

tokens_c01 = re.findall(r'\d+', header_c01)
values_c01 = [int(t) for t in tokens_c01]

print(f'C01 values: {values_c01}')
print(f'Positions:  {list(range(len(values_c01)))}')

# Find 4-digit year
for i, v in enumerate(values_c01):
    if 1900 <= v <= 2100:
        print(f'Found 4-digit year at index {i}: {v}')
        print(f'  year_idx+5: {values_c01[i+5]} (interval)')
        print(f'  year_idx+6: {values_c01[i+6]} (sensors)')
        if i+7 < len(values_c01):
            print(f'  year_idx+7: {values_c01[i+7]} (mode?)')
