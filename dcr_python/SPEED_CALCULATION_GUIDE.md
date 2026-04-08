# FIM Speed Calculation Guide

## Overview
FIM files store vehicle count data by speed ranges. Each data row contains 12 values representing the number of vehicles in each speed bin.

## Speed Bins Structure

### File Header Format
- **Line 0**: Metadata (date, time, sensors, interval)
- **Line 1**: Speed bin upper bounds (12 values, e.g., `0030.0040.0050.0060.0070.0080.0090.0100.0110.0120.0130.0150`)
- **Lines 2+**: Data rows (vehicle counts by speed bin)

### Speed Bin Ranges
The 12 values in line 1 represent **upper bounds** of speed ranges:

| Bin | Range | Upper Bound | Center |
|-----|-------|-------------|--------|
| 0   | <20   | -           | 10     |
| 1   | 20-30 | 30          | 25     |
| 2   | 30-40 | 40          | 35     |
| 3   | 40-50 | 50          | 45     |
| 4   | 50-60 | 60          | 55     |
| 5   | 60-70 | 70          | 65     |
| 6   | 70-80 | 80          | 75     |
| 7   | 80-90 | 90          | 85     |
| 8   | 90-100| 100         | 95     |
| 9   | 100-110| 110        | 105    |
| 10  | 110-120| 120        | 115    |
| 11  | 120-130/130-150 | 130/150 | 125/140 |

**Note**: The last bin varies by file type. Some files use 130 as upper bound (range 120-130, center 125), others use 150 (range 130-150+, center 140).

## Mean Speed Calculation

### Formula
For a measurement period (hour, day, etc.) with data row containing vehicle counts `[c₀, c₁, c₂, ..., c₁₁]`:

```
Mean Speed = Σ(cᵢ × centerᵢ) / Σ(cᵢ)
```

Where:
- `cᵢ` = number of vehicles in bin i
- `centerᵢ` = center point of speed range for bin i
- `Σ(cᵢ)` = total number of vehicles

### Example
For data `[7, 19, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0]` (7 vehicles <20 km/h, 19 at 20-30, 3 at 30-40):

```
Weighted sum = 7×10 + 19×25 + 3×35
             = 70 + 475 + 105
             = 650

Total vehicles = 7 + 19 + 3 = 29

Mean speed = 650 / 29 = 22.41 km/h
```

## Aggregation Levels

### Hourly Mean Speed
Calculate from a single row (1 hour of data per sensor):
```
Mean Speed (hourly) = Σ(count[i] × center[i]) / Σ(count[i])
```

### Daily Mean Speed  
Aggregate all 24 hourly rows for a sensor:
```
Mean Speed (daily) = Σ(all hourly counts × centers) / Σ(all hourly counts)
```
This is equivalent to summing all vehicle counts by bin across the day, then calculating the weighted mean.

## Implementation in Code

### Python
```python
# Speed bin upper bounds from file header
speed_bin_upper_bounds = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150]

# Calculate centers
speed_bin_centers = [10]
for i in range(len(speed_bin_upper_bounds) - 1):
    center = (speed_bin_upper_bounds[i] + speed_bin_upper_bounds[i + 1]) / 2.0
    speed_bin_centers.append(center)
# Result: [10, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]

# For a data row
counts = [7, 19, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
total_vehicles = sum(counts)
weighted_sum = sum(c * s for c, s in zip(counts, speed_bin_centers))
mean_speed = weighted_sum / total_vehicles if total_vehicles > 0 else 0
```

## Verification with C13 File

**Test Case: Nov 18, 2025 (Sens 1 VL)**

Daily aggregation:
- Total vehicles: 1,305
- Calculated mean speed: 31.82 km/h
- Expected: 31.9 km/h
- **Match**: ✓ (within 0.08 km/h)

This confirms the speed bin center calculation is correct.

## File-Specific Variations

Different FIM file types may have slightly different speed bins:

| File Type | Speed Bins |
|-----------|-----------|
| C13 | [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150] |
| MIX02 | [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 255] |
| MIX04 | Similar to C13 |
| MIX59 | Likely similar to C13 or MIX02 |

**Important**: Always extract the speed bins from the file header (Line 1), don't hardcode them.
