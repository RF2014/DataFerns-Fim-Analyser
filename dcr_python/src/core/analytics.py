"""
Traffic data analytics engine
"""
import pandas as pd
import numpy as np
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any

class AnalyticsEngine:
    """Core mathematical and statistical logic for traffic data"""

    @staticmethod
    def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers from traffic count data using IQR method.
        Calculates separate thresholds for each direction and vehicle class combination.
        Replaces outlier values with 0.
        """
        if df is None or df.empty or 'count' not in df.columns:
            return df
        
        df = df.copy()
        has_direction = 'direction' in df.columns
        has_vehicle_class = 'vehicle_class' in df.columns
        
        if not has_direction and not has_vehicle_class:
            median = df['count'].median()
            q1 = df['count'].quantile(0.25)
            q3 = df['count'].quantile(0.75)
            iqr = q3 - q1
            threshold = max(q3 + 13 * iqr, median * 10 if median > 0 else 0)
            df.loc[df['count'] > threshold, 'count'] = 0
            return df
        
        group_cols = [c for c in ['direction', 'vehicle_class'] if c in df.columns]
        
        for group_key, group_df in df.groupby(group_cols):
            if len(group_df) == 0: continue
            counts = group_df['count']
            median = counts.median()
            q1 = counts.quantile(0.25)
            q3 = counts.quantile(0.75)
            iqr = q3 - q1
            
            vehicle_class = group_key[1] if isinstance(group_key, tuple) and len(group_key) > 1 else group_key
            n_val = 5 if vehicle_class == 'VL' else 7
            threshold = max(q3 + n_val * iqr, median * 10 if median > 0 else 0)
            df.loc[group_df.index[group_df['count'] > threshold], 'count'] = 0
            
        return df

    @staticmethod
    def compute_busiest_day(df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Find the busiest day (highest traffic) for VL and PL per direction"""
        if df.empty or 'timestamp' not in df.columns:
            return {}, {}
        
        df = df.copy()
        df['date_only'] = df['timestamp'].dt.date
        daily_totals = df.groupby(['direction', 'date_only', 'vehicle_class'])['count'].sum().reset_index()
        
        day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        month_abbr_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        
        vl_busiest, pl_busiest = {}, {}
        for direction in daily_totals['direction'].unique():
            dir_data = daily_totals[daily_totals['direction'] == direction]
            
            for cls_name, target_dict in [('VL', vl_busiest), ('PL', pl_busiest)]:
                cls_data = dir_data[dir_data['vehicle_class'] == cls_name]
                if not cls_data.empty:
                    row = cls_data.loc[cls_data['count'].idxmax()]
                    d = row['date_only']
                    day_name = day_names_fr[d.weekday()]
                    month_abbr = month_abbr_fr[d.month - 1]
                    target_dict[direction] = f"{day_name}, {d.day} {month_abbr} {d.year} ({int(row['count'])})"
        
        return vl_busiest, pl_busiest

    @staticmethod
    def compute_weighted_speed(counts: List[int], centers: List[float]) -> float:
        """Calculate weighted mean speed from distribution bins"""
        total = sum(counts)
        if total <= 0 or not centers:
            return 0.0
        n = min(len(counts), len(centers))
        return sum(counts[i] * centers[i] for i in range(n)) / total

    @staticmethod
    def compute_percentile_speed(counts: List[int], centers: List[float], pct: float) -> float:
        """Calculate percentile speed from distribution bins"""
        total = sum(counts)
        if total <= 0 or not centers:
            return 0.0
        target = total * pct
        running = 0
        for i, count in enumerate(counts):
            running += count
            if running >= target:
                return float(centers[i])
        return float(centers[-1])

    @staticmethod
    def compute_tmj(df: pd.DataFrame) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Compute TMJ (Average Daily Traffic) per direction and class"""
        if df is None or df.empty:
            return {}, {}
        
        df = df.copy()
        df['date_only'] = df['timestamp'].dt.date
        days = df['date_only'].nunique() or 1
        
        table = df.pivot_table(index='direction', columns='vehicle_class', values='count', aggfunc='sum', fill_value=0)
        vl_dir = (table['VL'] / days).to_dict() if 'VL' in table else ((table['2RM'] / days).to_dict() if '2RM' in table else {})
        pl_dir = (table['PL'] / days).to_dict() if 'PL' in table else ((table['2R'] / days).to_dict() if '2R' in table else {})
        
        return {k: int(v) for k, v in vl_dir.items()}, {k: int(v) for k, v in pl_dir.items()}

    @staticmethod
    def compute_hourly_bins(df: pd.DataFrame, direction: str, vehicle_class: str) -> pd.DataFrame:
        """Calculate hourly speed bin totals for a specific direction and class"""
        if df.empty: return pd.DataFrame()
        
        bin_cols = [f"Bin{i+1}" for i in range(12)]
        
        # Subsetting logic with support for 'Total'
        sub = df.copy()
        if direction != 'Total' and 'direction' in sub.columns:
            sub = sub[sub['direction'] == direction]
        if vehicle_class != 'Total' and 'vehicle_class' in sub.columns:
            sub = sub[sub['vehicle_class'] == vehicle_class]
            
        if sub.empty: return pd.DataFrame().reindex(range(24), fill_value=0)
        
        sub['hour'] = sub['timestamp'].dt.hour
        hourly = sub.groupby('hour')[bin_cols].sum().reindex(range(24), fill_value=0)
        return hourly

    @staticmethod
    def compute_speed_metrics_for_report(counts: List[int], centers: List[float], vmax: float = 50.0) -> Dict[str, Any]:
        """Calculate a full suite of speed metrics for a distribution of vehicle counts"""
        total = sum(counts)
        if total <= 0:
            return {f: 0.0 for f in ['mean', 'v15', 'v50', 'v85', 'std', 'infractions', 'inf_pct']}
            
        mean = AnalyticsEngine.compute_weighted_speed(counts, centers)
        v15 = AnalyticsEngine.compute_percentile_speed(counts, centers, 0.15)
        v50 = AnalyticsEngine.compute_percentile_speed(counts, centers, 0.50)
        v85 = AnalyticsEngine.compute_percentile_speed(counts, centers, 0.85)
        
        # Standard deviation from bins
        variance = sum(counts[i] * ((centers[i] - mean) ** 2) for i in range(len(counts))) / total
        std = variance ** 0.5
        
        # Infractions
        inf_count = sum(counts[i] for i in range(len(counts)) if centers[i] > vmax)
        inf_pct = (inf_count / total) * 100
        
        return {
            'mean': mean, 'v15': v15, 'v50': v50, 'v85': v85,
            'std': std, 'infractions': inf_count, 'inf_pct': inf_pct
        }

    @staticmethod
    def compute_period_counts(df: pd.DataFrame, direction: str, vehicle_class: str, periods: List[str]) -> List[int]:
        """Calculate total counts for specific time periods (e.g., peak hours)"""
        if df.empty: return [0] * len(periods)
        
        counts = []
        # Support directional and global aggregations
        if direction == 'Total':
            df_sub = df if vehicle_class == 'Total' else df[df['vehicle_class'] == vehicle_class]
        else:
            df_sub = df[df['direction'] == direction]
            if vehicle_class != 'Total':
                df_sub = df_sub[df_sub['vehicle_class'] == vehicle_class]

        for period in periods:
            try:
                start_str, end_str = period.split('-')
                start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_str.strip(), "%H:%M").time()
                mask = df_sub['timestamp'].dt.time.between(start_time, end_time)
                counts.append(int(df_sub[mask]['count'].sum()))
            except Exception:
                counts.append(0)
        return counts
