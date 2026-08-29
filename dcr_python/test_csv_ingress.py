"""
Unit tests for CsvIngressService.
Verifies parsing of CSV files with and without comment headers.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.csv_ingress_service import CsvIngressService

def create_sample_df() -> pd.DataFrame:
    """Create a sample DataFrame matching the FIM data schema"""
    dates = pd.date_range(start="2026-06-01 00:00:00", periods=24, freq="h")
    
    rows = []
    # 2 sensors, alternating VL/PL
    for sensor in [1, 2]:
        direction = "Sens 1" if sensor == 1 else "Sens 2"
        v_class = "VL" if sensor == 1 else "PL"
        for ts in dates:
            bin_data = {f"Bin{i+1}": 5 + i for i in range(12)}
            row = {
                "sensor_id": sensor,
                "direction": direction,
                "vehicle_class": v_class,
                "timestamp": ts,
                "count": sum(bin_data.values()),
                **bin_data
            }
            rows.append(row)
            
    return pd.DataFrame(rows)

def test_csv_ingress_with_comments():
    print("\n--- Test Case 1: Ingress with metadata comment headers ---")
    df_orig = create_sample_df()
    meta_orig = {
        "num_sensors": 2,
        "gps_coordinates": "48.2360, 2.0244",
        "mode": 4
    }
    
    test_filepath = "test_data_with_comments.csv"
    
    try:
        # Export
        success = CsvIngressService.export_raw_to_csv(df_orig, meta_orig, test_filepath)
        assert success, "Export to CSV failed"
        
        # Verify file exists and has comment lines
        with open(test_filepath, 'r') as f:
            lines = [f.readline() for _ in range(5)]
            assert lines[0].startswith("#"), "Comment header line 1 missing"
            assert "gps_coordinates: 48.2360, 2.0244" in lines[2], "GPS metadata missing in comments"
            
        # Parse back
        df_loaded, meta_loaded = CsvIngressService.parse_csv_file(test_filepath)
        
        assert df_loaded is not None, "Parsed df is None"
        assert meta_loaded is not None, "Parsed metadata is None"
        
        # Assert metadata
        assert meta_loaded.get("num_sensors") == 2
        assert meta_loaded.get("gps_coordinates") == "48.2360, 2.0244"
        assert meta_loaded.get("mode") == 4
        
        # Assert columns and data shape
        assert df_loaded.shape == df_orig.shape, "Shape mismatch"
        assert pd.api.types.is_datetime64_any_dtype(df_loaded['timestamp']), "Timestamp is not datetime64"
        assert list(df_loaded.columns) == list(df_orig.columns), "Columns list mismatch"
        
        print("OK: CSV ingress with comments works successfully.")
        
    finally:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)

def test_csv_ingress_without_comments():
    print("\n--- Test Case 2: Ingress with comments stripped (Fallback dynamic reconstruction) ---")
    df_orig = create_sample_df()
    
    # Rename columns to mixed/capital case to simulate Excel modifications
    df_mixed = df_orig.rename(columns={
        'sensor_id': 'Sensor_ID',
        'direction': 'Direction',
        'vehicle_class': 'Vehicle_Class',
        'timestamp': 'Timestamp',
        'count': 'Count',
        'Bin1': 'bin1',
        'Bin2': 'BIN2',
        'Bin12': 'bin_12'  # standardizing handles bin12 -> Bin12 but bin_12 won't match, let's keep standard bin name formats but with mixed case
    })
    # Let's rename Bin12 to bIn12 to test case-insensitivity
    df_mixed = df_orig.rename(columns={
        'sensor_id': 'Sensor_Id',
        'direction': 'DIRection',
        'vehicle_class': 'vehicle_CLASS',
        'timestamp': 'TimeSTAMP',
        'count': 'cOuNt',
        'Bin1': 'bin1',
        'Bin2': 'BIN2',
        'Bin3': 'Bin3',
        'Bin4': 'bIn4',
        'Bin12': 'BiN12'
    })
    
    test_filepath = "test_data_no_comments.csv"
    
    try:
        # Export standard CSV (no comments) using pandas directly to simulate Excel strip
        df_mixed.to_csv(test_filepath, index=False)
        
        # Parse back using our ingress service (should dynamically reconstruct metadata and standardize headers)
        df_loaded, meta_loaded = CsvIngressService.parse_csv_file(test_filepath)
        
        assert df_loaded is not None, "Parsed df is None"
        assert meta_loaded is not None, "Parsed metadata is None"
        
        # Verify fallback reconstruction
        assert meta_loaded.get("num_sensors") == 2, f"Reconstructed num_sensors is {meta_loaded.get('num_sensors')}, expected 2"
        assert meta_loaded.get("mode") == 4, "Reconstructed mode should default to 4"
        assert meta_loaded.get("interval_minutes") == 60, f"Reconstructed interval_minutes is {meta_loaded.get('interval_minutes')}, expected 60"
        assert "sensor_map" in meta_loaded, "sensor_map not reconstructed"
        assert meta_loaded["sensor_map"][0]["direction"] == "Sens 1"
        assert meta_loaded["sensor_map"][1]["direction"] == "Sens 2"
        
        # Check raw_data array reconstruction
        assert len(meta_loaded["raw_data"]) == len(df_orig), "raw_data array length mismatch"
        assert len(meta_loaded["raw_data"][0]) == 12, "raw_data row bins count mismatch"
        
        # Verify type standard
        assert pd.api.types.is_datetime64_any_dtype(df_loaded['timestamp']), "Timestamp is not datetime64"
        
        print("OK: CSV ingress fallback metadata reconstruction and header standardisation works successfully.")
        
    finally:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)

if __name__ == "__main__":
    test_csv_ingress_with_comments()
    test_csv_ingress_without_comments()
    print("\nALL INGRESS TESTS COMPLETED")
