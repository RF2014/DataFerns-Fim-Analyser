"""
Flexible FIM parser - works with any .fim file format.

Universal FIM file format:
- Line 0: Metadata header (date, time, num_sensors)
- Line 1: Speed bin labels (typically 12 speed classes: 30, 40, 50, ..., 150 km/h)
- Lines 2+: Data rows (N blocks of ~288 rows each, one block per sensor/direction)

Key design principles:
1. Auto-detect structure - number of sensors, rows per block
2. Simple VL/PL split - default: columns 0-1 = VL, 2-11 = PL
3. Flexible mapping - allow user override for sensor names and column split
4. Works with any FIM file - not tied to specific format variants
"""
from typing import Optional, Tuple, List, Dict
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def _is_placeholder_bin_row(row_vals: List[int]) -> bool:
    """Check if row contains placeholder bin values (30,40,50,60,70,80,90,100,110,120,130,150)"""
    if len(row_vals) < 12:
        return False
    placeholder_values = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150]
    try:
        for i in range(12):
            if row_vals[i] != placeholder_values[i]:
                return False
        return True
    except (ValueError, TypeError, IndexError):
        return False


def _is_artificial_data_pattern(bin_counts: List[int]) -> bool:
    """
    Detect artificial/test data patterns in speed bin counts.
    
    Identifies suspicious patterns like:
    - Linear progression (e.g., 20, 30, 40, 50, 60... indicating test data)
    - Arithmetic sequence with constant differences
    
    Args:
        bin_counts: List of 12 speed bin counts
    
    Returns:
        True if pattern is suspicious (likely artificial test data)
    """
    if len(bin_counts) < 12:
        return False
    
    try:
        counts = np.array(bin_counts[:12], dtype=float)
        
        # Method 1: Check for linear progression via R² value
        # Real traffic data is random; R² > 0.85 indicates artificial line
        x = np.arange(len(counts))
        
        # Fit polynomial degree 1 (linear)
        coeffs = np.polyfit(x, counts, 1)
        poly = np.poly1d(coeffs)
        y_pred = poly(x)
        
        # Calculate R² (coefficient of determination)
        ss_res = np.sum((counts - y_pred) ** 2)
        ss_tot = np.sum((counts - np.mean(counts)) ** 2)
        
        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
            if r_squared > 0.85:  # Highly suspicious linear pattern
                return True
        
        # Method 2: Check for arithmetic sequence (constant differences)
        # Calculate differences between consecutive values
        differences = np.diff(counts[:11])  # First 11 differences
        
        # Coefficient of variation of differences
        if len(differences) > 0 and np.mean(differences) != 0:
            cv = np.std(differences) / np.mean(np.abs(differences))
            if cv < 0.2:  # Very consistent differences = suspicious
                return True
        
        return False
        
    except (ValueError, TypeError, IndexError, ZeroDivisionError):
        return False


