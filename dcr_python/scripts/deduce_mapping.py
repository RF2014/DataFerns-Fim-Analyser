"""
Deduce FIM column mapping by testing against known totals and speeds.

Expected results (10:00-22:00, 12 hours):
- Sens 1: VL=15662, PL=1856, mean_speed_VL=21, mean_speed_PL=20, v85_VL=35, v85_PL=34
- Sens 2: VL=13586, PL=2167, mean_speed_VL=32, mean_speed_PL=29, v85_VL=40, v85_PL=39
"""

from pathlib import Path
import pandas as pd
import numpy as np
import itertools

p = Path(r'C:\DCR4402\FIM\C01.fim')
lines = p.read_text(encoding='utf-8', errors='replace').splitlines()

# Speed bins from header row
speeds = [int(t) for t in lines[1].split('.') if t.strip()]
print('Speed bins:', speeds)

# Parse first block data (starting at line 2, skip header and speed labels)
data = lines[2:]
rows = []
for l in data:
    toks = [t for t in l.split('.') if t.strip()]
    nums = [int(t) for t in toks]
    if len(nums) == 12:
        rows.append(nums)

# Take first 144 rows (10:00 to 22:00 = 12 hours × 12 bins/hour)
rows = rows[:144]
df = pd.DataFrame(rows, columns=range(12))

print(f'\nData shape: {df.shape}')
print(f'Column sums:\n{df.sum()}')
print(f'Grand total: {df.sum().sum()}')

# Target totals
target_sens1_vl = 15662
target_sens1_pl = 1856
target_sens2_vl = 13586
target_sens2_pl = 2167

target_sens1_mean_vl = 21
target_sens1_mean_pl = 20
target_sens2_mean_vl = 32
target_sens2_mean_pl = 29

target_sens1_v85_vl = 35
target_sens1_v85_pl = 34
target_sens2_v85_vl = 40
target_sens2_v85_pl = 39

print(f'\nTarget totals:')
print(f'  Sens1: VL={target_sens1_vl}, PL={target_sens1_pl}')
print(f'  Sens2: VL={target_sens2_vl}, PL={target_sens2_pl}')
print(f'  Grand total: {target_sens1_vl + target_sens1_pl + target_sens2_vl + target_sens2_pl}')

def calc_stats(counts, speeds):
    """Calculate mean speed and V85 percentile."""
    total = counts.sum()
    if total == 0:
        return 0, 0
    mean_speed = (counts * speeds).sum() / total
    cum = counts.cumsum()
    v85_idx = (cum >= 0.85 * total).argmax()
    v85 = speeds[v85_idx] if v85_idx < len(speeds) else speeds[-1]
    return mean_speed, v85

# Test all possible 2^12 binary partitions of columns to (Sens1/Sens2 × VL/PL)
# For now, try simpler mappings: contiguous groups or interleaved patterns

best_matches = []

