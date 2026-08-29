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
    def generate_report(df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any], output_folder: str, auto_open: bool = False) -> str:
        # Determine if velocity data is present
        has_velocity = metadata.get('has_velocity', True)
        bin_cols = [f"Bin{i+1}" for i in range(12)]
        if all(c in df.columns for c in bin_cols):
            if df[bin_cols].sum().sum() == 0:
                has_velocity = False

        if not has_velocity:
            return ReportService._generate_no_velocity_report(df, metadata, settings, output_folder, auto_open=auto_open)

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
        ReportService._global_metadata_propagation(wb, df, metadata, settings)

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
        if auto_open:
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
    def _global_metadata_propagation(wb, df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any]):
        periods = settings.get('periods', [])
        p_vals = []
        for p in periods:
            parts = p.split('-')
            p_vals.append(parts[0].strip() if len(parts) > 0 else '')
            p_vals.append(parts[1].strip() if len(parts) > 1 else '')
        while len(p_vals) < 6: p_vals.append('')

        # Prioritize user manual entry for GPS (including blank values)
        if 'gps_coordinates' in settings:
            gps = settings['gps_coordinates']
        else:
            gps = metadata.get('gps_coordinates', '') if metadata else ''
            
        if gps is None:
            gps = ''

        location_val = settings.get('site_name', '--')
        if gps:
            location_val = f"{location_val} (GPS: {gps})"

        replacements = {
            "{{LOCATION}}": location_val,
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

        # Write GPS and Sens to the top header area of the Synthesis page (Page 1)
        sens = settings.get('sens', '')

        # Unmerge columns L, M, N to merge them into a single wide block for readability
        try:
            ws.unmerge_cells('L3:L4')
            ws.unmerge_cells('M3:M4')
            ws.unmerge_cells('N3:N4')
            ws.merge_cells('L3:P4')
            
            # Ensure text is left-aligned and vertically centered
            from openpyxl.styles import Alignment
            ws['L3'].alignment = Alignment(horizontal='left', vertical='center')
        except Exception:
            pass

        ReportService._safe_write(ws, 3, 11, "Sens:")
        ReportService._safe_write(ws, 3, 12, sens)

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

    @staticmethod
    def _generate_no_velocity_report(df: pd.DataFrame, metadata: Dict[str, Any], settings: Dict[str, Any], output_folder: str, auto_open: bool = False) -> str:
        """
        Generate adapted 3-sheet report layout for traffic datasets without velocity.
        Matches the layout of DataFIMLoader-V3/Format-without-velocity.
        """
        template_path = resource_path("report-template-no-velocity.xlsx")
        output_path = os.path.join(output_folder, f"Rapport_{settings.get('site_name', 'Trafic')}.xlsx")
        shutil.copy2(template_path, output_path)
        
        wb = openpyxl.load_workbook(output_path, keep_links=False)
        
        # 0. Global Cleanup: Kill all external links in charts
        for ws in wb.worksheets:
            if hasattr(ws, '_charts'):
                for chart in ws._charts:
                    if hasattr(chart, 'external_data_source') and chart.external_data_source:
                        chart.external_data_source = None
                        
        days = sorted(df['timestamp'].dt.date.unique())
        start_dt = df['timestamp'].min()
        end_dt = df['timestamp'].max()
        period_str = f"Du {start_dt.strftime('%d/%m/%Y')} au {end_dt.strftime('%d/%m/%Y')}"
        
        # Identify vehicle classes present
        classes = sorted(df['vehicle_class'].unique())
        is_2rm = '2RM' in classes or '2R' in classes
        v_class_1 = '2RM' if is_2rm else 'VL'
        v_class_2 = '2R' if is_2rm else 'PL'
        header_class_str = "(DEBIT 2RM/2R)" if is_2rm else "(DEBIT VL/PL)"
        legend_class_str = "2RM = 2 Roues Motorisées   2R = Cycles" if is_2rm else "VL = Véhicules légers   PL = Poids lourds"
        
        site_name = settings.get('site_name', 'Trafic')
        commune_str = f"COMMUNE DE {site_name}"
        voie_str = settings.get('voie', '') or settings.get('site_name', '')
        point_str = settings.get('sect_info', 'C01')
        
        sens_configs = [
            ('Synthèse Sens1', 'Sens 1', 1, settings.get('sens', 'Sens 1')),
            ('Synthèse Sens2', 'Sens 2', 2, settings.get('sens2_name', 'Sens 2')),
            ('Synthèse Sens3', 'Total', 3, '-')
        ]
        
        for sheet_name, direction, sens_num, direction_label in sens_configs:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            
            # Header Page 1
            ws['F1'] = commune_str
            ws['R1'] = voie_str
            ws['L2'] = point_str
            ws['N2'] = sens_num
            ws['R2'] = direction_label
            ws['F3'] = header_class_str
            ws['R3'] = period_str
            
            # Header Page 2
            ws['F68'] = commune_str
            ws['R68'] = voie_str
            ws['L69'] = point_str
            ws['N69'] = sens_num
            ws['R69'] = direction_label
            ws['F70'] = header_class_str
            ws['R70'] = period_str
            
            # Class labels
            ws['A9'] = v_class_1
            ws['A19'] = v_class_2
            ws['A29'] = '+'
            ws['A64'] = legend_class_str
            ws['D58'] = f"TMJO {v_class_2}"
            ws['H58'] = f"TMJA {v_class_2}"
            
            # Sub-dataset
            if direction == 'Total':
                sub_df = df
            else:
                sub_df = df[df['direction'] == direction]
                if sub_df.empty and 'Sens 1' in df['direction'].unique() and direction == 'Sens 1':
                    sub_df = df
            
            vl_hourly_matrix = []
            pl_hourly_matrix = []
            tv_hourly_matrix = []
            
            # Populate 7 daily rows
            for idx, d in enumerate(days[:7]):
                day_df = sub_df[sub_df['timestamp'].dt.date == d]
                weekday_idx = d.isocalendar()[2] % 7 + 1 # 1=Sun, 2=Mon...
                
                # Class 1 (VL / 2RM)
                c1_df = day_df[day_df['vehicle_class'] == v_class_1]
                c1_hours = [int(c1_df[c1_df['timestamp'].dt.hour == h]['count'].sum()) for h in range(24)]
                c1_tot = sum(c1_hours)
                vl_hourly_matrix.append((d, weekday_idx, c1_hours, c1_tot))
                
                r_c1 = 9 + idx
                ws.cell(r_c1, 2, value=datetime(d.year, d.month, d.day))
                ws.cell(r_c1, 3, value=weekday_idx)
                for h in range(24):
                    ws.cell(r_c1, 4 + h, value=c1_hours[h])
                ws.cell(r_c1, 28, value=c1_tot)
                
                # Class 2 (PL / 2R)
                c2_df = day_df[day_df['vehicle_class'] == v_class_2]
                c2_hours = [int(c2_df[c2_df['timestamp'].dt.hour == h]['count'].sum()) for h in range(24)]
                c2_tot = sum(c2_hours)
                pl_hourly_matrix.append((d, weekday_idx, c2_hours, c2_tot))
                
                r_c2 = 19 + idx
                ws.cell(r_c2, 2, value=datetime(d.year, d.month, d.day))
                ws.cell(r_c2, 3, value=weekday_idx)
                for h in range(24):
                    ws.cell(r_c2, 4 + h, value=c2_hours[h])
                ws.cell(r_c2, 28, value=c2_tot)
                
                # TV
                tv_hours = [c1_hours[h] + c2_hours[h] for h in range(24)]
                tv_tot = c1_tot + c2_tot
                tv_hourly_matrix.append((d, weekday_idx, tv_hours, tv_tot))
                
                r_tv = 29 + idx
                ws.cell(r_tv, 2, value=datetime(d.year, d.month, d.day))
                ws.cell(r_tv, 3, value=weekday_idx)
                for h in range(24):
                    ws.cell(r_tv, 4 + h, value=tv_hours[h])
                ws.cell(r_tv, 28, value=tv_tot)
                
            # If fewer than 7 days, clear remaining template rows
            for empty_idx in range(len(days), 7):
                for base_r in [9 + empty_idx, 19 + empty_idx, 29 + empty_idx]:
                    ws.cell(base_r, 2, value=None)
                    ws.cell(base_r, 3, value=None)
                    for h in range(24):
                        ws.cell(base_r, 4 + h, value=0)
                    ws.cell(base_r, 28, value=0)

            # Averages calculation helper
            def calc_averages(hourly_matrix):
                if not hourly_matrix:
                    return [0]*24, 0, [0]*24, 0
                ouvrable_rows = [row for row in hourly_matrix if row[1] in [2, 3, 4, 5, 6]]
                if not ouvrable_rows: ouvrable_rows = hourly_matrix
                
                tmjo_hours = [sum(row[2][h] for row in ouvrable_rows) / len(ouvrable_rows) for h in range(24)]
                tmjo_tot = sum(row[3] for row in ouvrable_rows) / len(ouvrable_rows)
                
                tmja_hours = [sum(row[2][h] for row in hourly_matrix) / len(hourly_matrix) for h in range(24)]
                tmja_tot = sum(row[3] for row in hourly_matrix) / len(hourly_matrix)
                
                return tmjo_hours, tmjo_tot, tmja_hours, tmja_tot

            c1_tmjo_h, c1_tmjo_t, c1_tmja_h, c1_tmja_t = calc_averages(vl_hourly_matrix)
            c2_tmjo_h, c2_tmjo_t, c2_tmja_h, c2_tmja_t = calc_averages(pl_hourly_matrix)
            tv_tmjo_h, tv_tmjo_t, tv_tmja_h, tv_tmja_t = calc_averages(tv_hourly_matrix)

            # Write TMJO / TMJA rows
            # Class 1
            for h in range(24):
                ws.cell(16, 4 + h, value=round(c1_tmjo_h[h], 1))
                ws.cell(17, 4 + h, value=round(c1_tmja_h[h], 1))
            ws.cell(16, 28, value=round(c1_tmjo_t, 1))
            ws.cell(17, 28, value=round(c1_tmja_t, 1))

            # Class 2
            for h in range(24):
                ws.cell(26, 4 + h, value=round(c2_tmjo_h[h], 1))
                ws.cell(27, 4 + h, value=round(c2_tmja_h[h], 1))
            ws.cell(26, 28, value=round(c2_tmjo_t, 1))
            ws.cell(27, 28, value=round(c2_tmja_t, 1))

            # TV
            for h in range(24):
                ws.cell(36, 4 + h, value=round(tv_tmjo_h[h], 1))
                ws.cell(37, 4 + h, value=round(tv_tmja_h[h], 1))
            ws.cell(36, 28, value=round(tv_tmjo_t, 1))
            ws.cell(37, 28, value=round(tv_tmja_t, 1))

            # KPI summary cards
            ws.cell(55, 4, value=round(tv_tmjo_t, 1))
            ws.cell(55, 8, value=round(tv_tmja_t, 1))
            ws.cell(59, 4, value=round(c2_tmjo_t, 1))
            ws.cell(59, 8, value=round(c2_tmja_t, 1))
            
            pct_tmjo = (c2_tmjo_t / tv_tmjo_t) if tv_tmjo_t > 0 else 0
            pct_tmja = (c2_tmja_t / tv_tmja_t) if tv_tmja_t > 0 else 0
            ws.cell(61, 4, value=pct_tmjo)
            ws.cell(61, 8, value=pct_tmja)
            
        try:
            wb.active = wb.sheetnames.index('Synthèse Sens1')
        except Exception:
            pass
            
        wb.save(output_path)
        if auto_open:
            try:
                os.startfile(output_path)
            except Exception:
                pass
            
        return output_path
