import os
import win32com.client as win32

def fix_charts_only():
    template_path = os.path.abspath(r"c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dcr_python\src\report-template.xlsx")
    logo_path = os.path.abspath(r"c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dcr_python\src\ui\logo-NC.png")
    
    print(f"Fixing charts only in {template_path}...")
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(template_path)
        block_height = 56
        target_days = 31

        for sheet_name in ['Sens 1', 'Sens 2', 'Sens 3']:
            ws = wb.Sheets(sheet_name)
            print(f"Surgical Chart Repair for {sheet_name}...")
            
            # 1. Clean all charts below the first block
            for s in list(ws.Shapes):
                if s.Top >= ws.Rows(block_height + 1).Top:
                    s.Delete()
            
            # 2. Identify the Master 4 Charts (those in rows 1-56)
            masters = []
            for s in list(ws.Shapes):
                # Avoid branding logo
                if "LOGO" in s.Name or s.Left < 200: continue
                masters.append(s)
            
            print(f"Found {len(masters)} master charts. Cloning to {target_days} days...")
            
            # 3. For each day, Copy and Paste Master Charts to correct position
            for i in range(1, target_days + 1):
                offset_top = ws.Rows(i * block_height + 1).Top
                original_top_avg = ws.Rows(1).Top
                
                # We also need to copy the formatted rows for the grid
                ws.Rows("1:56").Copy(Destination=ws.Rows(i * block_height + 1))
                
                # Wait, the above command clones the rows AND the charts automatically in many Excel versions.
                # However, some versions create duplicate charts on the SAME page.
                # Let's verify.
            
            # 4. Final Sweep: Dedup charts per block
            # (Ensures we don't have overlapping duplicates)
            seen_blocks = {}
            for s in list(ws.Shapes):
                if s.Left < 250: continue # Branding
                block_idx = int(s.Top // (ws.Rows(56).Top + 10)) # Rough block index
                pos = (block_idx, round(s.Top, 0), round(s.Left, 0))
                if pos in seen_blocks:
                    s.Delete()
                else:
                    seen_blocks[pos] = True
                    s.Placement = 1 # xlFreeFloating (but moves with cells)
                    
        wb.Save()
        wb.Close()
        print("Chart Repair Finished.")
        
    except Exception as e:
        print(f"Chart Repair Error: {e}")
    finally:
        excel.Quit()

if __name__ == "__main__":
    fix_charts_only()
