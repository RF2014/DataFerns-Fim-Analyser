"""
Simple test loader for FIM/DBL/IFX files.
Usage:
  python scripts/test_load_fim.py "C:\path\to\file.FIM"

This prints DataFrame diagnostics and attempts to guess processing columns.
"""
import sys
import os
import pandas as pd

# Ensure `src` modules are importable when running this script directly
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from core.fim_parser import parse_fim_file
except Exception:
    parse_fim_file = None

CANDIDATES = {
    'vehicle_count': ['vehicle_count','veh_count','vehcount','nbre','nbveh','count','nveh','nbr_veh','veh','v_count','vcount'],
    'speed': ['speed','vitesse','spd','v85','speed_km','speed_kph','vitesse_kmh'],
    'hour': ['hour','heure','time','t','h','hour_of_day','hh']
}


def guess_columns(df):
    cols = [c.lower() for c in df.columns]
    found = {}
    for target, candidates in CANDIDATES.items():
        for cand in candidates:
            if cand in cols:
                # return original column name (case-sensitive) from df
                for real in df.columns:
                    if real.lower() == cand:
                        found[target] = real
                        break
                if target in found:
                    break
    return found


def load_file(path):
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        return None

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in ['.xlsx', '.xls', '.ifx']:
            df = pd.read_excel(path)
        elif ext == '.fim' and parse_fim_file is not None:
            # Use the dedicated FIM parser when available
            df = parse_fim_file(path)
            return df
        else:
            # try csv or generic text
            try:
                df = pd.read_csv(path)
            except Exception:
                df = pd.read_table(path, sep='\t', engine='python')
        return df
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_load_fim.py <path-to-file>")
        sys.exit(2)

    path = sys.argv[1]
    print(f"Loading: {path}")
    df = load_file(path)
    if df is None:
        print("No data could be loaded.")
        sys.exit(1)

    print(f"Loaded DataFrame: {df.shape[0]} rows x {df.shape[1]} columns")
    print("Columns:")
    for c in df.columns:
        print(f"  - {c} ({df[c].dtype})")

    print("\nFirst 10 rows:\n")
    print(df.head(10).to_string(index=False))

    guessed = guess_columns(df)
    print("\nGuessed mapping:")
    for k in ['vehicle_count','speed','hour']:
        print(f"  {k}: {guessed.get(k, '<not found>')}")

    # Show some basic stats if vehicle_count present
    if 'vehicle_count' in guessed:
        col = guessed['vehicle_count']
        print(f"\n{col} stats:")
        print(df[col].describe())

    print("\nDone.")
