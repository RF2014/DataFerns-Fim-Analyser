"""
Report generation module
"""

import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime
from ..models import TrafficReport, RoadInformation


class ReportGenerator:
    """Generates traffic analysis reports"""
    
    @staticmethod
    def generate_summary_report(processed_data: pd.DataFrame, road_info: RoadInformation) -> Dict:
        """
        Generate a summary report.
        
        Args:
            processed_data: Processed traffic data
            road_info: Road information
        
        Returns:
            Dictionary containing report data
        """
        if processed_data is None or processed_data.empty:
            return {}
        
        total_vehicles = processed_data["vehicle_count"].sum() if "vehicle_count" in processed_data else 0
        
        report = {
            "title": "Traffic Analysis Summary Report",
            "generated_date": datetime.now().isoformat(),
            "road_information": {
                "client": road_info.client,
                "service": road_info.service,
                "location": road_info.location,
                "road_type": road_info.road_type,
                "lanes": road_info.number_of_lanes,
                "direction": road_info.direction,
                "speed_limit": road_info.speed_limit
            },
            "statistics": {
                "total_vehicles": int(total_vehicles),
                "average_flow": float(processed_data["flow"].mean()) if "flow" in processed_data else 0,
                "peak_flow": float(processed_data["flow"].max()) if "flow" in processed_data else 0,
                "average_speed": float(processed_data["speed"].mean()) if "speed" in processed_data else 0,
            }
        }
        
        return report
    
    @staticmethod
    def generate_hourly_report(processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate hourly detailed report.
        
        Args:
            processed_data: Processed traffic data
        
        Returns:
            DataFrame with hourly report
        """
        if processed_data is None or processed_data.empty:
            return pd.DataFrame()
        
        if "hour" not in processed_data.columns:
            return processed_data
        
        hourly_report = processed_data.groupby("hour").agg({
            "vehicle_count": ["sum", "mean"],
            "flow": ["sum", "mean", "max"],
            "speed": ["mean", "min", "max"]
        }).reset_index()
        
        hourly_report.columns = ["_".join(col).strip("_") for col in hourly_report.columns.values]
        
        return hourly_report
    
    @staticmethod
    def generate_vehicle_classification_report(processed_data: pd.DataFrame) -> Dict:
        """
        Generate vehicle classification report.
        
        Args:
            processed_data: Processed traffic data
        
        Returns:
            Dictionary with vehicle classification data
        """
        report = {
            "light_vehicles": 0,
            "heavy_vehicles": 0,
            "motorcycles": 0,
            "total_vehicles": 0
        }
        
        if "vehicle_type" in processed_data.columns:
            vehicle_counts = processed_data["vehicle_type"].value_counts().to_dict()
            
            report["light_vehicles"] = int(vehicle_counts.get("light", 0))
            report["heavy_vehicles"] = int(vehicle_counts.get("heavy", 0))
            report["motorcycles"] = int(vehicle_counts.get("motorcycle", 0))
            report["total_vehicles"] = int(processed_data.shape[0])
        
        return report
    
    @staticmethod
    def generate_peak_hours_report(processed_data: pd.DataFrame) -> Dict:
        """
        Generate peak hours analysis report.
        
        Args:
            processed_data: Processed traffic data
        
        Returns:
            Dictionary with peak hours information
        """
        if processed_data is None or processed_data.empty:
            return {"peak_hours": [], "off_peak_hours": []}
        
        if "hour" not in processed_data.columns or "flow" not in processed_data.columns:
            return {"peak_hours": [], "off_peak_hours": []}
        
        hourly_flow = processed_data.groupby("hour")["flow"].mean()
        
        # Peak hours: top 4 hours
        peak_hours = hourly_flow.nlargest(4).index.tolist()
        
        # Off-peak hours: bottom 4 hours
        off_peak_hours = hourly_flow.nsmallest(4).index.tolist()
        
        return {
            "peak_hours": sorted(peak_hours),
            "off_peak_hours": sorted(off_peak_hours),
            "peak_flow_avg": float(hourly_flow.max()),
            "off_peak_flow_avg": float(hourly_flow.min())
        }
    
    @staticmethod
    def generate_comparison_report(data1: pd.DataFrame, data2: pd.DataFrame) -> Dict:
        """
        Generate comparison report between two datasets.
        
        Args:
            data1: First processed dataset
            data2: Second processed dataset
        
        Returns:
            Dictionary with comparison data
        """
        comparison = {
            "dataset1": {
                "total_vehicles": int(data1["vehicle_count"].sum()) if "vehicle_count" in data1 else 0,
                "average_flow": float(data1["flow"].mean()) if "flow" in data1 else 0,
                "average_speed": float(data1["speed"].mean()) if "speed" in data1 else 0,
            },
            "dataset2": {
                "total_vehicles": int(data2["vehicle_count"].sum()) if "vehicle_count" in data2 else 0,
                "average_flow": float(data2["flow"].mean()) if "flow" in data2 else 0,
                "average_speed": float(data2["speed"].mean()) if "speed" in data2 else 0,
            },
            "differences": {}
        }
        
        # Calculate differences
        comparison["differences"]["vehicle_count_diff"] = (
            comparison["dataset2"]["total_vehicles"] - comparison["dataset1"]["total_vehicles"]
        )
        comparison["differences"]["flow_diff"] = (
            comparison["dataset2"]["average_flow"] - comparison["dataset1"]["average_flow"]
        )
        comparison["differences"]["speed_diff"] = (
            comparison["dataset2"]["average_speed"] - comparison["dataset1"]["average_speed"]
        )
        
        return comparison
