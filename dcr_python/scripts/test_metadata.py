"""Test FIM metadata extraction"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.fim_parser import parse_fim_file

fim_path = "C:\\DCR4402\\FIM\\C01.fim"

df, metadata = parse_fim_file(fim_path)

print("=" * 60)
print("FIM METADATA EXTRACTION TEST")
print("=" * 60)
if metadata:
    print(f"  Year: {metadata.get('year')}")
    print(f"  Month: {metadata.get('month')}")
    print(f"  Day: {metadata.get('day')}")
    print(f"  Start Hour: {metadata.get('start_hour')}")
    print(f"  Start Minute: {metadata.get('start_minute')}")
    print(f"  Interval (minutes): {metadata.get('interval_minutes')}")
else:
    print("  No metadata found")

print("\n" + "=" * 60)
print("RAW DATA")
print("=" * 60)
if df is not None:
    print(f"Data shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 10 rows:")
    print(df.head(10))
    print(f"\nData statistics:")
    print(df.describe())
else:
    print("ERROR: Failed to parse FIM file")
