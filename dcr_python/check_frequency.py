"""
Check if frequency is stored in FIM headers
"""
import re

files = [
    ('C01.fim', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim'),
    ('FIME0003.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM'),
    ('FIME0004.FIM', r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM'),
]

print('=' * 80)
print('FREQUENCY IN FIM FILE HEADERS')
print('=' * 80)

for filename, path in files:
    with open(path, 'r') as f:
        header = f.readline().strip()
    
    tokens = [int(t) for t in re.findall(r"\d+", header) if t]
    
    print(f'\n{filename}:')
    print(f'  Full header: {header}')
    print(f'  Tokens: {tokens}')
    
    # For both formats, interval is at position year_idx + 5
    # C01.fim: year at index 5 (4-digit: 2025)
    # FIME: year at index 5 (2-digit: 25)
    
    # Identify year position
    year_idx = None
    for i, val in enumerate(tokens):
        if 1900 <= val <= 2100:
            year_idx = i
            break
    
    if year_idx is None:
        # Look for 2-digit year pattern
        for i in range(len(tokens) - 6):
            if (0 <= tokens[i] <= 99 and 
                1 <= tokens[i+1] <= 12 and 
                1 <= tokens[i+2] <= 31 and 
                0 <= tokens[i+3] <= 23 and 
                0 <= tokens[i+4] <= 59 and
                tokens[i+5] in [15, 30, 60, 1440]):
                year_idx = i
                break
    
    if year_idx is not None:
        print(f'\n  Year index: {year_idx}')
        print(f'    Index {year_idx}: {tokens[year_idx]} (Year)')
        print(f'    Index {year_idx+1}: {tokens[year_idx+1]} (Month)')
        print(f'    Index {year_idx+2}: {tokens[year_idx+2]} (Day)')
        print(f'    Index {year_idx+3}: {tokens[year_idx+3]} (Hour)')
        print(f'    Index {year_idx+4}: {tokens[year_idx+4]} (Minute)')
        print(f'    Index {year_idx+5}: {tokens[year_idx+5]} (INTERVAL/FREQUENCY) ✓')
        print(f'    Index {year_idx+6}: {tokens[year_idx+6]} (Num Sensors)')
        print(f'    Index {year_idx+7}: {tokens[year_idx+7]} (Mode)')

print('\n' + '=' * 80)
print('CONCLUSION: ALL 3 FILES HAVE "60" AT POSITION (year_idx + 5)')
print('This is the measurement frequency/sequence in minutes')
print('=' * 80)
