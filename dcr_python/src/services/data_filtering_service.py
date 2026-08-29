"""
Service for filtering traffic data by datetime range.
Ensures unified type conversions to prevent TypeError.
"""
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Any

class DataFilteringService:
    """Provides utility methods for filtering traffic datasets"""

    @staticmethod
    def parse_timestamp_robustly(val: Any) -> Any:
        """
        Converts a value to a pandas Timestamp (datetime64[ns] compatible).
        Handles ISO (YYYY-MM-DD), French (DD/MM/YYYY) formats, Python datetime/date,
        and PyQt5 QDateTime/QDate dynamically.
        """
        if pd.isnull(val):
            return pd.NaT
            
        # Handle PyQt5 datetime objects if passed directly
        try:
            from PyQt5.QtCore import QDateTime, QDate
            if isinstance(val, QDateTime):
                val = val.toPyDateTime()
            elif isinstance(val, QDate):
                val = val.toPyDate()
        except ImportError:
            pass
            
        # Handle Python date/datetime
        from datetime import datetime, date
        if isinstance(val, datetime):
            return pd.Timestamp(val)
        if isinstance(val, date):
            return pd.Timestamp(datetime.combine(val, datetime.min.time()))
            
        if isinstance(val, pd.Timestamp):
            return val
            
        val_str = str(val).strip()
        try:
            # If it looks like ISO (starts with 4-digit year like YYYY-MM-DD or YYYY/MM/DD)
            if re.match(r'^\d{4}[-\/]', val_str):
                return pd.to_datetime(val_str, errors='coerce')
            else:
                # French format (DD/MM/YYYY)
                return pd.to_datetime(val_str, dayfirst=True, errors='coerce')
        except Exception:
            return pd.to_datetime(val_str, errors='coerce')

    @staticmethod
    def filter_by_date_range(df: pd.DataFrame, start_dt: Optional[Any] = None, end_dt: Optional[Any] = None) -> pd.DataFrame:
        """
        Filter a traffic DataFrame by start and end timestamps.
        Converts the dataframe's timestamp column and the inputs to a unified datetime64[ns]
        format (using pd.to_datetime and pd.Timestamp) to ensure safe comparisons.
        
        Args:
            df: Traffic DataFrame (having a 'timestamp' column)
            start_dt: Optional start boundary (string, datetime, or QDateTime)
            end_dt: Optional end boundary (string, datetime, or QDateTime)
            
        Returns:
            A copy of the filtered DataFrame.
        """
        if df is None or df.empty:
            return df
            
        df_filtered = df.copy()
        
        # 1. Standardize DataFrame timestamp column explicitly to datetime64[ns]
        if 'timestamp' in df_filtered.columns:
            df_filtered['timestamp'] = pd.to_datetime(
                df_filtered['timestamp'].apply(DataFilteringService.parse_timestamp_robustly),
                errors='coerce'
            )
        else:
            return df_filtered # Return copy unchanged if timestamp column missing
            
        # 2. Standardize boundary inputs to datetime64[ns] and filter
        if start_dt is not None:
            start_ns = DataFilteringService.parse_timestamp_robustly(start_dt)
            if not pd.isnull(start_ns):
                start_ns = pd.Timestamp(start_ns)
                df_filtered = df_filtered[df_filtered['timestamp'] >= start_ns]
                
        if end_dt is not None:
            end_ns = DataFilteringService.parse_timestamp_robustly(end_dt)
            if not pd.isnull(end_ns):
                end_ns = pd.Timestamp(end_ns)
                df_filtered = df_filtered[df_filtered['timestamp'] <= end_ns]
                
        return df_filtered.reset_index(drop=True)
