"""
Test the FIM loader GUI metadata display
"""
import sys
sys.path.insert(0, 'src')

from core.fim_parser import parse_fim_file
from datetime import datetime, timedelta
import pandas as pd

def test_metadata_display(file_path):
    """Simulate what the GUI would display"""
    df, meta = parse_fim_file(file_path)
    
    if df is None or meta is None:
        print("Failed to parse file")
        return
    
    # Start datetime
    start_dt = datetime(
        meta.get('year'), meta.get('month'), meta.get('day'),
        meta.get('start_hour'), meta.get('start_minute')
    )
    
    # End datetime
    num_measurements = len(df['timestamp'].unique())
    freq = meta.get('interval_minutes', 60)
    end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))
    
    # Detect speed vs counts by inspecting bin labels
    bins = meta.get('speed_bins', []) or []
    is_speed_bins = (
        len(bins) >= 4
        and all(bins[i] <= bins[i+1] for i in range(len(bins)-1))
        and max(bins) >= 80
    )
    speed_measurement = "Yes" if is_speed_bins else "No"
    traffic_counts = "Yes"

    # Daily averages (counts)
    daily_vl_avg, daily_pl_avg = compute_daily_count_averages(df)
    vl_dir, pl_dir = compute_daily_count_by_direction(df)

    # Average daily speeds (requires speed bins and raw data)
    avg_speed_vl, avg_speed_pl = compute_daily_speed_averages(meta)
    speed_vl_dir, speed_pl_dir = compute_daily_speed_by_direction(meta)
    
    # Vehicle classes
    vehicle_classes = df['vehicle_class'].nunique()
    
    # Directions
    directions = len(df['direction'].unique())
    
    # Display
    print(f"\n{'='*50}")
    print(f"Start Date and Time: {start_dt.strftime('%d/%m/%Y at %H:%M')}")
    print(f"End Date and Time: {end_dt.strftime('%d/%m/%Y at %H:%M')}")
    print(f"Frequency: {freq} minutes")
    print(f"Traffic Counts: {traffic_counts}")
    print(f"Speed Measurement: {speed_measurement}")
    print(f"Vehicle Classes: {vehicle_classes}")
    print(f"Directions: {directions}")
    print(f"Daily VL Average: {fmt_number(daily_vl_avg)}")
    print(f"Daily PL Average: {fmt_number(daily_pl_avg)}")
    print(f"Average Daily Speed VL: {fmt_speed(avg_speed_vl)}")
    print(f"Average Daily Speed PL: {fmt_speed(avg_speed_pl)}")
    print(f"Daily VL Avg by Direction: {fmt_dir(vl_dir, combine_to_two=True)}")
    print(f"Daily PL Avg by Direction: {fmt_dir(pl_dir, combine_to_two=True)}")
    print(f"Avg Daily Speed VL by Direction: {fmt_dir(speed_vl_dir, speed=True, combine_to_two=True)}")
    print(f"Avg Daily Speed PL by Direction: {fmt_dir(speed_pl_dir, speed=True, combine_to_two=True)}")
    print(f"{'='*50}")


def fmt_number(val: float) -> str:
    return f"{val:.1f}" if val is not None else "--"


def fmt_speed(val: float) -> str:
    return f"{val:.1f} km/h" if val is not None else "--"


def compute_daily_count_averages(df):
    if df.empty or 'timestamp' not in df:
        return None, None
    df = df.copy()
    df['date_only'] = df['timestamp'].dt.date
    grouped = df.groupby(['date_only', 'vehicle_class'])['count'].sum().unstack(fill_value=0)
    vl_avg = grouped.get('VL', pd.Series(dtype=float)).mean() if not grouped.empty else None
    pl_avg = grouped.get('PL', pd.Series(dtype=float)).mean() if not grouped.empty else None
    return vl_avg, pl_avg


