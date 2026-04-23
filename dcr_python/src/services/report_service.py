"""
Standardized Reporting Service V4
Targets a uniform template structure: Synthese, Sens 1, Sens 2, Sens 3.
"""
import os
import shutil
import pandas as pd
import openpyxl
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from ..core.analytics import AnalyticsEngine
from ..utils.helpers import resource_path

class ReportService:
    @staticmethod
    def generate_report(df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any], output_folder: str) -> str:
        template_path = resource_path("report-template.xlsx")
        output_path = os.path.join(output_folder, f"Rapport_{settings.get('site_name', 'Trafic')}.xlsx")
        shutil.copy2(template_path, output_path)
        
        # Load without external links to prevent security warnings
        wb = openpyxl.load_workbook(output_path, keep_links=False)
        
        # Calculate days for indexing and layout
        days = sorted(df['timestamp'].dt.date.unique())
        num_days = len(days)
        
        # 0. Global Cleanup: Kill all external links in charts
        for ws in wb.worksheets:
            if hasattr(ws, '_charts'):
                for chart in ws._charts:
                    if hasattr(chart, 'external_data_source') and chart.external_data_source:
                        chart.external_data_source = None

        # 1. Update Global Metadata (Site, Vmax, Sect, Period)
        ReportService._global_metadata_propagation(wb, df, settings)

        # 2. Main Sheet Injection (Strict Mapping)
        standard_sheets = {
            'Synthese_des_donnees': 'mixed',
            'Sens 1': 'Sens 1',
            'Sens 2': 'Sens 2',
            'Sens 3': 'Total'
        }
        
        for sheet_name, direction in standard_sheets.items():
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                if sheet_name == 'Synthese_des_donnees':
                    ReportService._populate_synthesis(ws, df, metadata, settings)
                else:
                    ReportService._populate_full_sheet(ws, df, metadata, settings, direction, days)
                    
                    # Update Print Area to match current days (Expanded to AR for full width)
                    last_printable_row = 57 + (num_days * 56)
                    ws.print_area = f'A1:AR{last_printable_row}'
                    
                    # Layout Management
                    ws.page_setup.fitToWidth = 1
                    ws.page_setup.fitToHeight = 0 # Use manual breaks naturally
                    ws.sheet_properties.pageSetUpPr.fitToPage = True
            else:
                print(f"Warning: Expected sheet {sheet_name} not found in template.")
        
        # Set default active view to Synthese sheet
        try:
            wb.active = wb.sheetnames.index('Synthese_des_donnees')
        except Exception:
            pass
            
        wb.save(output_path)
        
        # 4. Auto-open
        try:
            os.startfile(output_path)
        except Exception:
            pass
            
        return output_path

    @staticmethod
    def _safe_write(ws, r, c, val):
        """Write to cell, ensuring we don't crash on merged sub-cells or formulas"""
        try:
            cell = ws.cell(row=r, column=c)
            if isinstance(cell, openpyxl.cell.cell.MergedCell):
                for range_ in ws.merged_cells.ranges:
                    if cell.coordinate in range_:
                        ws.cell(row=range_.min_row, column=range_.min_col).value = val
                        return
                return
            cell.value = val
        except Exception:
            pass

    @staticmethod
    def _global_metadata_propagation(wb, df: pd.DataFrame, settings: Dict[str, Any]):
        periods = settings.get('periods', [])
        p_vals = []
        for p in periods:
            parts = p.split('-')
            p_vals.append(parts[0].strip() if len(parts) > 0 else '')
            p_vals.append(parts[1].strip() if len(parts) > 1 else '')
        while len(p_vals) < 6: p_vals.append('')

        replacements = {
            "{{LOCATION}}": settings.get('site_name', '--'),
            "{{VMAX}}": settings.get('vmax', 50),
            "{{SECT_INFO}}": settings.get('sect_info', 'Sect: 0000 / Ind: 00 / Count: 0000'),
            "{{P1_START}}": p_vals[0], "{{P1_END}}": p_vals[1],
            "{{P2_START}}": p_vals[2], "{{P2_END}}": p_vals[3],
            "{{P3_START}}": p_vals[4], "{{P3_END}}": p_vals[5]
        }
        
        start_dt = df['timestamp'].min()
        end_dt = df['timestamp'].max()
        replacements["{{SURVEY_PERIOD}}"] = f"du {start_dt.strftime('%d/%m/%Y %H:%M')} au {end_dt.strftime('%d/%m/%Y %H:%M')}"
        
        for ws in wb.worksheets:
            g2 = ws['G2'].value
            if g2 and isinstance(g2, str) and ("MOYENNE" in g2.upper() or g2 == "{{DATE}}"):
                ws['G2'] = "MOYENNE DE LA PERIODE DE RELEVE"

            for row in ws.iter_rows(): 
                for cell in row:
                    if not isinstance(cell.value, str): continue
                    for placeholder, value in replacements.items():
                        if placeholder in cell.value:
                            cell.value = cell.value.replace(placeholder, str(value))

    @staticmethod
    def _populate_synthesis(ws, df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any]):
        vmax = float(settings.get('vmax', 50.0))
        periods = settings.get('periods', [])
        
        # Inject standard directions into the Synthesis grid
        dir_blocks = {'Sens 1': 41, 'Sens 2': 45, 'Total': 49}
        for dir_name, start_row in dir_blocks.items():
            ReportService._inject_summary_block(ws, df, start_row, vmax, periods, metadata, dir_name)
        
        # Clean Footer Labels
        for i, p_str in enumerate(periods):
            row = 53 + i
            times = p_str.split('-')
            ReportService._safe_write(ws, row, 5, times[0] if len(times)>0 else '')
            ReportService._safe_write(ws, row, 7, times[1] if len(times)>1 else '')

    @staticmethod
    def _populate_full_sheet(ws, df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any], direction: str, days: List[date]):
        vmax = float(settings.get('vmax', 50.0))
        periods = settings.get('periods', [])
        
        # Top block (Average)
        ReportService._inject_hourly_grid(ws, df, 11, direction)
        ReportService._inject_summary_block(ws, df, 46, vmax, periods, metadata, direction)
        ReportService._inject_chart_data(ws, df, 0, direction)

        # Subsequent daily blocks 
        block_height = 56
        
        for block_idx in range(1, len(days) + 1):
            target_date = days[block_idx - 1]
            daily_df = df[df['timestamp'].dt.date == target_date]
            
            row_idx = 58 + (block_idx - 1) * block_height
            
            cell = ws[f"G{row_idx}"]
            cell.value = target_date.strftime("%d %B %Y")
            
            ReportService._inject_hourly_grid(ws, daily_df, 11 + (block_idx * block_height), direction)
            ReportService._inject_summary_block(ws, daily_df, 46 + (block_idx * block_height), vmax, periods, metadata, direction)
            ReportService._inject_chart_data(ws, daily_df, block_idx * block_height, direction)
            
        # Hide unused blocks explicitly so they don't print
        max_template_blocks = 31 
        for redundant_idx in range(len(days) + 1, max_template_blocks + 2):
            r_start = 58 + (redundant_idx - 1) * block_height
            if r_start > ws.max_row: break
            for r in range(r_start, r_start + block_height):
                ws.row_dimensions[r].hidden = True

    @staticmethod
    def _inject_chart_data(ws, df: pd.DataFrame, row_offset: int, direction: str):
        """Inject data into the hidden rows/cols that drive the 4 charts"""
        bin_cols = [f"Bin{i+1}" for i in range(12)]
        for i, v_class in enumerate(['VL', 'PL']):
            sub = df[df['vehicle_class'] == v_class] if v_class != 'Total' else df
            if direction != 'Total' and direction != 'mixed':
                sub = sub[sub['direction'] == direction]
            
            counts = [sub[c].sum() for c in bin_cols]
            total = sum(counts) or 1 # Avoid div zero
            
            # Row mapping (based on template audit)
            # VL: 41 (count), 42 (%), 43 (cumul), 44 (cumul %)
            # PL: 45 (count), 46 (%), 47 (cumul), 48 (cumul %)
            base_r = row_offset + (41 if v_class == 'VL' else 45)
            
            cumul = 0
            for b in range(12):
                c = 5 + b # Start Col E
                val = counts[b]
                cumul += val
                
                # Raw Count
                ReportService._safe_write(ws, base_r, c, val)
                # Percent
                ReportService._safe_write(ws, base_r + 1, c, val / total)
                # Cumulative Count
                ReportService._safe_write(ws, base_r + 2, c, cumul)
                # Cumulative Percent
                ReportService._safe_write(ws, base_r + 3, c, cumul / total)

    @staticmethod
    def _inject_hourly_grid(ws, df: pd.DataFrame, start_row: int, direction: str):
        for v_class in ['VL', 'PL']:
            hourly_bins = AnalyticsEngine.compute_hourly_bins(df, direction, v_class)
            base_col = 3 if v_class == "VL" else 4
            for hour in range(24):
                if hour in hourly_bins.index:
                    row_data = hourly_bins.loc[hour]
                    for bin_idx in range(12):
                        ReportService._safe_write(ws, start_row + hour, base_col + (bin_idx * 2), int(row_data[bin_idx]))

    @staticmethod
    def _inject_summary_block(ws, df: pd.DataFrame, start_row: int, vmax: float, periods: List[str], metadata: Dict[str, Any], direction: str):
        centers = metadata.get('speed_bin_centers', [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140])
        bin_cols = [f"Bin{i+1}" for i in range(12)]
        
        is_synthese = 'synthese' in ws.title.lower()
        offsets = [0, 1, 2] if is_synthese else [0, 2, 4]
        
        if is_synthese:
            col_map = {'pct': 10, 'total': 12, 'tmh': 14, 'mean': 16, 'v15': 18, 'v50': 20, 'v85': 22, 'std': 24, 'inf': 26, 'p1': 29}
        else:
            col_map = {'total': 30, 'tmh': 31, 'mean': 32, 'v15': 33, 'v50': 34, 'v85': 35, 'inf': 36, 'p1': 37}

        days = max(1, df['timestamp'].dt.date.nunique())
        duration_hours = max(1.0, (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600 if not df.empty else 1.0)
        grand_total = df['count'].sum() if not df.empty else 1

        for i, v_class in enumerate(['Total', 'VL', 'PL']):
            target_row = start_row + offsets[i]
            sub = df.copy()
            if direction != 'Total' and direction != 'mixed':
                sub = sub[sub['direction'] == direction]
            if v_class != 'Total':
                sub = sub[sub['vehicle_class'] == v_class]
            
            if sub.empty: continue
            
            count = sub['count'].sum()
            metrics = AnalyticsEngine.compute_speed_metrics_for_report([sub[c].sum() for c in bin_cols], centers, vmax)
            
            ReportService._safe_write(ws, target_row, col_map['total'], int(count / days) if is_synthese else int(count))
            ReportService._safe_write(ws, target_row, col_map['tmh'], round(count / duration_hours, 1))
            ReportService._safe_write(ws, target_row, col_map['mean'], round(metrics['mean'], 1))
            ReportService._safe_write(ws, target_row, col_map['v15'], round(metrics['v15'], 1))
            ReportService._safe_write(ws, target_row, col_map['v50'], round(metrics['v50'], 1))
            ReportService._safe_write(ws, target_row, col_map['v85'], round(metrics['v85'], 1))
            ReportService._safe_write(ws, target_row, col_map['inf'], int(metrics['infractions']))
            
            if is_synthese:
                ReportService._safe_write(ws, target_row, col_map['pct'], f"{(count / grand_total * 100):.1f}%")
                ReportService._safe_write(ws, target_row, col_map['std'], round(metrics['std'], 1))
                ReportService._safe_write(ws, target_row, col_map['inf'] + 1, f"{metrics['inf_pct']:.1f}%")

            p_counts = AnalyticsEngine.compute_period_counts(df, direction, v_class, periods)
            for j, p_count in enumerate(p_counts):
                ReportService._safe_write(ws, target_row, col_map['p1'] + j, p_count)
                if not is_synthese:
                    p_pct = (p_count / count * 100) if count > 0 else 0
                    ReportService._safe_write(ws, target_row + 1, col_map['p1'] + j, f"{p_pct:.1f}%")
