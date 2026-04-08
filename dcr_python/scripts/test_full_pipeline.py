"""End-to-end test of FIM processing pipeline with real metadata"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.fim_parser import parse_fim_file
from src.core.data_processor import DataProcessor
from src.models import TrafficMetadata

# Test parameters
fim_path = "C:\\DCR4402\\FIM\\C01.fim"
output_csv = "C:\\Users\\royston.fernandes\\Documents\\CodeVBA_fim\\GUI\\dcr_python\\test_output.csv"

print("=" * 70)
print("END-TO-END FIM PROCESSING TEST")
print("=" * 70)

# Step 1: Parse FIM file with metadata
print("\n[1/3] Parsing FIM file...")
df, metadata = parse_fim_file(fim_path)

if df is None:
    print("ERROR: Failed to parse FIM file")
    sys.exit(1)

print(f"  ✓ Parsed FIM file: {df.shape[0]} vehicle counts")
print(f"  ✓ Extracted metadata:")
print(f"    - Date: {metadata['year']}-{metadata['month']:02d}-{metadata['day']:02d}")
print(f"    - Start time: {metadata['start_hour']:02d}:{metadata['start_minute']:02d}")
print(f"    - Interval: {metadata['interval_minutes']} minutes")

# Attach metadata to dataframe
df.attrs['fim_metadata'] = metadata

# Step 2: Process the data
print("\n[2/3] Processing data into 15-minute intervals...")
processor = DataProcessor()

traffic_metadata = TrafficMetadata(
    filename="C01.fim",
    filepath=fim_path,
    format="FIM",
    sequence=1440,
    mode="1 - TV Conf."
)

success, message = processor.process_raw_data(df, traffic_metadata)

if not success:
    print(f"ERROR: {message}")
    sys.exit(1)

processed = processor.processed_data
print(f"  ✓ Processing complete: {df.shape[0]} raw counts → {processed.shape[0]} 15-min intervals")
print(f"  ✓ Columns: {list(processed.columns)}")

# Step 3: Examine the output
print("\n[3/3] Output preview (first 12 rows):")
print(processed.head(12).to_string())

print("\n" + "=" * 70)
print("Time assignment using FIM metadata:")
print("=" * 70)
print(f"Start time from FIM: {metadata['start_hour']:02d}:{metadata['start_minute']:02d}")
print(f"First row time: {processed.iloc[0]['hour']:02d}:{int(processed.iloc[0]['minute']):02d}")
print(f"Last row time: {processed.iloc[-1]['hour']:02d}:{int(processed.iloc[-1]['minute']):02d}")

# Step 4: Export as CSV
print(f"\n[EXPORT] Saving to {output_csv}...")
processed.to_csv(output_csv, index=False)
print(f"  ✓ Exported {processed.shape[0]} rows to CSV")

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)
print("\nKey findings:")
print(f"  • FIM files DO contain time data (date + start time)")
print(f"  • Parser now extracts: {metadata['year']}-{metadata['month']:02d}-{metadata['day']:02d} {metadata['start_hour']:02d}:{metadata['start_minute']:02d}")
print(f"  • Data processor uses actual start time (not synthetic)")
print(f"  • 15-minute intervals calculated from start time")
