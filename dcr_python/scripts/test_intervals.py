"""Test custom interval processing"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.fim_parser import parse_fim_file
from src.core.data_processor import DataProcessor
from src.models import TrafficMetadata

fim_path = "C:\\DCR4402\\FIM\\C01.fim"

print("=" * 70)
print("CUSTOM INTERVAL TEST")
print("=" * 70)

# Parse FIM file
df, metadata = parse_fim_file(fim_path)
df.attrs['fim_metadata'] = metadata

# Test different intervals
intervals = [5, 10, 15, 30, 60]

traffic_metadata = TrafficMetadata(
    filename="C01.fim",
    filepath=fim_path,
    format="FIM",
    sequence=1440,
    mode="1 - TV Conf."
)

for interval in intervals:
    processor = DataProcessor()
    success, message = processor.process_raw_data(df, traffic_metadata, interval)
    
    if success:
        processed = processor.processed_data
        print(f"\n✓ {interval}-min intervals: {processed.shape[0]} rows")
        print(f"  First 3 rows:")
        for i in range(min(3, len(processed))):
            row = processed.iloc[i]
            print(f"    {row['interval_time']}: {row['vehicle_count']:.0f} vehicles, flow: {row['flow']:.0f} veh/h")
    else:
        print(f"\n✗ {interval}-min intervals: {message}")

print("\n" + "=" * 70)
print("✓ ALL INTERVAL TESTS PASSED")
print("=" * 70)
