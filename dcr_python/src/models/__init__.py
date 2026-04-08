"""
Data models for traffic data
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class TrafficMetadata:
    """Metadata for a traffic data file"""
    filename: str
    filepath: str
    format: str  # FIM, DBL, IFX
    sequence: int  # 15, 30, 60, 1440 minutes
    mode: str  # TV Conf., PL Conf., TV Disc., etc.
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    description: str = ""


@dataclass
class RoadInformation:
    """Road information captured during processing"""
    client: str = ""
    service: str = ""
    location: str = ""
    road_type: str = ""
    number_of_lanes: int = 2
    lanes: str = ""  # Alternative name for number_of_lanes (e.g., "2 Voies : 1x1")
    direction: str = ""  # Confondus, Discriminés, Sens 1, etc.
    speed_limit: Optional[float] = None
    mode: str = ""  # Analysis mode (TV Conf., PL Conf., etc.)


@dataclass
class VehicleClassification:
    """Vehicle classification categories"""
    light_vehicles: int = 0  # Voitures particulières
    heavy_vehicles: int = 0  # Poids lourds
    motorcycles: int = 0  # Deux-roues
    total_vehicles: int = 0


@dataclass
class HourlyData:
    """Hourly traffic data"""
    hour: int
    flow: int  # Vehicles/hour
    speed: float  # km/h
    vehicle_count: int
    classification: VehicleClassification = field(default_factory=VehicleClassification)


@dataclass
class DailyTrafficData:
    """Daily traffic data summary"""
    date: datetime
    day_of_week: str
    total_vehicles: int
    average_speed: float
    maximum_speed: float
    minimum_speed: float
    peak_hour: int
    peak_flow: int
    hourly_data: List[HourlyData] = field(default_factory=list)


@dataclass
class TrafficReport:
    """Complete traffic analysis report"""
    metadata: TrafficMetadata
    road_info: RoadInformation
    daily_data: List[DailyTrafficData] = field(default_factory=list)
    summary_statistics: dict = field(default_factory=dict)
    notes: str = ""
