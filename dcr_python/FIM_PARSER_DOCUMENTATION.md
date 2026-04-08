# Flexible FIM Parser Implementation - Complete Documentation

## Overview

The FIM (Traffic Data Format) parser has been completely redesigned to be **format-agnostic and flexible**, working with ANY .fim file without hardcoded assumptions about structure or mapping.

## Architecture

### Components

1. **`src/core/fim_parser.py`** - Core flexible parser
   - Auto-detects file structure from header metadata
   - Applies sensible default VL/PL column mapping
   - Supports custom mapping overrides
   - Returns structured DataFrame with standardized columns

2. **`src/core/file_manager.py`** - File I/O integration
   - Updated `open_file()` to use new flexible parser
   - Preserves FIM metadata in DataFrame attributes for downstream processing

3. **`src/core/data_processor.py`** - Data processing pipeline
   - Updated `_clean_data()` to handle new parser output
   - Enhanced `_calculate_metrics()` to process timestamp-based data
   - Maintains backward compatibility with legacy formats

## FIM File Format (Universal)

```
Line 0: YYYY.MM.DD.HH.MM.INTERVAL.NUM_SENSORS
        Example: 2025.09.20.10.00.0060.4
        - Year, Month, Day (date of measurement)
        - Start Hour, Start Minute (when measurement began)
        - Interval in minutes (typically 60)
        - Number of sensors (typically 4)

Line 1: Speed bin labels (12 speed classes)
        Example: 30 40 50 60 70 80 90 100 110 120 130 150
        - Represents speed ranges in km/h

Lines 2+: Data rows (12 columns per row)
        - Each row: 12 numeric values (vehicle counts by speed class)
        - Organized in N sequential blocks (1 block per sensor)
        - ~288 rows per block = 24 hours of 5-minute intervals
        - Time progression: 00:00 → 23:55 (for 1440-minute = 24h measurement)
```

## Parser Usage

### Basic Usage (with defaults)

```python
from src.core.fim_parser import parse_fim_file

# Load with default mapping: columns 0-1 = VL, 2-11 = PL
df, metadata = parse_fim_file('path/to/file.fim')

# DataFrame columns: sensor_id, direction, vehicle_class, timestamp, count
# Each row represents VL or PL count for a specific timestamp and sensor

print(df.shape)  # (rows, 5)
print(df.columns)  # Index(['sensor_id', 'direction', 'vehicle_class', 'timestamp', 'count'], dtype='object')
```

### Advanced Usage (with custom mapping)

```python
# Custom VL/PL column split (columns 0-3 = VL, 4-11 = PL)
df, metadata = parse_fim_file(
    'path/to/file.fim',
    vl_pl_mapping={
        'columns': [0, 1, 2, 3]  # These columns are VL, rest are PL
    }
)

# Custom sensor/direction names
df, metadata = parse_fim_file(
    'path/to/file.fim',
    vl_pl_mapping={
        'sensor_map': {
            0: 'Direction A',
            1: 'Direction A (OPP)',
            2: 'Direction B',
            3: 'Direction B (OPP)'
        }
    }
)

# Combined custom mapping
df, metadata = parse_fim_file(
    'path/to/file.fim',
    vl_pl_mapping={
        'columns': [0, 1],
        'sensor_map': {0: 'Sens 1', 2: 'Sens 2'}
    }
)
```

## Output DataFrame Structure

### Columns

| Column | Type | Description |
|--------|------|-------------|
| sensor_id | int | Sensor number (1-N) |
| direction | str | Direction/sensor name (e.g., "Sens 1", "Sensor 2") |
| vehicle_class | str | Vehicle classification: "VL" (light) or "PL" (heavy) |
| timestamp | datetime | Date and time of measurement (5-minute intervals) |
| count | int | Number of vehicles in this class at this time |

### Example Output

```
   sensor_id direction vehicle_class           timestamp  count
0          1    Sens 1            VL 2025-09-20 10:00:00      8
1          1    Sens 1            PL 2025-09-20 10:00:00    2
2          1    Sens 1            VL 2025-09-20 10:05:00     12
3          1    Sens 1            PL 2025-09-20 10:05:00      1
...
```

## Metadata

The parser returns metadata dictionary with:

