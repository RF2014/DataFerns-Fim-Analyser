import sys
import re
sys.path.insert(0, 'src')

# Read the file directly
file_path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM'
with open(file_path, 'r') as f:
    header_line = f.readline()

print(f'Header line: {repr(header_line)}')

# Try different patterns
print('\nUsing explicit character positions:')
parts = header_line.strip().split('.')
print(f'Parts split by dot: {parts}')
print(f'Number of parts: {len(parts)}')

# Look for date pattern: 25, 12, 01, 10, 00 = YY, MM, DD, HH, MM
tokens = re.findall(r'\d+', header_line)
values = [int(t) for t in tokens]
print(f'\nExtracted numeric tokens: {values}')

# The pattern seems to be: ... 25 12 01 10 00 0060 2 ...
# Which would be: YY MM DD HH MM Interval Sensors ...
# Let's find this pattern
for i in range(len(values) - 8):
    if (values[i] == 25 and values[i+1] == 12 and values[i+2] == 1 and 
        values[i+3] == 10 and values[i+4] == 0 and values[i+5] == 60):
        print(f'Found date pattern at index {i}')
        print(f'YY={values[i]}, MM={values[i+1]}, DD={values[i+2]}, ' +
              f'HH={values[i+3]}, MM={values[i+4]}, Interval={values[i+5]}, ' +
              f'Sensors={values[i+6] if i+6 < len(values) else "N/A"}, ' +
              f'Mode={values[i+7] if i+7 < len(values) else "N/A"}')