def parse_fim_file(path: str, vl_pl_mapping: Optional[Dict] = None, interval_minutes: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[dict]]:
    """
    Parse any FIM file with flexible auto-detection.
    
    Args:
        path: Path to .fim file
        vl_pl_mapping: Optional override
            {'columns': [0, 1]} -> cols 0-1 are VL, 2-11 are PL
            {'sensor_map': {0: 'Sens 1', 2: 'Sens 2'}} -> custom sensor names
        interval_minutes: User-provided measurement interval in minutes (overrides header).
            If None, automatically uses value from FIM header (typically 60 minutes).
    
    Returns:
        (DataFrame with sensor_id, direction, vehicle_class, timestamp, count)
        (metadata dict with parsing details)
        (metadata dict with parsing details)
    """
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return None, None

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        if len(lines) < 3:
            return None, None

        # Parse header and speed bins
        metadata = _parse_header(lines[0])
        speed_bins = _parse_speed_bins(lines[1])
        metadata['speed_bins'] = speed_bins
        
        # Calculate speed bin centers for mean speed calculations
        speed_bin_centers = _calculate_speed_bin_centers(speed_bins)
        metadata['speed_bin_centers'] = speed_bin_centers
        
        # Extract all data rows (must have exactly 12 columns)
        all_data = []
        filtered_count = 0
        for line in lines[2:]:
            values = [int(t) for t in re.findall(r"\d+", line) if t]
            if len(values) == 12:
                # Skip placeholder rows (bin values: 30,40,50,60,70,80,90,100,110,120,130,150)
                if _is_placeholder_bin_row(values):
                    continue
                # Skip artificial data patterns (test data with linear progression)
                if _is_artificial_data_pattern(values):
                    filtered_count += 1
                    continue
                all_data.append(values)

        if not all_data:
            return None, metadata

        # Auto-detect block structure
        num_sensors = metadata.get('num_sensors', 4)
        
        # Fallback: if header says 1 sensor but we have ~100-200 rows, likely bi-directional
        # Split evenly into 2 sensors (Sens 1, Sens 2)
        if num_sensors == 1 and 50 <= len(all_data) <= 300:
            num_sensors = 2
            metadata['num_sensors'] = 2  # Override for downstream use
        
        # Override: if header says 2 sensors but row count suggests 4 sensors
        # Many MIX files have num_sensors=2 in header but actually contain 4 sensors
        # (e.g., MIX04: 975 rows = 4×243, MIX59: 679 rows = 4×169)
        # Heuristic: if total rows > 300, assume 4 sensors (VL/PL split per direction)
        # Files with genuinely 2 sensors are typically smaller (FIME: ~115 rows, MIX02: ~340 rows)
        if num_sensors == 2 and len(all_data) > 500:
            # Override to 4 sensors for large files
            num_sensors = 4
            metadata['num_sensors'] = 4  # Override for downstream use
        
        rows_per_block = len(all_data) // num_sensors if num_sensors > 0 else len(all_data)
        
        # Sensor-level vehicle class mapping (each sensor = complete vehicle class)
        # All 12 columns per sensor represent ONE vehicle class
        vl_cols = list(range(12))  # All columns
        pl_cols = list(range(12))  # All columns
        
        # Get sensor-to-direction+class mapping
        sensor_map = vl_pl_mapping.get('sensor_map', {}) if vl_pl_mapping else {}
        if not sensor_map:
            # Default mapping based on detected sensor count
            if num_sensors == 2:
                # 2-sensor: each sensor is all vehicles for a direction
                sensor_map = {
                    0: {'direction': 'Sens 1', 'class': 'ALL'},
                    1: {'direction': 'Sens 2', 'class': 'ALL'}
                }
            else:
                # 4-sensor: sensors alternate VL/PL for each direction
                sensor_map = {
                    0: {'direction': 'Sens 1', 'class': 'VL'},
                    1: {'direction': 'Sens 1', 'class': 'PL'},
                    2: {'direction': 'Sens 2', 'class': 'VL'},
                    3: {'direction': 'Sens 2', 'class': 'PL'}
                }
        
        # Build DataFrame
        df = _build_dataframe(
            all_data, rows_per_block, num_sensors, metadata,
            sensor_map, interval_minutes
        )
        
        # Add parsing metadata
        metadata['vl_columns'] = vl_cols
        metadata['pl_columns'] = pl_cols
        metadata['rows_per_block'] = rows_per_block
        metadata['num_data_rows'] = len(all_data)
        metadata['filtered_artificial_rows'] = filtered_count
        metadata['raw_data'] = all_data  # retain raw rows for speed/avg calculations
        metadata['sensor_map'] = sensor_map  # map sensor_id -> direction+class
        
        # Capture Start and End Datetimes for UI
        if df is not None and not df.empty:
            metadata['start_datetime'] = df['timestamp'].min().strftime('%d/%m/%Y %H:%M')
            metadata['end_datetime'] = df['timestamp'].max().strftime('%d/%m/%Y %H:%M')
        
        # Extract GPS coordinates
        gps = _extract_gps_coordinates(lines[0])
        metadata['gps_coordinates'] = gps
        
        return df, metadata

    except Exception as e:
        print(f"Error parsing FIM: {e}")
        return None, None


def _extract_gps_coordinates(header_line: str) -> Optional[str]:
    """
    Search for GPS coordinates in the FIM header line.
    Looks for:
    - GPS: lat, long
    - Coordonnées: lat, long
    - Raw decimal coordinates like 48.8566, 2.3522
    - Special encoded formats like .2360.0244 in MIX files
    """
    if not isinstance(header_line, str):
        return None
        
    try:
        # 1. Look for explicit keys
        gps_match = re.search(r'(?:gps|lat|long|coordonn[eé]es)\s*:?\s*(-?\d+\.\d+)\s*[,;\s]\s*(-?\d+\.\d+)', header_line, re.IGNORECASE)
        if gps_match:
            return f"{gps_match.group(1)}, {gps_match.group(2)}"
            
        # 2. Look for two floats close to each other (e.g. 48.2360, 2.0244)
        # typical France coordinates: lat around 41-51, long around -5 to 10
        raw_coords = re.findall(r'-?\d+\.\d+', header_line)
        for i in range(len(raw_coords) - 1):
            try:
                lat = float(raw_coords[i])
                lon = float(raw_coords[i+1])
                if 41.0 <= lat <= 51.0 and -5.0 <= lon <= 10.0:
                    return f"{lat:.4f}, {lon:.4f}"
            except ValueError:
                continue
                
        # 3. Special case: MIX header format with suffix dot-numbers like .2360.0244.
        # We reconstruct: 48.2360, 2.0244 (standard for NCR/Outarville site)
        mix_match = re.search(r'\.(\d{4})\.(\d{4})\.', header_line)
        if mix_match:
            lat_frac = mix_match.group(1)
            lon_frac = mix_match.group(2)
            # Reconstruct standard France prefix (48.xxxx and 2.xxxx or similar)
            return f"48.{lat_frac}, 2.{lon_frac}"
    except Exception as e:
        print(f"Error parsing GPS coordinates from header: {e}")

    return None


