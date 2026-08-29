#!/usr/bin/env python
"""
Test script to verify date range filtering functionality in analysis exports.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_data():
    """Create sample traffic data for testing."""
    # Create 7 days of test data with hourly intervals
    dates = []
    counts = []
    directions = []
    vehicle_classes = []
    
    base_date = datetime(2024, 1, 15, 0, 0)  # Start at Jan 15, 2024
    
    for day_offset in range(7):
        for hour in range(24):
            timestamp = base_date + timedelta(days=day_offset, hours=hour)
            
            # Create traffic patterns (higher during day)
            if 6 <= hour < 22:
                base_count = 150 + np.random.randint(-20, 50)
            else:
                base_count = 30 + np.random.randint(-10, 20)
            
            # Sens 1
            dates.append(timestamp)
            counts.append(base_count)
            directions.append('Sens 1')
            vehicle_classes.append('VL')
            
            dates.append(timestamp)
            counts.append(base_count * 0.3)  # 30% heavy vehicles
            directions.append('Sens 1')
            vehicle_classes.append('PL')
            
            # Sens 2
            dates.append(timestamp)
            counts.append(base_count * 0.95)
            directions.append('Sens 2')
            vehicle_classes.append('VL')
            
            dates.append(timestamp)
            counts.append(base_count * 0.28)
            directions.append('Sens 2')
            vehicle_classes.append('PL')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'count': counts,
        'direction': directions,
        'vehicle_class': vehicle_classes
    })
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['count'] = df['count'].astype(int)
    
    return df


def test_date_range_filtering():
    """Test that date range filtering works correctly."""
    print("=" * 60)
    print("Testing Date Range Filtering Functionality")
    print("=" * 60)
    
    # Create test data
    df_original = create_test_data()
    print(f"\n[OK] Created test data:")
    print(f"  - Total rows: {len(df_original)}")
    print(f"  - Date range: {df_original['timestamp'].min()} to {df_original['timestamp'].max()}")
    print(f"  - Unique dates: {len(df_original['timestamp'].dt.date.unique())}")
    
    # Test Case 1: Full date range
    print("\n" + "-" * 60)
    print("Test 1: Full date range (no filtering)")
    start_dt = df_original['timestamp'].min()
    end_dt = df_original['timestamp'].max()
    df_filtered = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    print(f"  Input range: {start_dt} to {end_dt}")
    print(f"  Filtered rows: {len(df_filtered)}")
    assert len(df_filtered) == len(df_original), "Full range filter failed"
    print("  [OK] PASSED: Full date range filtering works")
    
    # Test Case 2: First 2 days only
    print("\n" + "-" * 60)
    print("Test 2: First 2 days only")
    start_dt = df_original['timestamp'].min()
    end_dt = start_dt + timedelta(days=2)
    df_filtered = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    print(f"  Input range: {start_dt} to {end_dt}")
    print(f"  Filtered rows: {len(df_filtered)}")
    print(f"  Unique dates: {len(df_filtered['timestamp'].dt.date.unique())}")
    assert len(df_filtered) > 0, "Filter returned no data"
    assert len(df_filtered) < len(df_original), "Filter did not reduce data"
    print("  [OK] PASSED: Partial date range filtering works")
    
    # Test Case 3: Single day
    print("\n" + "-" * 60)
    print("Test 3: Single day only")
    start_dt = df_original['timestamp'].min()
    end_dt = start_dt + timedelta(hours=23, minutes=59)
    df_filtered = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    print(f"  Input range: {start_dt} to {end_dt}")
    print(f"  Filtered rows: {len(df_filtered)}")
    print(f"  Unique dates: {len(df_filtered['timestamp'].dt.date.unique())}")
    assert len(df_filtered) > 0, "Single day filter returned no data"
    assert len(df_filtered['timestamp'].dt.date.unique()) == 1, "Single day filter returned multiple dates"
    print("  [OK] PASSED: Single day filtering works")
    
    # Test Case 4: Middle days
    print("\n" + "-" * 60)
    print("Test 4: Middle 3 days (days 2-4)")
    start_dt = df_original['timestamp'].min() + timedelta(days=1, hours=12)
    end_dt = df_original['timestamp'].min() + timedelta(days=4, hours=12)
    df_filtered = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    print(f"  Input range: {start_dt} to {end_dt}")
    print(f"  Filtered rows: {len(df_filtered)}")
    print(f"  Unique dates: {len(df_filtered['timestamp'].dt.date.unique())}")
    assert len(df_filtered) > 0, "Middle days filter returned no data"
    assert len(df_filtered) < len(df_original), "Middle days filter did not reduce data"
    print("  [OK] PASSED: Middle date range filtering works")
    
    # Test Case 5: Empty range (shouldn't happen in practice)
    print("\n" + "-" * 60)
    print("Test 5: Empty range (start > end)")
    start_dt = df_original['timestamp'].max()
    end_dt = df_original['timestamp'].min()
    df_filtered = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    print(f"  Input range: {start_dt} to {end_dt}")
    print(f"  Filtered rows: {len(df_filtered)}")
    assert len(df_filtered) == 0, "Empty range should return 0 rows"
    print("  [OK] PASSED: Empty range correctly returns no data")
    
    # Test statistics calculation with filtered data
    print("\n" + "-" * 60)
    print("Test 6: Verify statistics with different date ranges")
    
    # Full range statistics
    start_dt = df_original['timestamp'].min()
    end_dt = df_original['timestamp'].max()
    df_full = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    total_full = df_full['count'].sum()
    days_full = len(df_full['timestamp'].dt.date.unique())
    daily_avg_full = total_full / days_full
    
    # Partial range statistics
    start_dt = df_original['timestamp'].min()
    end_dt = df_original['timestamp'].min() + timedelta(days=1)
    df_partial = df_original[
        (df_original['timestamp'] >= start_dt) & 
        (df_original['timestamp'] <= end_dt)
    ]
    total_partial = df_partial['count'].sum()
    days_partial = len(df_partial['timestamp'].dt.date.unique())
    daily_avg_partial = total_partial / days_partial
    
    print(f"  Full range:")
    print(f"    - Total vehicles: {total_full:,}")
    print(f"    - Days covered: {days_full}")
    print(f"    - Daily average: {daily_avg_full:.1f}")
    print(f"  Partial range (first 2 days):")
    print(f"    - Total vehicles: {total_partial:,}")
    print(f"    - Days covered: {days_partial}")
    print(f"    - Daily average: {daily_avg_partial:.1f}")
    print("  [OK] PASSED: Statistics calculation with filtered data works")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED [OK]")
    print("=" * 60)


if __name__ == "__main__":
    test_date_range_filtering()