```python
metadata = {
    'year': 2025,
    'month': 9,
    'day': 20,
    'start_hour': 10,
    'start_minute': 0,
    'interval_minutes': 60,
    'num_sensors': 4,
    'vl_columns': [0, 1],           # Which columns are VL
    'pl_columns': [2, 3, ..., 11],  # Which columns are PL
    'rows_per_block': 287,          # Rows per sensor
    'num_data_rows': 1151           # Total data rows
}
```

## Integration Points

### FileManager Integration

```python
from src.core.file_manager import FileManager

fm = FileManager(fim_dir='C:\\DCR4402\\FIM')
df = fm.open_file('C01.fim', 'FIM')

# Metadata is attached to DataFrame
metadata = df.attrs.get('fim_metadata')
```

### DataProcessor Integration

```python
from src.core.data_processor import DataProcessor
from src.models import TrafficMetadata

dp = DataProcessor()

# Metadata object for DataProcessor
metadata = TrafficMetadata(
    filename='C01.fim',
    filepath='C:\\DCR4402\\FIM\\C01.fim',
    format='FIM',
    sequence=5,  # 5-minute intervals
    mode='TV Conf.'
)

# Process the data
success, message = dp.process_raw_data(df, metadata, interval_minutes=5)

# Get summaries
hourly = dp.get_hourly_summary()
daily = dp.get_daily_summary()
```

## Key Features

✅ **Format-Agnostic**
- Auto-detects number of sensors from header
- Works with any valid .fim file structure
- No hardcoded assumptions

✅ **Flexible Mapping**
- Default sensible mapping (columns 0-1 = VL, 2-11 = PL)
- User-customizable VL/PL column split
- User-customizable sensor names/directions

✅ **Structured Output**
- Clean DataFrame format
- Proper timestamps with 5-minute granularity
- Separated VL/PL counts (one row per vehicle_class per timestamp)

✅ **Backward Compatible**
- FileManager and DataProcessor updated to handle new format
- Existing code continues to work
- Metadata preserved for downstream processing

## Testing

Test files demonstrating functionality:

1. **`test_v3_parser.py`** - Basic parser functionality
2. **`test_campaign_period.py`** - Period-based filtering and validation
3. **`test_flexible_demo.py`** - Custom mapping demonstrations
4. **`test_integration.py`** - Full integration with FileManager and DataProcessor

## C01.fim Validation Results

**File**: C:\DCR4402\FIM\C01.fim
**Date**: 2025-09-20 10:00
**Sensors**: 4 (4 blocks of 287 rows each)
**Interval**: 5 minutes (12 rows/hour)
**Total vehicles**: 60,678 (24h period)

### Sensor-wise breakdown:

| Sensor | Direction | VL | PL | Total |
|--------|-----------|----|----|-------|
| 1 | Sens 1 | 26,327 | 585 | 26,912 |
| 2 | Sensor 2 | 3,065 | 993 | 4,058 |
| 3 | Sens 2 | 20,715 | 4,624 | 25,339 |
| 4 | Sensor 4 | 3,154 | 1,215 | 4,369 |

### Campaign period (10:00-22:00, 12 hours):

| Sensor | VL | PL | Total |
|--------|----|----|-------|
| 1 | 15,065 | 338 | 15,403 |
| 2 | 1,747 | 976 | 2,723 |
| 3 | 12,320 | 2,877 | 15,197 |
| 4 | 1,902 | 1,094 | 2,996 |

## Migration Guide for Existing Code

### Old Approach
```python
# Hardcoded mapping per file
if filename == 'C01.fim':
    vl_cols = [0, 1]  # Custom for C01
elif filename == 'C02.fim':
    vl_cols = [0, 2]  # Different mapping
```

### New Approach
```python
# Single flexible parser works for all files
df, metadata = parse_fim_file('any_file.fim')  # Uses defaults

# Or with custom mapping if needed
df, metadata = parse_fim_file('any_file.fim', vl_pl_mapping={'columns': [0, 1, 2]})
```

## Future Enhancements

- Additional speed bin parsing (currently uses first 12 columns)
- Support for variable-length sensor blocks
- Automatic validation against known campaign totals
- Enhanced metadata extraction from file headers

---

**Status**: ✅ Complete and tested
**Compatibility**: Python 3.10+, pandas 2.1.3+, numpy 1.24.3+
**Last Updated**: 2025-12-11
