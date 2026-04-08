#!/usr/bin/env python3
"""Fix vehicle class filtering in page 4 methods"""

with open('dcr_python/src/ui/fim_loader.py', 'r') as f:
    lines = f.readlines()

# Find and fix lines with the bad logic
# Pattern: if vehicle_class == 'VL' or vehicle_class == 'ALL'
count_fixes = 0

for i in range(len(lines)):
    line = lines[i]
    
    # Only fix in page 4 methods (around lines 2192 and beyond for Excel)
    if i >= 2185:  # Only in the page 4 section
        if "if vehicle_class == 'VL' or vehicle_class == 'ALL':" in line:
            # Replace the two lines
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            
            # Check if next lines are the expected vl_ operations
            if i+1 < len(lines) and 'vl_numerator[hour] +=' in lines[i+1]:
                if i+2 < len(lines) and 'vl_denominator[hour] +=' in lines[i+2]:
                    if i+3 < len(lines) and "if vehicle_class == 'PL' or vehicle_class == 'ALL':" in lines[i+3]:
                        # Found the pattern - fix it
                        lines[i] = indent_str + "# Only accumulate for matching vehicle class - don't double count 'ALL'\n"
                        lines[i] += indent_str + "if vehicle_class == 'VL':\n"
                        lines[i+1] = indent_str + "    vl_numerator[hour] += count * speed_center\n"
                        lines[i+2] = indent_str + "    vl_denominator[hour] += count\n"
                        lines[i+3] = indent_str + "elif vehicle_class == 'PL':\n"
                        
                        # Fix PL lines too (should be i+4, i+5)
                        if i+4 < len(lines) and 'pl_numerator[hour] +=' in lines[i+4]:
                            lines[i+4] = indent_str + "    pl_numerator[hour] += count * speed_center\n"
                        if i+5 < len(lines) and 'pl_denominator[hour] +=' in lines[i+5]:
                            lines[i+5] = indent_str + "    pl_denominator[hour] += count\n"
                        
                        count_fixes += 1
                        print(f"Fixed vehicle class filtering at line {i+1}")

print(f"\nTotal fixes applied: {count_fixes}")

with open('dcr_python/src/ui/fim_loader.py', 'w') as f:
    f.writelines(lines)

print("File saved successfully")
