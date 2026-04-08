"""Analyze FIM file granularity - understand the raw data intervals"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.fim_parser import parse_fim_file

fim_path = "C:\\DCR4402\\FIM\\C01.fim"

print("=" * 70)
print("FIM FILE GRANULARITY ANALYSIS")
print("=" * 70)

# Parse the file
df, metadata = parse_fim_file(fim_path)

print("\nFIM FILE METADATA:")
print(f"  Date: {metadata['year']}-{metadata['month']:02d}-{metadata['day']:02d}")
print(f"  Start time: {metadata['start_hour']:02d}:{metadata['start_minute']:02d}")
print(f"  FIM interval setting: {metadata['interval_minutes']} minutes")

print("\nRAW DATA ANALYSIS:")
print(f"  Total vehicle count records: {len(df)}")
print(f"  Data range: {df['vehicle_count'].min()} to {df['vehicle_count'].max()} vehicles")
print(f"  Mean per record: {df['vehicle_count'].mean():.2f} vehicles")
print(f"  Median per record: {df['vehicle_count'].median():.0f} vehicles")

# Calculate what the granularity might be
total_vehicles = df['vehicle_count'].sum()
total_minutes = len(df) * metadata['interval_minutes'] if metadata['interval_minutes'] else 1
total_hours = total_minutes / 60
total_days = total_hours / 24

print(f"\nTOTAL TRAFFIC VOLUME:")
print(f"  Total vehicles recorded: {total_vehicles:.0f}")
print(f"  Duration covered: {total_minutes} minutes = {total_hours:.1f} hours = {total_days:.2f} days")

# Estimate the original interval
if len(df) > 0 and total_minutes > 0:
    estimated_interval = total_minutes / len(df)
    print(f"\nESTIMATED GRANULARITY:")
    print(f"  Records: {len(df)}")
    print(f"  Total time span: {total_minutes} minutes")
    print(f"  Calculated interval per record: {estimated_interval:.2f} minutes")

# Show sample of raw data
print(f"\nSAMPLE OF RAW DATA (first 20 records):")
print(df.head(20).to_string())

print(f"\nSAMPLE OF RAW DATA (last 20 records):")
print(df.tail(20).to_string())

print("\n" + "=" * 70)
print("INTERPRETATION:")
print("=" * 70)
print(f"The FIM file contains {len(df)} individual vehicle count measurements.")
print(f"The metadata says interval is {metadata['interval_minutes']} minutes,")
print(f"which means each record represents a {metadata['interval_minutes']}-minute period.")
print(f"Total span: ~{total_hours:.1f} hours of traffic data")
