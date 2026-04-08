"""
Data processing pipeline for traffic analysis
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from datetime import datetime

from .calculations import TrafficCalculations
from ..models import TrafficMetadata, RoadInformation, DailyTrafficData, HourlyData


class DataProcessor:
    """Main data processing pipeline"""
    
    def __init__(self):
        self.calculations = TrafficCalculations()
        self.processed_data: Optional[pd.DataFrame] = None
        self.metadata: Optional[TrafficMetadata] = None
    
    def process_raw_data(self, raw_data: pd.DataFrame, metadata: TrafficMetadata, interval_minutes: int = 15) -> Tuple[bool, str]:
        """
        Process raw traffic data.
        
        Args:
            raw_data: Raw traffic DataFrame
            metadata: Metadata about the data
            interval_minutes: Interval for grouping data (default 15 minutes)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.metadata = metadata
            
            # Clean data
            cleaned_data = self._clean_data(raw_data)
            
            # Extract FIM metadata if attached
            fim_metadata = raw_data.attrs.get('fim_metadata', None) if hasattr(raw_data, 'attrs') else None
            
            # Calculate metrics
            processed_data = self._calculate_metrics(cleaned_data, metadata.sequence, fim_metadata, interval_minutes)
            
            # Handle missing values
            processed_data = self.calculations.interpolate_missing_data(processed_data)
            
            self.processed_data = processed_data
            
            return True, "Data processing completed successfully"
        
        except Exception as e:
            return False, f"Error processing data: {str(e)}"
    
    def _clean_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean raw data by removing duplicates and invalid entries.
        Handles both legacy formats and new FIM parser output format.
        
        Args:
            raw_data: Raw data DataFrame
        
        Returns:
            Cleaned DataFrame with standardized structure
        """
        # Remove duplicates
        data = raw_data.drop_duplicates()
        
        # Remove rows with all NaN
        data = data.dropna(how='all')
        
        # Handle negative values in numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            data[col] = data[col].clip(lower=0)
        
        # Normalize column names for FIM parser output
        # The new FIM parser returns: sensor_id, direction, vehicle_class, timestamp, count
        if 'count' in data.columns and 'vehicle_count' not in data.columns:
            data = data.rename(columns={'count': 'vehicle_count'})
        
        # Ensure timestamp is datetime
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
        
        return data.reset_index(drop=True)
    
    def _calculate_metrics(self, data: pd.DataFrame, sequence: int, fim_metadata: dict = None, interval_minutes: int = 15) -> pd.DataFrame:
        """
        Calculate traffic metrics from raw data.
        Groups data into specified time intervals using actual start time from FIM header if available.
        Handles both legacy and new FIM parser output formats.
        
        Args:
            data: Cleaned data DataFrame (with vehicle_count and/or timestamp columns)
            sequence: Time sequence (15, 30, 60, 1440 minutes)
            fim_metadata: Optional dict with year/month/day/start_hour/start_minute/interval_minutes from FIM header
            interval_minutes: Time interval for grouping data in minutes (default 15)
        
        Returns:
            DataFrame with calculated metrics grouped by specified intervals
        """
        processed = data.copy()
        
        # Extract start time from FIM metadata if available
        start_hour = 0
        start_minute = 0
        if fim_metadata:
            start_hour = fim_metadata.get('start_hour', 0) or 0
            start_minute = fim_metadata.get('start_minute', 0) or 0
        
        # Handle FIM parser output (has timestamp and sensor_id, direction, vehicle_class)
        if 'timestamp' in processed.columns and 'vehicle_class' in processed.columns:
            # Group by timestamp and vehicle_class to aggregate VL and PL separately
            processed = processed.groupby(['timestamp', 'vehicle_class']).agg({
                'vehicle_count': 'sum'
            }).reset_index()
            
            # Add time-based columns
            processed['hour'] = processed['timestamp'].dt.hour
            processed['minute'] = processed['timestamp'].dt.minute
            processed['interval_time'] = processed['timestamp'].dt.strftime('%H:%M')
            processed['period'] = processed['hour'].apply(self._get_period)
            
            # Calculate flow (vehicles per minute)
            processed['flow'] = processed['vehicle_count'].apply(
                lambda x: self.calculations.calculate_flow(x, interval_minutes) if 'calculate_flow' in dir(self.calculations) else x / interval_minutes
            )
            
            # Default speed
            if 'speed' not in processed.columns:
                processed['speed'] = 50.0
            
            return processed
        
        # Handle legacy format or generic data
        # Group into specified intervals
        interval_size = max(1, len(processed) // (1440 // interval_minutes))  # intervals per day = 1440 / interval_minutes
        
        if interval_size > 1:
            # Aggregate data into buckets
            grouped_data = []
            for i in range(0, len(processed), interval_size):
                chunk = processed.iloc[i:i+interval_size]
                if chunk.empty:
                    continue
                
                # Sum vehicle counts in this interval
                vehicle_count = chunk['vehicle_count'].sum() if 'vehicle_count' in chunk else 0
                
                # Calculate metrics for this interval
                flow = self.calculations.calculate_flow(vehicle_count, interval_minutes) if hasattr(self.calculations, 'calculate_flow') else vehicle_count / interval_minutes
                speed = 50.0  # Default speed
                
                # Determine hour and minute from row index + start time
                intervals_elapsed = i // interval_size
                total_minutes = start_hour * 60 + start_minute + (intervals_elapsed * interval_minutes)
                hour = (total_minutes // 60) % 24
                minute = total_minutes % 60
                
                # Create interval_time in HH:MM format
                interval_time = f"{int(hour):02d}:{int(minute):02d}"
                
                grouped_data.append({
                    'vehicle_count': vehicle_count,
                    'flow': flow,
                    'speed': speed,
                    'hour': hour,
                    'minute': minute,
                    'interval_time': interval_time,
                    'period': self._get_period(hour)
                })
            
            processed = pd.DataFrame(grouped_data)
        else:
            # If data is small, just process as-is
            if "vehicle_count" in processed.columns:
                processed["flow"] = processed["vehicle_count"].apply(
                    lambda x: self.calculations.calculate_flow(x, interval_minutes) if hasattr(self.calculations, 'calculate_flow') else x / interval_minutes
                )
                if "speed" not in processed.columns:
                    processed["speed"] = 50.0
            
            if "hour" not in processed.columns:
                processed["hour"] = (processed.index // 4).astype(int)  # 4 x 15min = 1 hour
            
            if "minute" not in processed.columns:
                processed["minute"] = ((processed.index % 4) * 15).astype(int)
            
            if "interval_time" not in processed.columns:
                processed["interval_time"] = processed.apply(lambda row: f"{int(row['hour']):02d}:{int(row['minute']):02d}", axis=1)
            
            processed["period"] = processed["hour"].apply(self._get_period)
        
        return processed
    
    @staticmethod
    def _get_period(hour: int) -> str:
        """Determine time period from hour"""
        if 6 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 18:
            return "Afternoon"
        elif 18 <= hour < 24:
            return "Evening"
        else:
            return "Night"
        
        return processed
    
    def get_hourly_summary(self, date_str: Optional[str] = None) -> pd.DataFrame:
        """
        Get hourly summary of traffic data.
        
        Args:
            date_str: Optional date filter
        
        Returns:
            DataFrame with hourly summary
        """
        if self.processed_data is None or self.processed_data.empty:
            return pd.DataFrame()
        
        data = self.processed_data
        
        # Filter by date if provided
        if date_str and "date" in data.columns:
            data = data[data["date"].astype(str).str.contains(date_str)]
        
        # Group by hour
        if "hour" in data.columns:
            hourly = data.groupby("hour").agg({
                "vehicle_count": "sum",
                "flow": "mean",
                "speed": "mean"
            }).reset_index()
            
            return hourly
        
        return data
    
    def get_daily_summary(self) -> Dict:
        """
        Get daily summary statistics.
        
        Returns:
            Dictionary with daily statistics
        """
        if self.processed_data is None or self.processed_data.empty:
            return {}
        
        hourly_data = self.get_hourly_summary()
        return self.calculations.calculate_daily_statistics(hourly_data)
    
    def get_statistical_summary(self) -> Dict:
        """
        Get comprehensive statistical summary.
        
        Returns:
            Dictionary with statistical analysis
        """
        if self.processed_data is None:
            return {}
        
        data = self.processed_data
        numeric_data = data.select_dtypes(include=[np.number])
        
        summary = {}
        for col in numeric_data.columns:
            summary[col] = {
                "mean": float(numeric_data[col].mean()),
                "median": float(numeric_data[col].median()),
                "std": float(numeric_data[col].std()),
                "min": float(numeric_data[col].min()),
                "max": float(numeric_data[col].max()),
                "q25": float(numeric_data[col].quantile(0.25)),
                "q75": float(numeric_data[col].quantile(0.75))
            }
        
        return summary
    
    def export_processed_data(self, output_format: str = "dataframe") -> Optional[pd.DataFrame]:
        """
        Export processed data.
        
        Args:
            output_format: Output format (dataframe, dict, etc.)
        
        Returns:
            Processed data in requested format
        """
        if self.processed_data is None:
            return None
        
        if output_format == "dataframe":
            return self.processed_data.copy()
        elif output_format == "dict":
            return self.processed_data.to_dict(orient="records")
        
        return None
