"""
Fix page 4 vehicle class filtering and add debug output
"""

with open('dcr_python/src/ui/fim_loader.py', 'r') as f:
    content = f.read()

# Fix the vehicle class filtering logic - replace both occurrences (PDF and Excel)
old_logic = """                        if vehicle_class == 'VL' or vehicle_class == 'ALL':
                            vl_numerator[hour] += count * speed_center
                            vl_denominator[hour] += count
                        if vehicle_class == 'PL' or vehicle_class == 'ALL':
                            pl_numerator[hour] += count * speed_center
                            pl_denominator[hour] += count"""

new_logic = """                        # Only accumulate for matching vehicle class (not 'ALL')
                        if vehicle_class == 'VL':
                            vl_numerator[hour] += count * speed_center
                            vl_denominator[hour] += count
                        elif vehicle_class == 'PL':
                            pl_numerator[hour] += count * speed_center
                            pl_denominator[hour] += count"""

# Count and replace
count = content.count(old_logic)
print(f"Found {count} occurrences of old vehicle class filtering logic")

content = content.replace(old_logic, new_logic)

# Also add debug output after the calculation loop
old_calc = """            # Calculate mean speeds for each hour
            for hour in range(24):
                if vl_denominator[hour] > 0:
                    vl_mean_by_hour[hour] = vl_numerator[hour] / vl_denominator[hour]
                if pl_denominator[hour] > 0:
                    pl_mean_by_hour[hour] = pl_numerator[hour] / pl_denominator[hour]
            
            # Plot with real data (no alpha transparency)"""

new_calc = """            # Calculate mean speeds for each hour
            for hour in range(24):
                if vl_denominator[hour] > 0:
                    vl_mean_by_hour[hour] = vl_numerator[hour] / vl_denominator[hour]
                if pl_denominator[hour] > 0:
                    pl_mean_by_hour[hour] = pl_numerator[hour] / pl_denominator[hour]
            
            # DEBUG: Print calculated values
            print("\\n=== PAGE 4 CALCULATED SPEEDS ===")
            for hour in range(24):
                if vl_denominator[hour] > 0 or pl_denominator[hour] > 0:
                    vl_str = f"{vl_mean_by_hour[hour]:.1f}" if vl_denominator[hour] > 0 else "--"
                    pl_str = f"{pl_mean_by_hour[hour]:.1f}" if pl_denominator[hour] > 0 else "--"
                    print(f"Hour {hour:02d}: VL={vl_str} | PL={pl_str}")
            
            # Plot with real data (no alpha transparency)"""

calc_count = content.count(old_calc)
print(f"Found {calc_count} occurrences of calculation section to add debug")

content = content.replace(old_calc, new_calc)

with open('dcr_python/src/ui/fim_loader.py', 'w') as f:
    f.write(content)

print("File updated successfully")