def _parse_header(header_line: str) -> dict:
    """Extract date, time, and sensor count from header.
    
    Handles two header formats:
    1. YYYY.MM.DD.HH.MM.INTERVAL.NUM_SENSORS (e.g., C01.fim)
    2. ...YY.MM.DD.HH.MM.INTERVAL...NUM_SENSORS (e.g., FIME0003.FIM)
    """
    tokens = re.findall(r"\d+", header_line)
    values = [int(t) for t in tokens]
    
    metadata = {
        'year': None, 'month': None, 'day': None,
        'start_hour': None, 'start_minute': None,
        'interval_minutes': None, 'num_sensors': 4,
        'mode': None
    }
    
    try:
        # Try to find year as 4-digit value (1900-2100) first
        year_idx = None
        for i in range(len(values) - 6):
            if 1900 <= values[i] <= 2100:
                year_idx = i
                break
        
        # If no 4-digit year found, look for 2-digit year pattern
        # Pattern: YY (0-99), MM (1-12), DD (1-31), HH (0-23), MM (0-59), INTERVAL (15/30/60/1440)
        # Collect all matching patterns and choose the best one
        if year_idx is None:
            candidates = []
            for i in range(len(values) - 6):
                try:
                    # Strict pattern check for 2-digit year format
                    if (0 <= values[i] <= 99 and 
                        1 <= values[i+1] <= 12 and 
                        1 <= values[i+2] <= 31 and 
                        0 <= values[i+3] <= 23 and 
                        0 <= values[i+4] <= 59 and
                        values[i+5] in [15, 30, 60, 1440]):
                        # Score: prefer non-zero years and standard intervals (60 > 15)
                        score = 0
                        if values[i] > 0:  # Non-zero year
                            score += 100
                        if values[i] >= 20:  # Reasonable 2-digit year (2020+)
                            score += 50
                        if values[i+5] == 60:  # Common interval
                            score += 30
                        elif values[i+5] == 15:
                            score += 20
                        candidates.append((score, i))
                except IndexError:
                    continue
            
            # Choose best candidate
            if candidates:
                candidates.sort(reverse=True)  # Sort by score descending
                year_idx = candidates[0][1]
        
        if year_idx is not None:
            year_val = values[year_idx]
            # Convert 2-digit year to 4-digit (assume 20xx for values 0-99)
            if year_val < 1000:
                year_val = 2000 + year_val
            
            metadata['year'] = year_val
            metadata['month'] = values[year_idx + 1]
            metadata['day'] = values[year_idx + 2]
            metadata['start_hour'] = values[year_idx + 3]
            metadata['start_minute'] = values[year_idx + 4]
            metadata['interval_minutes'] = values[year_idx + 5]
            
            # Extract num_sensors (at year_idx + 6)
            if year_idx + 6 < len(values):
                metadata['num_sensors'] = values[year_idx + 6]
            
            # Extract mode - try multiple positions
            # Mode value in header may be mode-1 (add 1) or already the mode (no +1)
            # We need to infer which format is being used
            mode_val = None
            
            # Try position year_idx + 7 first (standard format like C01)
            if year_idx + 7 < len(values) and 1 <= values[year_idx + 7] <= 4:
                mode_val = values[year_idx + 7]
            
            # If not found, search for a value in 1-4 range after the sensor count
            # This handles MIX02-like format where mode is elsewhere
            if mode_val is None:
                for i in range(year_idx + 7, min(year_idx + 15, len(values))):
                    if 1 <= values[i] <= 4:
                        mode_val = values[i]
                        break
            
            # If still not found, check end of header (sometimes last value)
            if mode_val is None and len(values) > 0:
                for i in range(max(0, len(values) - 4), len(values)):
                    if 1 <= values[i] <= 4:
                        mode_val = values[i]
                        # Use the last one found
            
            if mode_val is not None:
                # Determine if this is mode-1 format (needs +1) or already mode (no +1)
                # If mode_val is 1, it's likely mode-1 format (mode 2)
                # If mode_val is 4, it's likely already the mode (mode 4)
                if mode_val == 1:
                    metadata['mode'] = mode_val + 1  # 1 -> Mode 2
                elif mode_val in [2, 3]:
                    # Could be either format. Default to mode-1 format for now
                    metadata['mode'] = mode_val + 1  # 2->Mode 3, 3->Mode 4
                elif mode_val == 4:
                    # Most likely already the mode, don't add 1
                    metadata['mode'] = mode_val  # 4 -> Mode 4

    
    except Exception:
        pass
    
    return metadata


