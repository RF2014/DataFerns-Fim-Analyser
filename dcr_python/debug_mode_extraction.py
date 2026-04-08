import sys
sys.path.insert(0, 'src')

file_path = r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM'

# Manually trace through the parser logic
import re
with open(file_path, 'r') as f:
    header_line = f.readline()

tokens = re.findall(r'\d+', header_line)
values = [int(t) for t in tokens]

print(f'All values: {values}')

# Find 2-digit year pattern
year_idx = None
for i in range(len(values) - 6):
    if (0 <= values[i] <= 99 and 
        1 <= values[i+1] <= 12 and 
        1 <= values[i+2] <= 31 and 
        0 <= values[i+3] <= 23 and 
        0 <= values[i+4] <= 59 and
        values[i+5] in [15, 30, 60, 1440]):
        print(f'Candidate year pattern at index {i}: {values[i:i+6]}')

# We know the answer is at index 5
year_idx = 5
print(f'\nUsing year_idx = {year_idx}')
print(f'year_idx + 6 = {year_idx + 6}: {values[year_idx + 6]}')
print(f'year_idx + 7 = {year_idx + 7}: {values[year_idx + 7]}')
print(f'year_idx + 8 = {year_idx + 8}: {values[year_idx + 8]}')

# The algorithm should find mode_val = 2 (at year_idx + 6 + 1 = 12? No...)
# Let me check what's at year_idx + 6
sensors = values[year_idx + 6]
print(f'Sensors at year_idx + 6: {sensors}')

# Then offset = 1 would give us year_idx + 7
print(f'At offset 1 (year_idx + 7): {values[year_idx + 7]}')  # This is 2 - the mode!
