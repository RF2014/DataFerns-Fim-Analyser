import sys
import re
sys.path.insert(0, 'src')

# Read the file directly
file_path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM'
with open(file_path, 'r') as f:
    header_line = f.readline()

tokens = re.findall(r'\d+', header_line)
values = [int(t) for t in tokens]

print('Token positions:')
for i, v in enumerate(values):
    print(f'{i:2d}: {v}')

# The pattern: 25, 12, 1, 10, 0, 60, 2, [?], 2360
# At index 5: YY=25, MM=12, DD=1, HH=10, MM=0, Interval=60, Sensors=2
# At index 11: This is where things get weird
# At index 12: 2360 (which is definitely wrong for mode)

# Looking at the header string directly:
print('\nBreaking down header parts:')
header = header_line.strip()
parts = header.split('.')
for i, p in enumerate(parts):
    print(f'{i:2d}: {repr(p)}')

# Based on the structure, the Mode seems to be in a strange position
# Let me check if the mode is actually at index 11 (which is 2)
print(f'\nAt index 11: {values[11]} (this might be the mode)')