# Strategy 1: Try all ways to partition 12 columns into 4 groups (Sens1_VL, Sens1_PL, Sens2_VL, Sens2_PL)
# Heuristic: group consecutive columns
for s1_vl_start in range(12):
    for s1_vl_len in range(1, 12 - s1_vl_start):
        for s1_pl_start in range(12):
            if s1_pl_start >= s1_vl_start and s1_pl_start < s1_vl_start + s1_vl_len:
                continue
            for s1_pl_len in range(1, 13 - max(s1_vl_start + s1_vl_len, s1_pl_start + 1)):
                # Remaining columns for Sens2
                used = set(range(s1_vl_start, s1_vl_start + s1_vl_len)) | set(range(s1_pl_start, s1_pl_start + s1_pl_len))
                if len(used) < 2:
                    continue
                remaining = [i for i in range(12) if i not in used]
                if len(remaining) < 2:
                    continue
                
                # Try splitting remaining into Sens2_VL and Sens2_PL
                for split_pt in range(1, len(remaining)):
                    s2_vl_cols = remaining[:split_pt]
                    s2_pl_cols = remaining[split_pt:]
                    
                    s1_vl_cols = list(range(s1_vl_start, s1_vl_start + s1_vl_len))
                    s1_pl_cols = list(range(s1_pl_start, s1_pl_start + s1_pl_len))
                    
                    # Compute totals
                    s1_vl_total = df[s1_vl_cols].sum().sum()
                    s1_pl_total = df[s1_pl_cols].sum().sum()
                    s2_vl_total = df[s2_vl_cols].sum().sum()
                    s2_pl_total = df[s2_pl_cols].sum().sum()
                    
                    # Check if totals match
                    if (abs(s1_vl_total - target_sens1_vl) < 100 and
                        abs(s1_pl_total - target_sens1_pl) < 100 and
                        abs(s2_vl_total - target_sens2_vl) < 100 and
                        abs(s2_pl_total - target_sens2_pl) < 100):
                        
                        # Compute speeds
                        s1_vl_speeds = calc_stats(df[s1_vl_cols].sum(), np.array(speeds))
                        s1_pl_speeds = calc_stats(df[s1_pl_cols].sum(), np.array(speeds))
                        s2_vl_speeds = calc_stats(df[s2_vl_cols].sum(), np.array(speeds))
                        s2_pl_speeds = calc_stats(df[s2_pl_cols].sum(), np.array(speeds))
                        
                        error = (
                            abs(s1_vl_total - target_sens1_vl) +
                            abs(s1_pl_total - target_sens1_pl) +
                            abs(s2_vl_total - target_sens2_vl) +
                            abs(s2_pl_total - target_sens2_pl) +
                            abs(s1_vl_speeds[0] - target_sens1_mean_vl) +
                            abs(s1_pl_speeds[0] - target_sens1_mean_pl) +
                            abs(s2_vl_speeds[0] - target_sens2_mean_vl) +
                            abs(s2_pl_speeds[0] - target_sens2_mean_pl)
                        )
                        
                        best_matches.append({
                            'error': error,
                            'sens1_vl_cols': s1_vl_cols,
                            'sens1_pl_cols': s1_pl_cols,
                            'sens2_vl_cols': s2_vl_cols,
                            'sens2_pl_cols': s2_pl_cols,
                            'sens1_vl_total': s1_vl_total,
                            'sens1_pl_total': s1_pl_total,
                            'sens2_vl_total': s2_vl_total,
                            'sens2_pl_total': s2_pl_total,
                            's1_vl_mean': s1_vl_speeds[0],
                            's1_pl_mean': s1_pl_speeds[0],
                            's2_vl_mean': s2_vl_speeds[0],
                            's2_pl_mean': s2_pl_speeds[0],
                            's1_vl_v85': s1_vl_speeds[1],
                            's1_pl_v85': s1_pl_speeds[1],
                            's2_vl_v85': s2_vl_speeds[1],
                            's2_pl_v85': s2_pl_speeds[1],
                        })

if best_matches:
    best_matches.sort(key=lambda x: x['error'])
    print(f'\n\n=== TOP 5 MATCHES ===\n')
    for i, match in enumerate(best_matches[:5]):
        print(f"\nMatch {i+1} (error={match['error']:.1f}):")
        print(f"  Sens1_VL cols: {match['sens1_vl_cols']} -> {match['sens1_vl_total']} (target {target_sens1_vl}, mean {match['s1_vl_mean']:.1f}, v85 {match['s1_vl_v85']})")
        print(f"  Sens1_PL cols: {match['sens1_pl_cols']} -> {match['sens1_pl_total']} (target {target_sens1_pl}, mean {match['s1_pl_mean']:.1f}, v85 {match['s1_pl_v85']})")
        print(f"  Sens2_VL cols: {match['sens2_vl_cols']} -> {match['sens2_vl_total']} (target {target_sens2_vl}, mean {match['s2_vl_mean']:.1f}, v85 {match['s2_vl_v85']})")
        print(f"  Sens2_PL cols: {match['sens2_pl_cols']} -> {match['sens2_pl_total']} (target {target_sens2_pl}, mean {match['s2_pl_mean']:.1f}, v85 {match['s2_pl_v85']})")
else:
    print('\nNo exact matches found. Trying simpler patterns...')
    
    # Try even/odd split
    print('\n\nPattern: Even cols = Sens1, Odd cols = Sens2')
    s1_cols = [0, 2, 4, 6, 8, 10]
    s2_cols = [1, 3, 5, 7, 9, 11]
    s1_total = df[s1_cols].sum().sum()
    s2_total = df[s2_cols].sum().sum()
    print(f'  Sens1 total: {s1_total}, Sens2 total: {s2_total}')
    print(f'  (Target: Sens1_total={target_sens1_vl + target_sens1_pl}, Sens2_total={target_sens2_vl + target_sens2_pl})')
    
    # Try first half / second half
    print('\nPattern: First 6 cols = Sens1, Last 6 cols = Sens2')
    s1_cols = [0, 1, 2, 3, 4, 5]
    s2_cols = [6, 7, 8, 9, 10, 11]
    s1_total = df[s1_cols].sum().sum()
    s2_total = df[s2_cols].sum().sum()
    print(f'  Sens1 total: {s1_total}, Sens2 total: {s2_total}')
    print(f'  (Target: Sens1_total={target_sens1_vl + target_sens1_pl}, Sens2_total={target_sens2_vl + target_sens2_pl})')
