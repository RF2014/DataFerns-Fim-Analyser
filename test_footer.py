"""
Quick test to verify footer is added correctly
"""
import os
import sys

# Add paths
HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'dcr_python/src'))

from dcr_python.src.ui.fim_loader import MetadataPanel

# Create a panel instance
panel = MetadataPanel()

# Test data - create simple mock data
import pandas as pd
from datetime import datetime, timedelta

# Create sample data
dates = pd.date_range('2024-01-01', periods=48, freq='H')
data = {
    'timestamp': dates,
    'count': [100 + i for i in range(len(dates))],
    'vehicle_class': ['VL'] * len(dates),
    'direction': ['Sens 1'] * len(dates),
}
df = pd.DataFrame(data)

# Create metadata
meta = {
    'year': 2024,
    'month': 1,
    'day': 1,
    'start_hour': 0,
    'start_minute': 0,
    'interval_minutes': 60,
    'frequency': 60,
}

# Set current data
panel.current_df = df
panel.current_metadata = meta
panel.analysis_start_dt = dates[0].to_pydatetime()
panel.analysis_end_dt = dates[-1].to_pydatetime()

# Generate time series data
ts_data = panel._generate_timeseries_data()

print("Time series data generated successfully")
print(f"Keys: {ts_data.keys()}")

# Test footer method
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(8.27, 11.69))

# Test adding footer
panel._add_footer_with_logo(fig)
print("Footer added successfully")

# Check if logo file exists
logo_path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\Nordcomptages.jpg'
print(f"Logo exists: {os.path.exists(logo_path)}")

plt.close(fig)
print("Test completed successfully!")