def _parse_speed_bins(speed_line: str) -> List[int]:
    """Extract speed bin labels (typically 12 values)."""
    tokens = re.findall(r"\d+", speed_line)
    return [int(t) for t in tokens[:12]]


def _calculate_speed_bin_centers(speed_bin_upper_bounds: List[int]) -> List[float]:
    """
    Calculate the center points of speed bins from their upper bounds.
    
    Speed bins in FIM files are represented by upper bounds, e.g., [30, 40, 50, ...]
    These represent ranges: <20, 20-30, 30-40, 40-50, ...
    
    For mean speed calculation, we use the center of each range:
    - Bin 0 (<20): center = 10
    - Bin 1 (20-30): center = 25
    - Bin 2 (30-40): center = 35
    - Bin 3 (40-50): center = 45
    - etc.
    
    Args:
        speed_bin_upper_bounds: List of upper bounds, e.g., [30, 40, 50, ...]
    
    Returns:
        List of center points for each bin
    """
    if not speed_bin_upper_bounds or len(speed_bin_upper_bounds) == 0:
        return []
    
    centers = [10]  # First bin <20, center = 10
    
    # For remaining bins, calculate midpoint between consecutive upper bounds
    for i in range(len(speed_bin_upper_bounds) - 1):
        center = (speed_bin_upper_bounds[i] + speed_bin_upper_bounds[i + 1]) / 2.0
        centers.append(center)
    
    return centers


def _build_dataframe(
    all_data: List[List[int]],
    rows_per_block: int,
    num_sensors: int,
    metadata: dict,
    sensor_map: Dict,
    interval_minutes: Optional[int] = None
) -> pd.DataFrame:
    """Build structured DataFrame from raw data with sensor-level vehicle class mapping."""
    
    rows = []
    
    for sensor_id in range(num_sensors):
        start_row = sensor_id * rows_per_block
        end_row = min(start_row + rows_per_block, len(all_data))
        
        if start_row >= len(all_data):
            break
        
        block = all_data[start_row:end_row]
        
        # Get direction and vehicle class from sensor map
        sensor_info = sensor_map.get(sensor_id, {'direction': f'Sensor {sensor_id + 1}', 'class': 'ALL'})
        direction = sensor_info['direction']
        vehicle_class = sensor_info['class']
        
        # Determine base timestamp
        if metadata['year']:
            base_time = datetime(
                metadata['year'], metadata['month'], metadata['day'],
                metadata['start_hour'], metadata['start_minute']
            )
        else:
            base_time = datetime.now()
        
        # Determine interval: user-provided > header value > default to 5
        interval = interval_minutes if interval_minutes is not None else metadata.get('interval_minutes', 5)
        
        # Process each row - entire sensor is one vehicle class (all 12 columns)
        for row_idx, row_vals in enumerate(block):
            timestamp = base_time + timedelta(minutes=interval * row_idx)
            total_count = sum(row_vals[i] for i in range(min(12, len(row_vals))))
            bin_dict = {f'Bin{i+1}': row_vals[i] if i < len(row_vals) else 0 for i in range(12)}
            if vehicle_class == 'ALL':
                rows.append({
                    'sensor_id': sensor_id + 1,
                    'direction': direction,
                    'vehicle_class': 'VL',
                    'timestamp': timestamp,
                    'count': total_count,
                    **bin_dict
                })
                rows.append({
                    'sensor_id': sensor_id + 1,
                    'direction': direction,
                    'vehicle_class': 'PL',
                    'timestamp': timestamp,
                    'count': 0,  # No PL data for 2-sensor files
                    **{f'Bin{i+1}': 0 for i in range(12)}
                })
            else:
                rows.append({
                    'sensor_id': sensor_id + 1,
                    'direction': direction,
                    'vehicle_class': vehicle_class,
                    'timestamp': timestamp,
                    'count': total_count,
                    **bin_dict
                })
    
    if not rows:
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df
