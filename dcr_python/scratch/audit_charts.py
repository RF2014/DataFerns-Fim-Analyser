import os
import win32com.client as win32

def audit_chart_series():
    template_path = os.path.abspath(r"dcr_python/src/report-template.xlsx")
    print(f"Auditing Template: {template_path}")
    
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(template_path)
        for sheet_name in ['Sens 1', 'Sens 2', 'Sens 3']:
            ws = wb.Sheets(sheet_name)
            print(f"\nSheet: {sheet_name}")
            for c in ws.ChartObjects():
                print(f"  Chart: {c.Name} (Pos: {c.Top}, {c.Left})")
                for s in c.Chart.SeriesCollection():
                    try:
                        print(f"    Series {s.Name}: {s.Formula}")
                    except:
                        pass
        wb.Close(False)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        excel.Quit()

if __name__ == "__main__":
    audit_chart_series()
