"""
Traffic data calculations module
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class TrafficCalculations:
    """Performs traffic data calculations"""
    
    @staticmethod
    def calculate_flow(vehicle_count: int, time_interval_minutes: int) -> float:
        """
        Calculate traffic flow (vehicles per hour).
        
        Args:
            vehicle_count: Number of vehicles
            time_interval_minutes: Time interval in minutes
        
        Returns:
            Flow in vehicles per hour
        """
        if time_interval_minutes <= 0:
            return 0
        return (vehicle_count * 60) / time_interval_minutes
    
    @staticmethod
    def calculate_average_speed(speeds: List[float]) -> float:
        """
        Calculate average speed.
        
        Args:
            speeds: List of speed measurements
        
        Returns:
            Average speed in km/h
        """
        if not speeds or len(speeds) == 0:
            return 0
        return np.mean(speeds)
    
    @staticmethod
    def calculate_speed_percentile(speeds: List[float], percentile: int) -> float:
        """
        Calculate speed percentile (e.g., 85th percentile).
        
        Args:
            speeds: List of speed measurements
            percentile: Percentile value (0-100)
        
        Returns:
            Speed at given percentile
        """
        if not speeds or len(speeds) == 0:
            return 0
        return np.percentile(speeds, percentile)
    
    @staticmethod
    def classify_vehicles(total_vehicles: int, light_ratio: float = 0.8) -> Dict[str, int]:
        """
        Classify vehicles into categories.
        
        Args:
            total_vehicles: Total number of vehicles
            light_ratio: Ratio of light vehicles (0-1)
        
        Returns:
            Dictionary with vehicle classifications
        """
        light = int(total_vehicles * light_ratio)
        heavy = total_vehicles - light
        
        return {
            "light_vehicles": light,
            "heavy_vehicles": heavy,
            "total": total_vehicles
        }
    
    @staticmethod
    def calculate_peak_hour(hourly_data: pd.DataFrame, value_column: str = "flow") -> Dict:
        """
        Find the peak hour in traffic data.
        
        Args:
            hourly_data: DataFrame with hourly traffic data
            value_column: Column to find peak for
        
        Returns:
            Dictionary with peak hour information
        """
        if hourly_data.empty:
            return {"hour": 0, "value": 0}
        
        peak_idx = hourly_data[value_column].idxmax()
        peak_row = hourly_data.loc[peak_idx]
        
        return {
            "hour": int(peak_row.get("hour", 0)),
            "value": float(peak_row[value_column]),
            "index": peak_idx
        }
    
    @staticmethod
    def calculate_off_peak_hours(hourly_data: pd.DataFrame, threshold_percentile: int = 25) -> List[int]:
        """
        Find off-peak hours based on flow threshold.
        
        Args:
            hourly_data: DataFrame with hourly traffic data
            threshold_percentile: Percentile to use as threshold
        
        Returns:
            List of off-peak hours
        """
        if hourly_data.empty:
            return []
        
        threshold = hourly_data["flow"].quantile(threshold_percentile / 100)
        off_peak = hourly_data[hourly_data["flow"] <= threshold]["hour"].tolist()
        
        return sorted(off_peak)
    
    @staticmethod
    def calculate_congestion_index(flow: int, capacity: int) -> float:
        """
        Calculate congestion index (0 = free flow, 1 = congested).
        
        Args:
            flow: Current traffic flow
            capacity: Road capacity
        
        Returns:
            Congestion index (0-1)
        """
        if capacity <= 0:
            return 0
        
        index = flow / capacity
        return min(index, 1.0)  # Cap at 1.0
    
    @staticmethod
    def calculate_daily_statistics(hourly_data: pd.DataFrame) -> Dict:
        """
        Calculate daily summary statistics.
        
        Args:
            hourly_data: DataFrame with hourly traffic data
        
        Returns:
            Dictionary with summary statistics
        """
        if hourly_data.empty:
            return {
                "total_vehicles": 0,
                "average_flow": 0,
                "peak_flow": 0,
                "average_speed": 0,
                "min_speed": 0,
                "max_speed": 0
            }
        
        return {
            "total_vehicles": int(hourly_data["vehicle_count"].sum()),
            "average_flow": float(hourly_data["flow"].mean()),
            "peak_flow": float(hourly_data["flow"].max()),
            "average_speed": float(hourly_data["speed"].mean()) if "speed" in hourly_data else 0,
            "min_speed": float(hourly_data["speed"].min()) if "speed" in hourly_data else 0,
            "max_speed": float(hourly_data["speed"].max()) if "speed" in hourly_data else 0
        }
    
    @staticmethod
    def interpolate_missing_data(data: pd.DataFrame, method: str = "linear") -> pd.DataFrame:
        """
        Interpolate missing data in time series.
        
        Args:
            data: DataFrame with potential missing values
            method: Interpolation method (linear, forward_fill, etc.)
        
        Returns:
            DataFrame with interpolated values
        """
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if method == "linear":
                data[col] = data[col].interpolate(method="linear")
            elif method == "forward_fill":
                data[col] = data[col].fillna(method="ffill")
            elif method == "backward_fill":
                data[col] = data[col].fillna(method="bfill")
        
        return data
