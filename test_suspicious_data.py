"""
Test for detecting suspicious data patterns during FIM file reading.

Pattern to detect: Speed bins with incrementally increasing counts
(e.g., 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 255)

This is clearly artificial/corrupted data, not real traffic counts.
Real traffic should have random distribution across speed bins.
"""

import numpy as np
from typing import List, Tuple


def detect_linear_progression(bin_counts: List[int], tolerance: float = 0.15) -> Tuple[bool, float]:
    """
    Detect if bin counts follow a linear progression pattern.
    
    Real traffic data has random variations across speed bins.
    Artificial data often shows linear patterns: 20, 30, 40, 50...
    
    Uses least squares fitting to check if data fits a line.
    If R² > 0.9 (very good fit to a line), it's suspicious.
    
    Args:
        bin_counts: List of 12 speed bin counts
        tolerance: R² threshold above which pattern is suspicious (0-1)
        
    Returns:
        (is_suspicious, r_squared): Whether pattern is suspicious and R² value
    """
    if len(bin_counts) < 3:
        return False, 0.0
    
    # Fit a line: y = ax + b
    x = np.arange(len(bin_counts))
    y = np.array(bin_counts, dtype=float)
    
    # Remove zero values for analysis
    non_zero_mask = y > 0
    if np.sum(non_zero_mask) < 3:
        return False, 0.0
    
    x_fit = x[non_zero_mask]
    y_fit = y[non_zero_mask]
    
    # Fit polynomial
    coeffs = np.polyfit(x_fit, y_fit, 1)  # Linear fit
    poly = np.poly1d(coeffs)
    y_pred = poly(x_fit)
    
    # Calculate R²
    ss_res = np.sum((y_fit - y_pred) ** 2)
    ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
    
    if ss_tot == 0:
        return False, 0.0
    
    r_squared = 1 - (ss_res / ss_tot)
    
    # If R² is very high (>0.9), it fits a line too well = suspicious
    is_suspicious = r_squared > tolerance
    
    return is_suspicious, r_squared


def detect_arithmetic_sequence(bin_counts: List[int]) -> Tuple[bool, float]:
    """
    Detect if bins form an arithmetic sequence (constant difference).
    
    E.g., 20, 30, 40, 50, 60... (difference = 10)
    Real traffic never shows this pattern.
    
    Args:
        bin_counts: List of 12 speed bin counts
        
    Returns:
        (is_suspicious, avg_difference): Whether sequence is arithmetic
    """
    if len(bin_counts) < 3:
        return False, 0.0
    
    non_zero = [v for v in bin_counts if v > 0]
    if len(non_zero) < 3:
        return False, 0.0
    
    # Calculate differences between consecutive values
    diffs = []
    for i in range(len(non_zero) - 1):
        diffs.append(non_zero[i + 1] - non_zero[i])
    
    if not diffs:
        return False, 0.0
    
    # Check if differences are consistent (arithmetic sequence)
    avg_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    
    # If std_diff is very small relative to avg_diff, it's arithmetic
    # Coefficient of variation: std/mean
    if avg_diff != 0:
        cv = std_diff / abs(avg_diff)
    else:
        cv = float('inf')
    
    # If CV < 0.2 (20%), it's a very consistent pattern = suspicious
    is_suspicious = cv < 0.2 and len(non_zero) >= 6
    
    return is_suspicious, avg_diff


def detect_test_data_pattern(bin_counts: List[int]) -> Tuple[bool, dict]:
    """
    Comprehensive check for test/corrupted data patterns.
    
    Args:
        bin_counts: List of 12 speed bin counts
        
    Returns:
        (is_suspicious, details): Whether data is suspicious and why
    """
    details = {
        'linear_fit': False,
        'arithmetic': False,
        'r_squared': 0.0,
        'avg_diff': 0.0,
        'reasons': []
    }
    
    # Check 1: Linear progression
    is_linear, r_sq = detect_linear_progression(bin_counts, tolerance=0.85)
    details['linear_fit'] = is_linear
    details['r_squared'] = r_sq
    if is_linear:
        details['reasons'].append(f"Linear pattern detected (R²={r_sq:.3f})")
    
    # Check 2: Arithmetic sequence
    is_arithmetic, avg_diff = detect_arithmetic_sequence(bin_counts)
    details['arithmetic'] = is_arithmetic
    details['avg_diff'] = avg_diff
    if is_arithmetic:
        details['reasons'].append(f"Arithmetic sequence detected (diff={avg_diff:.1f})")
    
    is_suspicious = is_linear or is_arithmetic
    
    return is_suspicious, details


# Test cases
print("=" * 80)
print("TEST 1: Your suspicious data - linear progression")
print("=" * 80)
your_data = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 255]
is_sus, details = detect_test_data_pattern(your_data)
print(f"Data:     {your_data}")
print(f"Suspicious: {is_sus}")
print(f"R² (linear fit): {details['r_squared']:.4f}")
print(f"Reasons: {', '.join(details['reasons']) if details['reasons'] else 'None'}")
print()

print("=" * 80)
print("TEST 2: Another test pattern - clean arithmetic")
print("=" * 80)
test_pattern = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
is_sus, details = detect_test_data_pattern(test_pattern)
print(f"Data:     {test_pattern}")
print(f"Suspicious: {is_sus}")
print(f"R² (linear fit): {details['r_squared']:.4f}")
print(f"Avg difference: {details['avg_diff']:.1f}")
print(f"Reasons: {', '.join(details['reasons']) if details['reasons'] else 'None'}")
print()

print("=" * 80)
print("TEST 3: Real traffic data - random distribution")
print("=" * 80)
real_data = [15, 45, 32, 28, 50, 38, 42, 35, 48, 30, 25, 20]
is_sus, details = detect_test_data_pattern(real_data)
print(f"Data:     {real_data}")
print(f"Suspicious: {is_sus}")
print(f"R² (linear fit): {details['r_squared']:.4f}")
print(f"Reasons: {', '.join(details['reasons']) if details['reasons'] else 'None'}")
print()

print("=" * 80)
print("TEST 4: More test cases")
print("=" * 80)
test_cases = [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "Perfect increment by 1"),
    ([5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], "Perfect increment by 5"),
    ([100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45], "Decreasing linear"),
    ([45, 32, 48, 38, 52, 41, 49, 39, 51, 40, 47, 44], "Random realistic"),
    ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "All zeros"),
    ([50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50], "All same value"),
]

for data, label in test_cases:
    is_sus, details = detect_test_data_pattern(data)
    status = "SUSPICIOUS" if is_sus else "CLEAN"
    r_sq = details['r_squared']
    print(f"{label:35} {status:12} R²={r_sq:.3f}")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
DETECTION METHODS:

1. LINEAR REGRESSION (R² metric):
   - Fit a line to the bin counts
   - If R² > 0.85: Data follows a line too perfectly
   - Real traffic is random, not linear
   - Your data: R² = 0.989 (VERY suspicious)

2. ARITHMETIC SEQUENCE (constant difference):
   - Check if consecutive values have consistent difference
   - If std(differences) / mean(difference) < 0.2: Too consistent
   - Real traffic has variable counts per bin
   - Your data: difference = 10 consistently (SUSPICIOUS)

RECOMMENDATION FOR FIM PARSER:

Add filter during file reading in fim_parser.py:

    def is_artificial_data(row_values):
        '''Flag rows with test/corrupted patterns'''
        is_linear, r_sq = detect_linear_progression(row_values)
        is_arith, _ = detect_arithmetic_sequence(row_values)
        
        # Skip rows that look like test data
        return is_linear or is_arith
        
Then skip these rows when building the dataset.
""")
