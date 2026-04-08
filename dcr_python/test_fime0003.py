import re
import pathlib
from datetime import datetime, timedelta

path = pathlib.Path(r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM')
lines = path.read_text().splitlines()

header = lines[0]
print("Header:", repr(header))

# Extract all numbers
tokens = [int(x) for x in re.findall(r'\d+', header)]
print("Tokens:", tokens)

# Expected: 06 oct 2025 at 15:00, Sequence: 60
# From inspection: [15, 64, 4, 0, 1, 25, 10, 6, 15, 0, 60, 1, 2, 0, 34, 4]
# Mapping:
# pos 5: 25 = 2025 (year)
# pos 6: 10 = 10 (month)
# pos 7: 6 = 6 (day)
# pos 8: 15 = 15 (hour)
# pos 9: 0 = 0 (minute)
# pos 10: 60 = 60 (interval)
# pos 15: 4 = 4 (num sensors)

year = tokens[5]
month = tokens[6]
day = tokens[7]
hour = tokens[8]
minute = tokens[9]
interval = tokens[10]
num_sensors = tokens[15]

print(f"\n=== EXTRACTED FROM FILE ===")
print(f"Start Date: {day:02d}/{month:02d}/{year}")
print(f"Start Time: {hour:02d}:{minute:02d}")
print(f"Interval: {interval} minutes")
print(f"Number of sensors: {num_sensors}")

print(f"\n=== EXPECTED ===")
print(f"Start Date: 06/10/2025")
print(f"Start Time: 15:00")
print(f"Interval: 60 minutes")
print(f"Number of sensors: 4 (or 2?)")

# Count valid data rows (lines with 12 columns)
valid_rows = 0
for line in lines[2:]:  # Skip header and speed bins
    nums = [int(t) for t in re.findall(r'\d+', line)]
    if len(nums) == 12:
        valid_rows += 1

print(f"\n=== FILE STRUCTURE ===")
print(f"Total lines: {len(lines)}")
print(f"Valid data rows (12 columns): {valid_rows}")
print(f"Rows per sensor block: {valid_rows // num_sensors if num_sensors > 0 else 'N/A'}")

# The expected period is: 06 oct 15:00 to 23 oct 13:00
# That's 17 days and 22 hours = 430 hours = 7 measurements at 60-minute intervals per hour = 7*430 = 3010 measurements
# OR: if 60 min interval = 1 measurement per hour, then 430 measurements total across 4 sensors = ~107 per sensor
start_dt = datetime(year, month, day, hour, minute)
end_dt = datetime(2025, 10, 23, 13, 0)  # Expected end
duration = (end_dt - start_dt).total_seconds() / 3600  # hours
expected_measurements = int(duration / (interval / 60))
print(f"\nExpected duration: {duration} hours")
print(f"Expected measurements per interval: {expected_measurements}")
print(f"Expected per sensor: {expected_measurements // num_sensors if num_sensors > 0 else 'N/A'}")
print(f"Actual per sensor: {valid_rows // num_sensors if num_sensors > 0 else 'N/A'}")