def compute_daily_speed_averages(meta):
    bins = meta.get('speed_bins') or []
    raw = meta.get('raw_data') or []
    rows_per_block = meta.get('rows_per_block') or 0
    num_sensors = meta.get('num_sensors') or 0
    vl_cols = meta.get('vl_columns') or [0, 1]
    pl_cols = meta.get('pl_columns') or [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    freq = meta.get('interval_minutes', 60)

    if len(bins) < 4 or not raw or rows_per_block == 0 or num_sensors == 0:
        return None, None
    try:
        start_dt = datetime(meta['year'], meta['month'], meta['day'], meta['start_hour'], meta['start_minute'])
    except Exception:
        return None, None

    daily_vl_num, daily_vl_den = {}, {}
    daily_pl_num, daily_pl_den = {}, {}

    for sensor_id in range(num_sensors):
        start_row = sensor_id * rows_per_block
        end_row = min(start_row + rows_per_block, len(raw))
        block = raw[start_row:end_row]
        for idx, row_vals in enumerate(block):
            ts = start_dt + timedelta(minutes=freq * idx)
            d = ts.date()
            vl_counts = [row_vals[i] for i in vl_cols if i < len(row_vals) and i < len(bins)]
            vl_num = sum(v * bins[i] for i, v in zip(vl_cols, vl_counts) if i < len(bins))
            vl_den = sum(vl_counts)
            if vl_den > 0:
                daily_vl_num[d] = daily_vl_num.get(d, 0) + vl_num
                daily_vl_den[d] = daily_vl_den.get(d, 0) + vl_den
            pl_counts = [row_vals[i] for i in pl_cols if i < len(row_vals) and i < len(bins)]
            pl_num = sum(v * bins[i] for i, v in zip(pl_cols, pl_counts) if i < len(bins))
            pl_den = sum(pl_counts)
            if pl_den > 0:
                daily_pl_num[d] = daily_pl_num.get(d, 0) + pl_num
                daily_pl_den[d] = daily_pl_den.get(d, 0) + pl_den

    def avg_daily_speed(num_map, den_map):
        if not num_map:
            return None
        daily_avgs = [num_map[d]/den_map[d] for d in num_map if den_map.get(d,0) > 0]
        return sum(daily_avgs)/len(daily_avgs) if daily_avgs else None

    return avg_daily_speed(daily_vl_num, daily_vl_den), avg_daily_speed(daily_pl_num, daily_pl_den)


def compute_daily_count_by_direction(df):
    if df.empty or 'timestamp' not in df:
        return {}, {}
    df = df.copy()
    df['date_only'] = df['timestamp'].dt.date
    table = df.pivot_table(index=['direction', 'date_only'], columns='vehicle_class', values='count', aggfunc='sum', fill_value=0)
    vl_dir = table['VL'].groupby(level=0).mean() if 'VL' in table else pd.Series(dtype=float)
    pl_dir = table['PL'].groupby(level=0).mean() if 'PL' in table else pd.Series(dtype=float)
    return vl_dir.to_dict(), pl_dir.to_dict()


def compute_daily_speed_by_direction(meta):
    bins = meta.get('speed_bins') or []
    raw = meta.get('raw_data') or []
    rows_per_block = meta.get('rows_per_block') or 0
    num_sensors = meta.get('num_sensors') or 0
    vl_cols = meta.get('vl_columns') or [0, 1]
    pl_cols = meta.get('pl_columns') or [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    freq = meta.get('interval_minutes', 60)
    sensor_names = meta.get('sensor_names') or {}

    if len(bins) < 4 or not raw or rows_per_block == 0 or num_sensors == 0:
        return {}, {}
    try:
        start_dt = datetime(meta['year'], meta['month'], meta['day'], meta['start_hour'], meta['start_minute'])
    except Exception:
        return {}, {}

    vl_num = {}
    vl_den = {}
    pl_num = {}
    pl_den = {}

    for sensor_id in range(num_sensors):
        dir_label = sensor_names.get(sensor_id, f"Sens {sensor_id+1}")
        start_row = sensor_id * rows_per_block
        end_row = min(start_row + rows_per_block, len(raw))
        block = raw[start_row:end_row]
        for idx, row_vals in enumerate(block):
            ts = start_dt + timedelta(minutes=freq * idx)
            d = ts.date()
            vl_counts = [row_vals[i] for i in vl_cols if i < len(row_vals) and i < len(bins)]
            vl_num_val = sum(v * bins[i] for i, v in zip(vl_cols, vl_counts) if i < len(bins))
            vl_den_val = sum(vl_counts)
            if vl_den_val > 0:
                vl_num[(dir_label, d)] = vl_num.get((dir_label, d), 0) + vl_num_val
                vl_den[(dir_label, d)] = vl_den.get((dir_label, d), 0) + vl_den_val
            pl_counts = [row_vals[i] for i in pl_cols if i < len(row_vals) and i < len(bins)]
            pl_num_val = sum(v * bins[i] for i, v in zip(pl_cols, pl_counts) if i < len(bins))
            pl_den_val = sum(pl_counts)
            if pl_den_val > 0:
                pl_num[(dir_label, d)] = pl_num.get((dir_label, d), 0) + pl_num_val
                pl_den[(dir_label, d)] = pl_den.get((dir_label, d), 0) + pl_den_val

    def avg_by_dir(num_map, den_map):
        out = {}
        dirs = {k[0] for k in num_map.keys()}
        for dir_label in dirs:
            vals = [num_map[k] / den_map[k] for k in num_map if k[0] == dir_label and den_map.get(k, 0) > 0]
            if vals:
                out[dir_label] = sum(vals) / len(vals)
        return out

    return avg_by_dir(vl_num, vl_den), avg_by_dir(pl_num, pl_den)


def fmt_dir(d: dict, speed: bool = False, combine_to_two: bool = False) -> str:
    if not d:
        return "--"
    data = d
    if combine_to_two:
        agg = {'Sens 1': [], 'Sens 2': []}
        for k, v in d.items():
            if v is None:
                continue
            key = 'Sens 2' if ('2' in str(k) or 'Opp' in str(k) or '2' in str(k).split()) else 'Sens 1'
            agg[key].append(v)
        data = {k: (sum(vals)/len(vals) if vals else None) for k, vals in agg.items() if vals}
    parts = []
    for k, v in data.items():
        if v is None:
            continue
        parts.append(f"{k}: {v:.1f}{' km/h' if speed else ''}")
    return ", ".join(parts) if parts else "--"

# Test all files
files = [
    r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\C01.fim',
    r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0003.FIM',
    r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\FIME0004.FIM',
    r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX02_2512081115_M4H_WA.FIM',
    r'c:\Users\royston.fernandes\Documents\CodeVBA_fim\data_test\MIX04_2511271715_M4H_WA.FIM',
]

for file_path in files:
    try:
        print(f"\nTesting: {file_path.split(chr(92))[-1]}")
        test_metadata_display(file_path)
    except Exception as e:
        print(f"Error: {e}")
