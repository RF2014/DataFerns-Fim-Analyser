# Quick Start Guide - Date Range Filtering

## How to Use Date Range Filtering in Analysis

### Step 1: Click the "Analyse" Button
- Located in the main GUI window
- Triggers the analysis workflow

### Step 2: Select Date/Time Range
A dialog box will appear with two date/time pickers:

**Start Date/Time**
- Shows minimum date/time of your data
- You can change this to filter from a later date/time
- Click calendar icon for calendar picker

**End Date/Time**
- Shows maximum date/time of your data
- You can change this to filter up to an earlier date/time
- Click calendar icon for calendar picker

**Format**: DD/MM/YYYY HH:MM (e.g., 15/01/2024 14:30)

### Step 3: Confirm Date Range
- Click **OK** to confirm your selection
- Click **Annuler** (Cancel) to cancel the analysis

### Step 4: Choose Export Format
After confirming the date range, select where to save:
- **Excel (.xlsx)** - Save as Excel file with charts and statistics
- **PDF (.pdf)** - Save as PDF file with charts and tables
- **Annuler** (Cancel) - Cancel the export

### Step 5: Save File
Navigate to desired location and give your file a name. The analysis will be created with data from your selected date range.

---

## Example Scenarios

### Scenario 1: Analyze Last 7 Days
1. Click "Analyse"
2. Start Date: Change to 7 days before end date
3. End Date: Keep as is (today/latest data)
4. Click OK
5. Choose format and save

### Scenario 2: Analyze Single Day
1. Click "Analyse"
2. Start Date: Select morning at 00:00
3. End Date: Select same day at 23:59
4. Click OK
5. Choose format and save

### Scenario 3: Compare Two Weeks
1. Click "Analyse"
2. Start Date: Select first day of week 1 at 00:00
3. End Date: Select last day of week 2 at 23:59
4. Click OK
5. Choose format and save

---

## Important Notes

### Data Range Constraints
- You **cannot** select dates before your earliest data
- You **cannot** select dates after your latest data
- The pickers automatically limit your options to available data

### What Gets Filtered
✅ Time series graphs (show only selected period)
✅ Statistical calculations (calculated from selected period)
✅ Chart data (uses only selected period)
✅ Daily averages (calculated for selected period)
✅ Working day calculations (considers holidays in selected period)

### What Does NOT Get Filtered
❌ Original data file (not modified)
❌ Future analysis (can choose different range each time)
❌ Export format (settings preserved)

---

## Troubleshooting

### Date Picker Not Responding
- Make sure you're clicking on the text field or calendar icon
- Try double-clicking to activate the calendar picker

### Can't Select Certain Dates
- Check if the date is within your data range
- The pickers only allow dates that contain data

### Analysis Cancelled
- If you clicked Cancel in the date range dialog, the analysis stops
- Click "Analyse" again to retry with different dates

### File Not Created
- Make sure you have write permission to the selected folder
- Check that your disk has enough space
- Try saving to a different location (e.g., Desktop)

---

## Tips & Tricks

1. **Use Calendar Picker**: Click the calendar icon to quickly navigate months/years

2. **Precise Times**: Use keyboard to enter exact times (e.g., 14:30) instead of clicking

3. **Full Range**: To analyze all data, accept the default dates (don't change them)

4. **Partial Day**: You can select any hour/minute combination for precise analysis

5. **Recurring Analysis**: Each time you analyze, the dialog remembers the data range and suggests it

---

## Supported Date/Time Format

**Format**: DD/MM/YYYY HH:MM

**Examples**:
- `01/01/2024 00:00` - January 1st, 2024 at midnight
- `15/06/2024 14:30` - June 15th, 2024 at 2:30 PM
- `31/12/2024 23:59` - December 31st, 2024 at 11:59 PM

**Note**: Times are in 24-hour format (0-23 for hours)

---

## Video Tutorial (if available)
See video: `Date_Range_Filtering_Tutorial.mp4` for visual walkthrough

---

## Contact & Support
For issues or questions, contact: [Support Contact]

**Version**: 1.0  
**Last Updated**: January 2025
