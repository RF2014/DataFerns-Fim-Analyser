import os
import win32com.client as win32

def remove_duplicate_charts_only():
    template_path = os.path.abspath(r"c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dcr_python\src\report-template.xlsx")
    
    print(f"Cleaning duplicated charts from {template_path}...")
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(template_path)
        block_height = 56

        for sheet_name in ['Sens 1', 'Sens 2', 'Sens 3']:
            ws = wb.Sheets(sheet_name)
            print(f"Auditing {sheet_name} for duplicates...")
            
            # Group shapes by block
            # Block N starts at Rows(N*56 + 1)
            # block_id = int(shape.Top // ws.Rows(56).Top)
            
            blocks = {}
            for s in list(ws.Shapes):
                # Branding is small, Left < 100
                if s.Left < 150: continue 
                
                # Identify block (0-31)
                # We use a bit of tolerance for floating charts
                block_id = int((s.Top + 10) // ws.Rows(56).Top)
                
                # Key based on Relative Position within block and Type
                # Using rounded coordinates to catch overlapping duplicates
                rel_top = round(s.Top % ws.Rows(56).Top, 0)
                rel_left = round(s.Left, 0)
                pos_key = (block_id, rel_top, rel_left)
                
                if pos_key in blocks:
                    print(f"  Deleting duplicate chart in block {block_id} at {rel_top}, {rel_left}")
                    s.Delete()
                else:
                    blocks[pos_key] = s
                    
        wb.Save()
        wb.Close()
        print("Success: Duplicated charts removed. Template is now clean.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        excel.Quit()

if __name__ == "__main__":
    remove_duplicate_charts_only()
