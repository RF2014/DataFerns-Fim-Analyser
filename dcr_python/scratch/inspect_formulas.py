import openpyxl
from openpyxl.utils import get_column_letter

def inspect_formulas():
    template_path = r"dcr_python/src/report-template.xlsx"
    wb = openpyxl.load_workbook(template_path, data_only=False)
    ws = wb['Sens 1']
    
    cells = ['AK11', 'AL11', 'AM11', 'E40', 'E42', 'E44', 'E46', 'E48']
    print(f"Inspecting formulas in {template_path}:")
    for c in cells:
        val = ws[c].value
        print(f"  {c}: {val}")
    
    # Check if there are values in columns E-Y rows 41, 43, 45, 47
    print("\nChecking intermediate data rows:")
    for r in [41, 43, 45, 47]:
        val = ws.cell(row=r, column=5).value # Col E
        print(f"  Row {r}, Col E: {val}")

if __name__ == "__main__":
    inspect_formulas()
