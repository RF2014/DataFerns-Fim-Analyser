"""
Unit tests for DataFilteringService.
Verifies unified type conversions to datetime64[ns] and boundary comparison comparisons.
"""
import os
import sys
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.data_filtering_service import DataFilteringService

def test_datetime_standardization():
    print("\n--- Test Case 1: Datetime boundary input type conversions ---")
    
    # Create DataFrame with timestamps as strings
    df_raw = pd.DataFrame({
        'timestamp': [
            '2026-06-01 08:00:00',
            '2026-06-02 09:00:00',
            '2026-06-03 10:00:00',
            '04/06/2026 11:00:00'  # French date string format
        ],
        'count': [10, 20, 30, 40]
    })
    
    # Check string boundaries
    start_str = "2026-06-02 00:00:00"
    end_str = "03/06/2026 23:59:59" # French format
    
    # Filter
    df_filtered = DataFilteringService.filter_by_date_range(df_raw, start_str, end_str)
    
    assert df_filtered is not None
    assert len(df_filtered) == 2, f"Expected 2 rows, got {len(df_filtered)}"
    assert df_filtered.loc[0, 'count'] == 20
    assert df_filtered.loc[1, 'count'] == 30
    
    # Verify timestamp column is standardized to datetime64[ns]
    assert pd.api.types.is_datetime64_any_dtype(df_filtered['timestamp'])
    
    # Check python datetime boundaries
    start_dt = datetime(2026, 6, 2, 9, 0)
    end_dt = datetime(2026, 6, 4, 12, 0)
    
    print("\nOriginal DataFrame:")
    print(df_raw)
    
    df_parsed = df_raw.copy()
    df_parsed['timestamp'] = pd.to_datetime(df_parsed['timestamp'], dayfirst=True, errors='coerce')
    print("\nParsed DataFrame:")
    print(df_parsed)
    
    print(f"\nFiltering with bounds: {start_dt} to {end_dt}")
    df_filtered_dt = DataFilteringService.filter_by_date_range(df_raw, start_dt, end_dt)
    print("\nFiltered DataFrame:")
    print(df_filtered_dt)
    
    assert len(df_filtered_dt) == 3, f"Expected 3 rows, got {len(df_filtered_dt)}"
    assert df_filtered_dt.loc[0, 'count'] == 20
    assert df_filtered_dt.loc[2, 'count'] == 40
    
    print("OK: Datetime conversion and filtering operations completed without type errors.")

if __name__ == "__main__":
    test_datetime_standardization()
    print("\nALL FILTERING TESTS COMPLETED")
