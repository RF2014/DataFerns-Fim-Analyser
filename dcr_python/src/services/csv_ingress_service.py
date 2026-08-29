"""
Service for ingesting and exporting edited CSV traffic data.
Decouples data storage from origin format (FIM or CSV).
"""
import os
import re
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

class CsvIngressService:
    """Ingress layer for CSV files, mapping them to the central state schema"""

    @staticmethod
    def parse_csv_file(path: str) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
        """
        Ingest an edited CSV file and reconstruct the central state schema.
        Reads embedded metadata from comment headers, or reconstructs it dynamically if missing.
        """
        try:
            if not os.path.exists(path):
                return None, None
                
            metadata = {}
            # 1. Read comments at the top for metadata
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if line.strip().startswith('#'):
                        # parse key: value
                        match = re.match(r'^#\s*([^:]+)\s*:\s*(.*)$', line.strip())
                        if match:
                            key = match.group(1).strip()
                            val = match.group(2).strip()
                            # Convert types if possible
                            if val.isdigit():
                                metadata[key] = int(val)
                            elif val.replace('.', '', 1).isdigit() and '.' in val:
                                metadata[key] = float(val)
                            else:
                                metadata[key] = val
                    else:
                        break # End of comments
            
            # 2. Read DataFrame (pandas automatically skips lines starting with # if comment='#' is passed)
            df = pd.read_csv(path, comment='#')
            
            # Standardize column names (case-insensitive and strip whitespace)
            df.columns = [c.strip() for c in df.columns]
            col_mapping = {}
            for col in df.columns:
                lower_col = col.lower()
                if lower_col == 'sensor_id':
                    col_mapping[col] = 'sensor_id'
                elif lower_col == 'direction':
                    col_mapping[col] = 'direction'
                elif lower_col == 'vehicle_class':
                    col_mapping[col] = 'vehicle_class'
                elif lower_col == 'timestamp':
                    col_mapping[col] = 'timestamp'
                elif lower_col == 'count':
                    col_mapping[col] = 'count'
                elif lower_col.startswith('bin'):
                    try:
                        bin_num = int(re.findall(r'\d+', lower_col)[0])
                        if 1 <= bin_num <= 12:
                            col_mapping[col] = f'Bin{bin_num}'
                    except Exception:
                        pass
            df = df.rename(columns=col_mapping)
            
            # 3. Validate columns
            required_cols = ['sensor_id', 'direction', 'vehicle_class', 'timestamp', 'count']
            bin_cols = [f'Bin{i+1}' for i in range(12)]
            for col in required_cols + bin_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column in CSV: {col}")
                    
            # 4. Standardize types and parse timestamps (handling French dayfirst=True and ISO formats robustly)
            from .data_filtering_service import DataFilteringService
            df['timestamp'] = pd.to_datetime(
                df['timestamp'].apply(DataFilteringService.parse_timestamp_robustly),
                errors='coerce'
            )
            
            df['sensor_id'] = df['sensor_id'].astype(int)
            df['count'] = df['count'].astype(int)
            for b in bin_cols:
                df[b] = df[b].fillna(0).astype(int)
                
            # 5. Reconstruct / supplement metadata dynamically
            min_ts = df['timestamp'].min()
            max_ts = df['timestamp'].max()
            
            if pd.isnull(min_ts) or pd.isnull(max_ts):
                raise ValueError("CSV contains invalid or missing timestamps")
                
            metadata.setdefault('year', min_ts.year)
            metadata.setdefault('month', min_ts.month)
            metadata.setdefault('day', min_ts.day)
            metadata.setdefault('start_hour', min_ts.hour)
            metadata.setdefault('start_minute', min_ts.minute)
            
            num_sensors = int(df['sensor_id'].nunique())
            metadata.setdefault('num_sensors', num_sensors)
            bin_totals = [df[b].sum() for b in bin_cols] if all(b in df.columns for b in bin_cols) else [0]
            non_zero_bins = sum(1 for tot in bin_totals if tot > 0)
            has_velocity = non_zero_bins > 1 and sum(bin_totals) > 0
            metadata.setdefault('has_velocity', has_velocity)
            metadata.setdefault('mode', 4 if has_velocity else 3)
            
            metadata.setdefault('speed_bins', [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150])
            metadata.setdefault('speed_bin_centers', [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140])
            metadata.setdefault('vl_columns', list(range(12)))
            metadata.setdefault('pl_columns', list(range(12)))
            metadata.setdefault('gps_coordinates', None)
            
            # Reconstruct interval_minutes dynamically from consecutive timestamps of a single sensor
            interval_minutes = 60
            if num_sensors > 0:
                first_sensor = sorted(df['sensor_id'].unique())[0]
                sensor_ts = df[df['sensor_id'] == first_sensor]['timestamp'].sort_values()
                if len(sensor_ts) > 1:
                    diff = (sensor_ts.iloc[1] - sensor_ts.iloc[0]).total_seconds() / 60
                    if diff > 0:
                        interval_minutes = int(diff)
            metadata.setdefault('interval_minutes', interval_minutes)
            
            # Reconstruct sensor_map from unique values in DataFrame
            sensor_map = {}
            for s_id in sorted(df['sensor_id'].unique()):
                sub_df = df[df['sensor_id'] == s_id]
                if not sub_df.empty:
                    row = sub_df.iloc[0]
                    # sensor_map expects 0-indexed keys matching sensor_id - 1
                    sensor_map[s_id - 1] = {
                        'direction': str(row['direction']),
                        'class': str(row['vehicle_class'])
                    }
            metadata.setdefault('sensor_map', sensor_map)
            
            # Reconstruct raw_data for compatibility with downstream speed/average calculations
            raw_data = []
            for s_id in sorted(df['sensor_id'].unique()):
                sensor_df = df[df['sensor_id'] == s_id].sort_values('timestamp')
                for _, row in sensor_df.iterrows():
                    bin_vals = [int(row[b]) for b in bin_cols]
                    raw_data.append(bin_vals)
            metadata.setdefault('raw_data', raw_data)
            
            # Calculate rows_per_block based on the actual sensor blocks
            if num_sensors > 0:
                metadata.setdefault('rows_per_block', len(df) // num_sensors)
            else:
                metadata.setdefault('rows_per_block', len(df))
                
            metadata.setdefault('num_data_rows', len(df))
            metadata.setdefault('filtered_artificial_rows', 0)
            
            # Formatting start and end datetimes for UI
            metadata['start_datetime'] = min_ts.strftime('%d/%m/%Y %H:%M')
            metadata['end_datetime'] = max_ts.strftime('%d/%m/%Y %H:%M')
            
            return df, metadata
            
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return None, None

    @staticmethod
    def export_raw_to_csv(df: pd.DataFrame, metadata: Dict[str, Any], filepath: str) -> bool:
        """
        Export raw traffic data to CSV, embedding metadata as comments at the top.
        """
        try:
            gps = metadata.get('gps_coordinates', '')
            if gps is None:
                gps = ''
                
            comments = [
                "# format: CSV",
                f"# num_sensors: {metadata.get('num_sensors', 4)}",
                f"# gps_coordinates: {gps}",
                f"# mode: {metadata.get('mode', 4)}"
            ]
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write('\n'.join(comments) + '\n')
                df.to_csv(f, index=False)
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
