import os
import win32com.client as win32

def migrate_gold_standard_charts_robust():
    gold_path = os.path.abspath(r"C:\Users\suppo\OneDrive\Desktop\FIM Analyser Files\Ville de Estaires - Rue de Merville.xlsx")
    template_path = os.path.abspath(r"c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dcr_python\src\report-template.xlsx")
    
    print(f"Opening Gold Standard: {gold_path}")
    print(f"Target Template: {template_path}")
    
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    
    # Sheet Mapping: Template: GoldStandardSource
    mapping = {
        'Sens 1': 'Sens 1',
        'Sens 2': 'Sens 2',
        'Sens 3': 'Sens 3 (S1+S2)'
    }
    
    try:
        wb_gold = excel.Workbooks.Open(gold_path)
        wb_temp = excel.Workbooks.Open(template_path)
        
        block_height = 56
        target_days = 31

        for temp_name, gold_name in mapping.items():
            print(f"Processing Template {temp_name} from Gold {gold_name}...")
            try:
                ws_gold = wb_gold.Sheets(gold_name)
                ws_temp = wb_temp.Sheets(temp_name)
                
                # 1. Clean existing shapes in template block
                for s in list(ws_temp.Shapes):
                    s.Delete()
                
                # 2. Extract Master shapes (all in first 56 rows)
                master_shapes = []
                for s in ws_gold.Shapes:
                    if s.Top < ws_gold.Rows(block_height + 1).Top:
                        master_shapes.append(s)
                
                print(f"  Found {len(master_shapes)} master shapes.")
                
                # 3. Paste into Template
                for s in master_shapes:
                    s.Copy()
                    ws_temp.Paste()
                    new_s = ws_temp.Shapes(ws_temp.Shapes.Count)
                    new_s.Top = s.Top
                    new_s.Left = s.Left
                    new_s.Width = s.Width
                    new_s.Height = s.Height
                
                # 4. Clone Block
                source_range = ws_temp.Rows(f"1:{block_height}")
                for i in range(1, target_days + 1):
                    dest_row = (i * block_height) + 1
                    source_range.Copy(Destination=ws_temp.Rows(dest_row))
                
                # 5. Deduplicate small logos
                for s in list(ws_temp.Shapes):
                    if s.Left < 150 and s.Top > 150:
                        s.Delete()
                        
            except Exception as se:
                print(f"  Warning: Error processing {temp_name}: {se}")

        wb_temp.Save()
        wb_gold.Close(False)
        wb_temp.Close()
        print("Success: Final Template Restoration Complete.")
        
    except Exception as e:
        print(f"Migration Global Error: {e}")
    finally:
        excel.Quit()

if __name__ == "__main__":
    migrate_gold_standard_charts_robust()
