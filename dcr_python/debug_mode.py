"""
Analyze FIM header structure to identify mode field
"""
import re

# FIME0003 header
header1 = "0015.  64.0004.  00.   1.  25.  10.  06.  15.  00.0060.   1.  02.000 .0034.  4"
# FIME0004 header  
header2 = "2698.  64.0004.  00.   1.  25.  03.  04.  15.  00.0060.   1.  02.000 .0043.  4"

print("Header token analysis:")
print("\nFIME0003:")
tokens1 = [int(t) for t in re.findall(r"\d+", header1) if t]
print(f"Tokens: {tokens1}")
print(f"Length: {len(tokens1)}")

print("\nFIME0004:")
tokens2 = [int(t) for t in re.findall(r"\d+", header2) if t]
print(f"Tokens: {tokens2}")
print(f"Length: {len(tokens2)}")

print("\n\nKnown field positions:")
print("Index 5-10: [year=25, month=10/03, day=06/04, hour=15, minute=0, interval=60]")
print("Index 11: Always 1")
print("Index 12: 2 (Mode?)")
print("Index 13: 0")
print("Index 14: 34/43 (varies)")
print("Index 15: 4 (num_sensors)")

print("\n\nIf index 12 is mode:")
print(f"FIME0003 Mode: {tokens1[12]} -> Mode 3 - TV/PL ✓")
print(f"FIME0004 Mode: {tokens2[12]} -> Mode 3 - TV/PL ✓")

# But you said they're on Mode 3, and the value is 2... 
# So maybe mode = value + 1?
print("\n\nAlternative: mode = header_value + 1")
print(f"FIME0003: header[12]={tokens1[12]} -> Mode {tokens1[12]+1}")
print(f"FIME0004: header[12]={tokens2[12]} -> Mode {tokens2[12]+1}")
