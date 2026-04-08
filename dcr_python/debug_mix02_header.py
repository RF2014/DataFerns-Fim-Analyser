import sys
import re
sys.path.insert(0, 'src')

# Read the file directly
file_path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM'
with open(file_path, 'r') as f:
    header_line = f.readline()

print(f'Header line: {repr(header_line)}')
tokens = re.findall(r'\d+', header_line)
values = [int(t) for t in tokens]
print(f'Extracted tokens: {values}')
print(f'Number of tokens: {len(values)}')

# Find year pattern
for i in range(len(values) - 6):
    if 1900 <= values[i] <= 2100:
        print(f'Found 4-digit year at index {i}: {values[i]}')
        sensors = values[i+6] if i+6 < len(values) else 'N/A'
        mode = values[i+7] if i+7 < len(values) else 'N/A'
        print(f'At this index: year={values[i]}, month={values[i+1]}, day={values[i+2]}, ' +
              f'hour={values[i+3]}, min={values[i+4]}, interval={values[i+5]}, ' +
              f'sensors={sensors}, mode={mode}')
