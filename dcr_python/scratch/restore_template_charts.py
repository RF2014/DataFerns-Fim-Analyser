import os
import win32com.client as win32

def migrate_gold_standard_charts():
    gold_path = os.path.abspath(r"C:\Users\suppo\OneDrive\Desktop\FIM Analyser Files\Ville de Estaires - Rue de Merville.xlsx")
    template_path = os.path.abspath(r"c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dcr_python\src\report-template.xlsx")
    
    print(f"Opening Gold Standard: {gold_path}")
    print(f"Target Template: {template_path}")
    
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    try:
        wb_gold = excel.Workbooks.Open(gold_path)
        wb_temp = excel.Workbooks.Open(template_path)
        
        block_height = 56
        target_days = 31

        for sheet_name in ['Sens 1', 'Sens 2', 'Sens 3']:
            print(f"Processing {sheet_name}...")
            ws_gold = wb_gold.Sheets(sheet_name)
            ws_temp = wb_temp.Sheets(sheet_name)
            
            # 1. Clean existing charts in template (ALL OF THEM)
            # We will rebuild from Gold Standard to ensure perfect geometry
            for s in list(ws_temp.Shapes):
                s.Delete()
            
            # 2. Extract the 4 Master Charts from Gold Standard (Top block only)
            master_shapes = []
            for s in ws_gold.Shapes:
                if s.Top < ws_gold.Rows(block_height + 1).Top:
                    # It's in the first block
                    master_shapes.append(s)
            
            print(f"  Found {len(master_shapes)} master shapes in Gold Standard.")
            
            # 3. Copy/Paste these 4 into Template Block 1
            # We copy them as a group or individually
            for s in master_shapes:
                s.Copy()
                ws_temp.Paste()
                new_shape = ws_temp.Shapes(ws_temp.Shapes.Count)
                new_shape.Top = s.Top
                new_shape.Left = s.Left
                new_shape.Width = s.Width
                new_shape.Height = s.Height

            # 4. Use Row Copy to expand this perfect block to 31 more days
            # This is the most stable way to clone charts in Excel
            source_range = ws_temp.Rows(f"1:{block_height}")
            for i in range(1, target_days + 1):
                dest_row = (i * block_height) + 1
                source_range.Copy(Destination=ws_temp.Rows(dest_row))
                
            # 5. Clean redundant branding (logos) on pages 2-32
            # Logos are small and in top-left of each block
            for s in list(ws_temp.Shapes):
                rel_top = s.Top % ws_temp.Rows(block_height + 1).Top
                # If it's a small shape (logo) and not on page 1
                if s.Left < 150 and s.Top > 150:
                    s.Delete()

        wb_temp.Save()
        wb_gold.Close(False)
        wb_temp.Close()
        print("Success: Gold Standard charts migrated and cloned across all 32 days.")
        
    except Exception as e:
        print(f"Migration Error: {e}")
    finally:
        excel.Quit()

if __name__ == "__main__":
    migrate_gold_standard_charts()
