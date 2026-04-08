"""
FIM File Loader with Metadata Display
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QGridLayout, QMessageBox, QComboBox, QDialog,
    QDateTimeEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
import sys
import os
import statistics
import csv

from typing import List
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator, NullFormatter
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import holidays
from PIL import Image
import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def resource_path(*parts: str) -> str:
    base_dirs = [os.path.dirname(__file__)]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base_dirs.append(meipass)
        base_dirs.append(os.path.join(meipass, "src", "ui"))
    for base_dir in base_dirs:
        candidate = os.path.join(base_dir, *parts)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(base_dirs[0], *parts)

# Ensure project src directory is on path for imports
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Add parent directory for module imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.fim_parser import parse_fim_file
except ImportError:
    # Try alternative import path for PyInstaller bundled executable
    try:
        from src.core.fim_parser import parse_fim_file
    except ImportError:
        from dcr_python.src.core.fim_parser import parse_fim_file



class MetadataPanel(QWidget):
    def _find_busiest_days(self, df):
        # Export-related logic removed; keep safe defaults.
        return {}, {}
    def init_ui(self):
        layout = QVBoxLayout()

        # Add file operation buttons at the top
        # ...existing code...
        # ...existing code...
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Charger un fichier FIM", os.path.expanduser("~/Documents"), "Fichiers FIM (*.fim);;Tous les fichiers (*)")
        if file_path:
            self.file_label.setText(os.path.basename(file_path))
            try:
                df, metadata = parse_fim_file(file_path)
                # Compute and set expected metadata fields
                if df is not None and metadata is not None:
                    # Start datetime
                    from datetime import datetime, timedelta
                    import locale
                    # Set locale to French for day names
                    try:
                        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
                    except locale.Error:
                        # Windows fallback
                        locale.setlocale(locale.LC_TIME, 'French')
                    start = datetime(metadata.get('year', 2000), metadata.get('month', 1), metadata.get('day', 1), metadata.get('start_hour', 0), metadata.get('start_minute', 0))
                    start_dt = start.strftime('%A, %d-%m-%Y %H:%M')
                    metadata['start_datetime'] = start_dt
                    # End datetime
                    interval = metadata.get('interval_minutes', 1)
                    n = len(metadata.get('raw_data', []))
                    end = start + timedelta(minutes=interval * (n - 1))
                    end_dt = end.strftime('%A, %d-%m-%Y %H:%M')
                    metadata['end_datetime'] = end_dt
                    # Frequency
                    metadata['frequency'] = metadata.get('interval_minutes', '--')
                    # TMJ VL/PL (average daily count per class)
                    if df is not None and not df.empty:
                        df['date_only'] = df['timestamp'].dt.date
                        vl_avg = df[df['vehicle_class'] == 'VL'].groupby(['direction', 'date_only'])['count'].sum().groupby('direction').mean().to_dict()
                        pl_avg = df[df['vehicle_class'] == 'PL'].groupby(['direction', 'date_only'])['count'].sum().groupby('direction').mean().to_dict()
                        metadata['tmj_vl_sens1'] = int(vl_avg.get('Sens 1', 0)) if vl_avg else '--'
                        metadata['tmj_vl_sens2'] = int(vl_avg.get('Sens 2', 0)) if vl_avg else '--'
                        metadata['tmj_pl_sens1'] = int(pl_avg.get('Sens 1', 0)) if pl_avg else '--'
                        metadata['tmj_pl_sens2'] = int(pl_avg.get('Sens 2', 0)) if pl_avg else '--'
                        # Mean speed (weighted by speed bins, averaged across directions)
                        speed_centers = metadata.get('speed_bin_centers', [])
                        bin_cols = [c for c in df.columns if c.startswith('Bin')]

                        def _sorted_bins(cols):
                            def _bin_key(name):
                                try:
                                    return int(name.replace('Bin', ''))
                                except ValueError:
                                    return 0
                            return sorted(cols, key=_bin_key)

                        def _row_mean_speeds(vehicle_class, direction):
                            if not speed_centers or not bin_cols:
                                return []
                            bins = _sorted_bins(bin_cols)
                            sub = df[(df['vehicle_class'] == vehicle_class) & (df['direction'] == direction)]
                            if sub.empty:
                                return []
                            max_len = min(len(speed_centers), len(bins))
                            means = []
                            for _, row in sub[bins].iterrows():
                                counts = row.iloc[:max_len]
                                total = counts.sum()
                                if total > 0:
                                    num = sum(counts.iloc[i] * speed_centers[i] for i in range(max_len))
                                    means.append(num / total)
                            return means

                        vl_s1 = _row_mean_speeds('VL', 'Sens 1')
                        vl_s2 = _row_mean_speeds('VL', 'Sens 2')
                        pl_s1 = _row_mean_speeds('PL', 'Sens 1')
                        pl_s2 = _row_mean_speeds('PL', 'Sens 2')

                        if vl_s1:
                            vl_mean = sum(vl_s1) / len(vl_s1)
                            vl_median = statistics.median(vl_s1)
                            metadata['mean_speed_vl_sens1'] = f"{vl_mean:.1f} / {vl_median:.1f} km/h"
                        else:
                            metadata['mean_speed_vl_sens1'] = '--'

                        if vl_s2:
                            vl_mean = sum(vl_s2) / len(vl_s2)
                            vl_median = statistics.median(vl_s2)
                            metadata['mean_speed_vl_sens2'] = f"{vl_mean:.1f} / {vl_median:.1f} km/h"
                        else:
                            metadata['mean_speed_vl_sens2'] = '--'

                        if pl_s1:
                            pl_mean = sum(pl_s1) / len(pl_s1)
                            pl_median = statistics.median(pl_s1)
                            metadata['mean_speed_pl_sens1'] = f"{pl_mean:.1f} / {pl_median:.1f} km/h"
                        else:
                            metadata['mean_speed_pl_sens1'] = '--'

                        if pl_s2:
                            pl_mean = sum(pl_s2) / len(pl_s2)
                            pl_median = statistics.median(pl_s2)
                            metadata['mean_speed_pl_sens2'] = f"{pl_mean:.1f} / {pl_median:.1f} km/h"
                        else:
                            metadata['mean_speed_pl_sens2'] = '--'
                        # Directions
                        metadata['directions'] = ', '.join(df['direction'].unique())
                        # Vehicle classes
                        metadata['vehicle_classes'] = ', '.join(df['vehicle_class'].unique())
                        # Speed measurement
                        metadata['speed_measurement'] = 'Oui' if 'speed_bin_centers' in metadata else 'Non'
                        # Busiest days
                        import locale
                        try:
                            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
                        except locale.Error:
                            locale.setlocale(locale.LC_TIME, 'French')
                        def busiest_day(df, vehicle_class, direction):
                            sub = df[(df['vehicle_class'] == vehicle_class) & (df['direction'] == direction)]
                            if not sub.empty:
                                day = sub.groupby('date_only')['count'].sum().idxmax()
                                count = sub.groupby('date_only')['count'].sum().max()
                                # Add French day of week
                                try:
                                    from datetime import datetime
                                    day_dt = datetime.strptime(str(day), '%Y-%m-%d')
                                    day_name = day_dt.strftime('%A')
                                except Exception:
                                    day_name = ''
                                return f"{day_name}, {day} ({count})"
                            return '--'
                        metadata['busiest_vl_sens1'] = busiest_day(df, 'VL', 'Sens 1')
                        metadata['busiest_vl_sens2'] = busiest_day(df, 'VL', 'Sens 2')
                        metadata['busiest_pl_sens1'] = busiest_day(df, 'PL', 'Sens 1')
                        metadata['busiest_pl_sens2'] = busiest_day(df, 'PL', 'Sens 2')
                    self.current_df = df
                    self.current_metadata = metadata
                    # Update metadata fields
                    for label, (key, widget) in self.metadata_fields.items():
                        value = metadata.get(key, '--')
                        widget.setText(str(value))
                else:
                    for label, (key, widget) in self.metadata_fields.items():
                        widget.setText('--')
            except Exception as e:
                QMessageBox.critical(self, "Erreur de chargement", f"Impossible de charger le fichier:\n{str(e)}")
                for label, (key, widget) in self.metadata_fields.items():
                    widget.setText('--')
        else:
            self.file_label.setText("Aucun fichier chargé")
            for label, (key, widget) in self.metadata_fields.items():
                widget.setText('--')

        # Only update widgets and metadata fields, not layout
    def __init__(self, parent=None):
        super().__init__(parent)
        self.metadata_fields = {
            'Date/Heure de début': ('start_datetime', QLabel('--')),
            'Date/Heure de fin': ('end_datetime', QLabel('--')),
            'TMJ VL Sens 1': ('tmj_vl_sens1', QLabel('--')),
            'TMJ VL Sens 2': ('tmj_vl_sens2', QLabel('--')),
            'TMJ PL Sens 1': ('tmj_pl_sens1', QLabel('--')),
            'TMJ PL Sens 2': ('tmj_pl_sens2', QLabel('--')),
            'Vitesse moyenne / median VL Sens 1': ('mean_speed_vl_sens1', QLabel('--')),
            'Vitesse moyenne / median VL Sens 2': ('mean_speed_vl_sens2', QLabel('--')),
            'Vitesse moyenne / median PL Sens 1': ('mean_speed_pl_sens1', QLabel('--')),
            'Vitesse moyenne / median PL Sens 2': ('mean_speed_pl_sens2', QLabel('--')),
            'Jour le plus chargé en VL Sens 1': ('busiest_vl_sens1', QLabel('--')),
            'Jour le plus chargé en VL Sens 2': ('busiest_vl_sens2', QLabel('--')),
            'Jour le plus chargé en PL Sens 1': ('busiest_pl_sens1', QLabel('--')),
            'Jour le plus chargé en PL Sens 2': ('busiest_pl_sens2', QLabel('--')),
        }
        self.init_ui()
        # Signal connection handled in init_ui after button creation
        # ...existing code...

        # Logo at the bottom right
        from PyQt5.QtGui import QPixmap
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("logo.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaledToHeight(192, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        # ...existing code...

        # Add logo at the end, bottom right
        logo_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # File selection row at top
        file_layout = QHBoxLayout()
        file_btn_label = QLabel("Fichier:")
        file_btn_label.setFont(QFont("Segoe UI", 11))
        self.file_label = QLabel("Aucun fichier chargé")
        self.file_label.setFont(QFont("Segoe UI", 11))
        self.file_label.setStyleSheet("color: #0066cc;")
        self.load_button = QPushButton("Charger fichier FIM")
        self.load_button.setFont(QFont("Segoe UI", 11))
        self.load_button.setStyleSheet("QPushButton { background-color: #0066cc; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #0052a3; }")
        self.load_button.clicked.connect(self.load_file)
        self.extract_button = QPushButton("Extraire données")
        self.extract_button.setFont(QFont("Segoe UI", 11))
        self.extract_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
        self.extract_button.clicked.connect(self.extract_data)
        self.report_button = QPushButton("Générer des rapports")
        self.report_button.setFont(QFont("Segoe UI", 11))
        self.report_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
        self.report_button.clicked.connect(self.generate_reports)
        # ...existing code...
        file_layout.addWidget(file_btn_label)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.load_button)
        file_layout.addWidget(self.extract_button)
        file_layout.addWidget(self.report_button)
        layout.addLayout(file_layout)

        # Metadata group immediately below
        metadata_group = QGroupBox("Métadonnées")
        metadata_layout = QGridLayout()
        # ...existing code for metadata fields...

        # Set placeholder color for all metadata field values
        for field_key, (_, label_widget) in self.metadata_fields.items():
            label_widget.setStyleSheet("color: #0066cc;")

        row = 0
        for label_text, (field_key, label_widget) in self.metadata_fields.items():
            label_widget.setFont(QFont("Segoe UI", 11))
            label_key = QLabel(label_text + ":")
            label_key.setFont(QFont("Segoe UI", 11))
            metadata_layout.addWidget(label_key, row, 0)
            metadata_layout.addWidget(label_widget, row, 1)
            row += 1

        # Add logo to bottom right of metadata group
        from PyQt5.QtGui import QPixmap
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("logo.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaledToHeight(96, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        metadata_layout.addWidget(logo_label, row, 1, alignment=Qt.AlignRight | Qt.AlignBottom)

        # Add copyright label at bottom center
        copyright_label = QLabel("© Data Ferns 2026")
        copyright_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        copyright_label.setAlignment(Qt.AlignCenter)
        metadata_layout.addWidget(copyright_label, row + 1, 0, 1, 2, alignment=Qt.AlignCenter)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Per-direction panel (Sens 1 / Sens 2)
        direction_group = QGroupBox("Par Direction (moyennes journalières)")
        direction_layout = QGridLayout()

        header_blank = QLabel("")
        header_blank.setFont(QFont("Segoe UI", 11))
        direction_layout.addWidget(header_blank, 0, 0)
        header_sens1 = QLabel("Sens 1")
        header_sens1.setFont(QFont("Segoe UI", 11))
        direction_layout.addWidget(header_sens1, 0, 1)
        header_sens2 = QLabel("Sens 2")
        header_sens2.setFont(QFont("Segoe UI", 11))
        direction_layout.addWidget(header_sens2, 0, 2)

        self.direction_fields = {
            'tmj_vl': {'Sens 1': QLabel('--'), 'Sens 2': QLabel('--')},
            'tmj_pl': {'Sens 1': QLabel('--'), 'Sens 2': QLabel('--')},
            'busiest_pl': {'Sens 1': QLabel('--'), 'Sens 2': QLabel('--')},
        }

        # Set the layout for the widget
        self.setLayout(layout)

    def _set_dir_row(self, row_fields: dict, values: dict, speed: bool = False, blank_if_none: bool = False):
        for label, widget in row_fields.items():
            val = values.get(label)
            if val is None and blank_if_none:
                widget.setText("")
            else:
                # If value is already a string (like busiest day), use it directly
                if isinstance(val, str):
                    widget.setText(val)
                else:
                    widget.setText(self._fmt_speed(val) if speed else self._fmt_number(val))

    @staticmethod
    def _remove_outliers(df):
        """
        Remove outliers from traffic count data using IQR method.
        Calculates separate thresholds for each direction and vehicle class combination.
        Replaces outlier values with 0.
        """
        if df is None or df.empty or 'count' not in df.columns:
            return df
        
        df = df.copy()
        
        # Check if we have direction and vehicle_class columns
        has_direction = 'direction' in df.columns
        has_vehicle_class = 'vehicle_class' in df.columns
        
        if not has_direction and not has_vehicle_class:
            # Fallback to global threshold
            median = df['count'].median()
            q1 = df['count'].quantile(0.25)
            q3 = df['count'].quantile(0.75)
            iqr = q3 - q1
            threshold_iqr = q3 + 13 * iqr
            threshold_median = median * 10 if median > 0 else 0
            threshold = max(threshold_iqr, threshold_median)
            
            outlier_mask = df['count'] > threshold
            num_outliers = outlier_mask.sum()
            if num_outliers > 0:
                df.loc[outlier_mask, 'count'] = 0
                print(f"Removed {num_outliers} outlier values (threshold: {threshold:.1f})")
            return df
        
        # Group by direction and vehicle class to calculate separate thresholds
        group_cols = []
        if has_direction:
            group_cols.append('direction')
        if has_vehicle_class:
            group_cols.append('vehicle_class')
        
        total_outliers = 0
        
        for group_key, group_df in df.groupby(group_cols):
            if len(group_df) == 0:
                continue
            
            # Calculate statistics for this group
            counts = group_df['count']
            median = counts.median()
            q1 = counts.quantile(0.25)
            q3 = counts.quantile(0.75)
            iqr = q3 - q1
            
            # Determine vehicle class for this group
            vehicle_class = None
            if has_vehicle_class:
                vehicle_class = group_key[1] if isinstance(group_key, tuple) and len(group_key) > 1 else group_key
            
            # Define outlier threshold using two methods and take the maximum
            # Method 1: Q3 + N × IQR where N=5 for VL, N=7 for PL
            # Method 2: 10 × median
            if vehicle_class == 'VL':
                threshold_iqr = q3 + 5 * iqr  # VL: Q3 + 5 × IQR
            else:
                threshold_iqr = q3 + 7 * iqr  # PL: Q3 + 7 × IQR
            
            threshold_median = median * 10 if median > 0 else 0
            
            # Use the more lenient (larger) of the two thresholds
            threshold = max(threshold_iqr, threshold_median)
            
            # Find outliers in this group
            group_indices = group_df.index
            outlier_mask = df.loc[group_indices, 'count'] > threshold
            num_outliers = outlier_mask.sum()
            
            if num_outliers > 0:
                df.loc[group_indices[outlier_mask], 'count'] = 0
                total_outliers += num_outliers
                group_label = ' - '.join([str(g) for g in (group_key if isinstance(group_key, tuple) else [group_key])])
                print(f"  {group_label}: Removed {num_outliers} outliers (threshold: {threshold:.1f})")
        
        if total_outliers > 0:
            print(f"Total outliers removed: {total_outliers}")
        
        return df

    @staticmethod
    def _looks_like_speed_bins(bins: List[int]) -> bool:
        """Heuristic: true if bins are monotonic increasing and cover speed-like range."""
        if len(bins) < 4:
            return False
        if any(b < 0 for b in bins):
            return False
        is_monotonic = all(bins[i] <= bins[i+1] for i in range(len(bins)-1))
        return is_monotonic and max(bins) >= 80

    @staticmethod
    def _fmt_number(val: float) -> str:
        return f"{val:.1f}" if val is not None else "--"

    @staticmethod
    def _fmt_speed(val: float) -> str:
        return f"{val:.1f} km/h" if val is not None else "--"

    @staticmethod
    def _fmt_dir_dict(d: dict, speed: bool = False, combine_to_two: bool = False) -> str:
        if not d:
            return "--"
        row = 0
        for label_text, (field_key, label_widget) in self.metadata_fields.items():
            label_widget.setFont(QFont("Segoe UI", 11))
            label_key = QLabel(label_text + ":")
            label_key.setFont(QFont("Segoe UI", 11))
            metadata_layout.addWidget(label_key, row, 0)
            metadata_layout.addWidget(label_widget, row, 1)
            row += 1

        # Add logo to bottom right of metadata group
        from PyQt5.QtGui import QPixmap
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("logo.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaledToHeight(48, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        metadata_layout.addWidget(logo_label, row, 1, alignment=Qt.AlignRight | Qt.AlignBottom)
        df = df.copy()
        df['date_only'] = df['timestamp'].dt.date
        table = df.pivot_table(index=['direction', 'date_only'], columns='vehicle_class', values='count', aggfunc='sum', fill_value=0)
        vl_dir = table['VL'].groupby(level=0).mean() if 'VL' in table else pd.Series(dtype=float)
        pl_dir = table['PL'].groupby(level=0).mean() if 'PL' in table else pd.Series(dtype=float)
        return vl_dir.to_dict(), pl_dir.to_dict()

    def _compute_busiest_day_by_direction(self, df):
        """Find the busiest day (highest traffic) for VL and PL per direction
        Returns: (vl_busiest_dict, pl_busiest_dict) where values are formatted strings like 'Mardi, 18 Nov 2024 (1234)'
        """
        if df.empty or 'timestamp' not in df:
            return {}, {}
        
        df = df.copy()
        df['date_only'] = df['timestamp'].dt.date
        
        # Get daily totals by direction and vehicle class
        daily_totals = df.groupby(['direction', 'date_only', 'vehicle_class'])['count'].sum().reset_index()
        
        # French day names and month abbreviations
        day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        month_abbr_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        
        vl_busiest = {}
        pl_busiest = {}
        
        for direction in daily_totals['direction'].unique():
            dir_data = daily_totals[daily_totals['direction'] == direction]
            
            # VL busiest day
            vl_data = dir_data[dir_data['vehicle_class'] == 'VL']
            if not vl_data.empty:
                busiest_vl_row = vl_data.loc[vl_data['count'].idxmax()]
                busiest_date = busiest_vl_row['date_only']
                vehicle_count = int(busiest_vl_row['count'])
                day_of_week = day_names_fr[busiest_date.weekday()]
                month_abbr = month_abbr_fr[busiest_date.month - 1]
                vl_busiest[direction] = f"{day_of_week}, {busiest_date.day} {month_abbr} {busiest_date.year} ({vehicle_count})"
            
            # PL busiest day
            pl_data = dir_data[dir_data['vehicle_class'] == 'PL']
            if not pl_data.empty:
                busiest_pl_row = pl_data.loc[pl_data['count'].idxmax()]
                busiest_date = busiest_pl_row['date_only']
                vehicle_count = int(busiest_pl_row['count'])
                day_of_week = day_names_fr[busiest_date.weekday()]
                month_abbr = month_abbr_fr[busiest_date.month - 1]
                pl_busiest[direction] = f"{day_of_week}, {busiest_date.day} {month_abbr} {busiest_date.year} ({vehicle_count})"
        
        return vl_busiest, pl_busiest

    def _compute_daily_speed_by_direction(self, meta):
        bins = meta.get('speed_bins', [])
        raw = meta.get('raw_data', [])
        rows_per_block = meta.get('rows_per_block', 0)
        num_sensors = meta.get('num_sensors', 0)
        freq = meta.get('interval_minutes', 60)
        sensor_map = meta.get('sensor_map', {})
        try:
            start_dt = datetime(meta['year'], meta['month'], meta['day'], meta['start_hour'], meta['start_minute'])
        except Exception:
            return {}, {}

        if len(bins) < 4 or not raw or rows_per_block == 0 or num_sensors == 0:
            return {}, {}

        dir_vl_num = {}
        dir_vl_den = {}
        dir_pl_num = {}
        dir_pl_den = {}

        for sensor_id in range(num_sensors):
            sensor_info = sensor_map.get(sensor_id, {'direction': f'Sensor {sensor_id + 1}', 'class': 'ALL'})
            direction = sensor_info['direction']
            vehicle_class = sensor_info['class']

            if direction not in dir_vl_num:
                dir_vl_num[direction] = {}
                dir_vl_den[direction] = {}
                dir_pl_num[direction] = {}
                dir_pl_den[direction] = {}

            start_row = sensor_id * rows_per_block
            end_row = min(start_row + rows_per_block, len(raw))
            block = raw[start_row:end_row]

            for idx, row_vals in enumerate(block):
                ts = start_dt + timedelta(minutes=freq * idx)
                d = ts.date()

                counts = [row_vals[i] for i in range(min(12, len(row_vals))) if i < len(bins)]
                speed_num = sum(counts[i] * bins[i] for i in range(min(len(counts), len(bins))))
                speed_den = sum(counts)

                if speed_den > 0:
                    if vehicle_class == 'VL' or vehicle_class == 'ALL':
                        dir_vl_num[direction][d] = dir_vl_num[direction].get(d, 0) + speed_num
                        dir_vl_den[direction][d] = dir_vl_den[direction].get(d, 0) + speed_den
                    if vehicle_class == 'PL':
                        dir_pl_num[direction][d] = dir_pl_num[direction].get(d, 0) + speed_num
                        dir_pl_den[direction][d] = dir_pl_den[direction].get(d, 0) + speed_den

        def avg_by_dir(dir_num_map, dir_den_map):
            out = {}
            for direction in dir_num_map:
                vals = []
                for d in dir_num_map[direction]:
                    if dir_den_map[direction].get(d, 0) > 0:
                        vals.append(dir_num_map[direction][d] / dir_den_map[direction][d])
                if vals:
                    out[direction] = sum(vals) / len(vals)
            return out

        return avg_by_dir(dir_vl_num, dir_vl_den), avg_by_dir(dir_pl_num, dir_pl_den)

    def export_data(self):
        # Export functionality removed.
        pass

    def extract_data(self):
        values = [(label, widget.text()) for label, (_, widget) in self.metadata_fields.items()]
        has_data = any(val not in ('--', '') for _, val in values)
        if not has_data:
            QMessageBox.warning(self, "Attention", "Aucune metadata a extraire")
            return

        if getattr(self, 'current_df', None) is None:
            QMessageBox.warning(self, "Attention", "Aucune donnee chargee")
            return

        folder = QFileDialog.getExistingDirectory(self, "Selectionner un dossier", os.path.expanduser("~/Documents"))
        if not folder:
            return

        file_path = os.path.join(folder, "Données_brut.xlsx")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            df_meta = pd.DataFrame(values, columns=["Champ", "Valeur"])

            df = self.current_df.copy()
            df['Date'] = df['timestamp'].dt.strftime('%d/%m/%Y')
            df['Heure'] = df['timestamp'].dt.strftime('%H:%M')

            def build_comptages(direction_label):
                df_dir = df[df['direction'] == direction_label]
                vl_counts = df_dir[df_dir['vehicle_class'] == 'VL'].groupby(['Date', 'Heure'])['count'].sum()
                pl_counts = df_dir[df_dir['vehicle_class'] == 'PL'].groupby(['Date', 'Heure'])['count'].sum()
                all_keys = sorted(set(vl_counts.index) | set(pl_counts.index))

                comptages_rows = []
                for date, heure in all_keys:
                    vl = int(vl_counts.get((date, heure), 0))
                    pl = int(pl_counts.get((date, heure), 0))
                    tv = vl + pl
                    comptages_rows.append([date, heure, vl, pl, tv])

                return pd.DataFrame(comptages_rows, columns=['Date', 'Heure', 'VL', 'PL', 'TV'])

            df_comptages_s1 = build_comptages('Sens 1')
            df_comptages_s2 = build_comptages('Sens 2')

            bin_cols = [f"Bin{i+1}" for i in range(12)]
            for col in bin_cols:
                if col not in df.columns:
                    df[col] = 0

            speed_centers = self.current_metadata.get('speed_bin_centers', [])
            if not speed_centers:
                speed_centers = [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]

            def compute_vmoy(row):
                total = sum(row[col] for col in bin_cols)
                if total <= 0:
                    return 0.0
                return sum(row[bin_cols[i]] * speed_centers[i] for i in range(len(bin_cols))) / total

            def build_vitesse(direction_label, vehicle_class_label):
                df_vitesse = df[(df['direction'] == direction_label) & (df['vehicle_class'] == vehicle_class_label)].copy()
                grouped = df_vitesse.groupby(['Date', 'Heure'])[bin_cols].sum().reset_index()
                if grouped.empty:
                    return grouped
                grouped['Vmoy'] = grouped.apply(compute_vmoy, axis=1)
                grouped['Débit'] = grouped[bin_cols].sum(axis=1)
                grouped['Vmoy'] = grouped['Vmoy'].round(1)
                return grouped[['Date', 'Heure'] + bin_cols + ['Vmoy', 'Débit']]

            vitesse_s1_vl = build_vitesse('Sens 1', 'VL')
            vitesse_s2_vl = build_vitesse('Sens 2', 'VL')
            vitesse_s1_pl = build_vitesse('Sens 1', 'PL')
            vitesse_s2_pl = build_vitesse('Sens 2', 'PL')

            with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
                df_meta.to_excel(writer, sheet_name='Métadonnées', index=False)
                df_comptages_s1.to_excel(writer, sheet_name='Comptages Sens 1', index=False)
                df_comptages_s2.to_excel(writer, sheet_name='Comptages Sens 2', index=False)
                if not vitesse_s1_vl.empty:
                    vitesse_s1_vl.to_excel(writer, sheet_name='Vitesse Sens 1 VL', index=False)
                if not vitesse_s2_vl.empty:
                    vitesse_s2_vl.to_excel(writer, sheet_name='Vitesse Sens 2 VL', index=False)
                if not vitesse_s1_pl.empty:
                    vitesse_s1_pl.to_excel(writer, sheet_name='Vitesse Sens 1 PL', index=False)
                if not vitesse_s2_pl.empty:
                    vitesse_s2_pl.to_excel(writer, sheet_name='Vitesse Sens 2 PL', index=False)

            QMessageBox.information(self, "Succes", f"Donnees extraites avec succes:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'extraction:\n{str(exc)}")

    def generate_reports(self):
        if getattr(self, 'current_df', None) is None:
            QMessageBox.warning(self, "Attention", "Aucune donnee chargee")
            return

        df = self.current_df.copy()
        if df.empty or 'timestamp' not in df.columns:
            QMessageBox.warning(self, "Attention", "Aucune donnee disponible pour les rapports")
            return

        folder = QFileDialog.getExistingDirectory(self, "Selectionner un dossier", os.path.expanduser("~/Documents"))
        if not folder:
            return

        df['date_only'] = df['timestamp'].dt.date
        unique_dates = sorted(df['date_only'].dropna().unique())
        if not unique_dates:
            QMessageBox.warning(self, "Attention", "Aucune date valide trouvee dans les donnees")
            return

        try:
            logo_path = resource_path("logo-NC.png")
            street, ok = QInputDialog.getText(self, "Rue enquete?", "Rue enquete?")
            if not ok:
                return
            street = street.strip() or "--"

            client, ok = QInputDialog.getText(self, "Client", "Client")
            if not ok:
                return
            client = client.strip() or "--"

            vmax, ok = QInputDialog.getInt(
                self,
                "VITESSE MAXIMALE AUTORISEE",
                "VITESSE MAXIMALE AUTORISEE (km/h)",
                value=50,
                min=1,
                max=200
            )
            if not ok:
                return

            period_defaults = ["07:00-09:00", "12:00-14:00", "17:00-19:00"]
            period_ranges = []
            for idx in range(3):
                period_text, ok = QInputDialog.getText(
                    self,
                    f"Periode {idx + 1}",
                    f"Periode {idx + 1} (HH:MM-HH:MM)",
                    text=period_defaults[idx]
                )
                if not ok:
                    return
                period_ranges.append(period_text.strip())

            period_ranges = (period_ranges + ['--', '--', '--'])[:3]

            start_dt = self.current_metadata.get('start_datetime') if self.current_metadata else None
            end_dt = self.current_metadata.get('end_datetime') if self.current_metadata else None
            if not start_dt or not end_dt:
                min_ts = df['timestamp'].min()
                max_ts = df['timestamp'].max()
                start_dt = min_ts.strftime('%A %d/%m/%Y %H:%M') if pd.notna(min_ts) else "--"
                end_dt = max_ts.strftime('%A %d/%m/%Y %H:%M') if pd.notna(max_ts) else "--"

            def add_header_logo(doc_obj):
                if not os.path.exists(logo_path):
                    return
                section = doc_obj.sections[0]
                section.header_distance = int(section.header_distance * 0.9)
                section.footer_distance = int(section.footer_distance * 0.9)
                header = section.header
                paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                header_width = section.page_width - section.left_margin - section.right_margin
                table = header.add_table(rows=1, cols=2, width=header_width)
                table.autofit = True
                left_width = int(header_width * 0.3)
                right_width = int(header_width * 0.7)
                logo_cell = table.cell(0, 0)
                logo_cell.width = left_width
                logo_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                logo_cell_par = logo_cell.paragraphs[0]
                logo_cell_par.alignment = WD_ALIGN_PARAGRAPH.LEFT
                logo_cell_par.add_run().add_picture(logo_path, width=Mm(22.5))

                text_cell = table.cell(0, 1)
                text_cell.width = right_width
                text_par = text_cell.paragraphs[0]
                text_par.alignment = WD_ALIGN_PARAGRAPH.LEFT
                text_run = text_par.add_run(f"Localisation : {street}")
                text_run.font.size = Pt(12)
                text_run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)
                text_par.add_run().add_break()
                date_run = text_par.add_run(f"Date debut/fin : {start_dt} - {end_dt}")
                date_run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)
                text_par.add_run().add_break()
                client_run = text_par.add_run(f"Client : {client}")
                client_run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)

            def add_footer_page_number(doc_obj):
                footer = doc_obj.sections[0].footer
                paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
                paragraph.text = ""

                section = doc_obj.sections[0]
                footer_width = section.page_width - section.left_margin - section.right_margin
                table = footer.add_table(rows=1, cols=2, width=footer_width)
                table.autofit = True

                left_cell = table.cell(0, 0)
                left_par = left_cell.paragraphs[0]
                left_par.alignment = WD_ALIGN_PARAGRAPH.LEFT
                left_run = left_par.add_run('nordcomptageroutier@gmail.com')
                left_run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)
                left_par.add_run().add_break()
                link_run = left_par.add_run('https://nordcomptageroutier.fr/')
                link_run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)

                right_cell = table.cell(0, 1)
                right_par = right_cell.paragraphs[0]
                right_par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = right_par.add_run()
                run.font.color.rgb = RGBColor(0x8C, 0xC7, 0x40)
                fld_simple = OxmlElement('w:fldSimple')
                fld_simple.set(qn('w:instr'), 'PAGE')
                run._r.append(fld_simple)

            def parse_period(period_text):
                try:
                    start_str, end_str = period_text.split('-')
                    start_time = datetime.strptime(start_str.strip(), '%H:%M').time()
                    end_time = datetime.strptime(end_str.strip(), '%H:%M').time()
                    return start_time, end_time
                except Exception:
                    return None

            parsed_periods = []
            for period_text in period_ranges:
                parsed = parse_period(period_text)
                if not parsed:
                    QMessageBox.warning(self, "Attention", f"Periode invalide: {period_text}")
                    return
                parsed_periods.append(parsed)

            parsed_periods = (parsed_periods + [(datetime.min.time(), datetime.min.time())] * 3)[:3]

            def percentile_from_bins(counts, centers, pct):
                total = sum(counts)
                if total <= 0:
                    return 0.0
                target = total * pct
                running = 0
                for idx, count in enumerate(counts):
                    running += count
                    if running >= target:
                        return float(centers[idx])
                return float(centers[-1])

            def mean_std_from_bins(counts, centers):
                total = sum(counts)
                if total <= 0:
                    return 0.0, 0.0
                mean = sum(counts[i] * centers[i] for i in range(len(counts))) / total
                var = sum(counts[i] * ((centers[i] - mean) ** 2) for i in range(len(counts))) / total
                return mean, var ** 0.5

            def infractions_from_bins(counts, centers, max_speed):
                total = sum(counts)
                if total <= 0:
                    return 0, 0.0
                inf = sum(counts[i] for i in range(len(counts)) if centers[i] > max_speed)
                return int(inf), (inf / total * 100)

            def get_period_count(df_src, start_time, end_time):
                if df_src.empty:
                    return 0
                ts = df_src['timestamp']
                mask = (ts.dt.time >= start_time) & (ts.dt.time <= end_time)
                return int(df_src[mask]['count'].sum())

            def set_cell_shading(cell, color_hex):
                tc_pr = cell._tc.get_or_add_tcPr()
                shading = OxmlElement('w:shd')
                shading.set(qn('w:fill'), color_hex)
                tc_pr.append(shading)

            def set_vmerge(cell, merge_val):
                tc_pr = cell._tc.get_or_add_tcPr()
                vmerge = tc_pr.find(qn('w:vMerge'))
                if vmerge is None:
                    vmerge = OxmlElement('w:vMerge')
                    tc_pr.append(vmerge)
                vmerge.set(qn('w:val'), merge_val)

            def build_summary_section(doc_obj, df_scope, title_text, use_daily_averages=False):
                doc_obj.add_heading(title_text, level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
                #doc_obj.add_paragraph(f"Fichier: {self.file_label.text()}")

                bin_cols = [f"Bin{i+1}" for i in range(12)]
                for col in bin_cols:
                    if col not in df_scope.columns:
                        df_scope[col] = 0

                speed_centers = self.current_metadata.get('speed_bin_centers', [])
                if not speed_centers:
                    speed_centers = [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]

                def _daily_metrics(df_input):
                    daily_rows = []
                    for _, df_day in df_input.groupby(df_input['timestamp'].dt.date):
                        total_day = int(df_day['count'].sum())
                        if total_day <= 0:
                            continue
                        bins_sum = df_day[bin_cols].sum()
                        counts = [int(bins_sum.iloc[i]) if i < len(bins_sum) else 0 for i in range(len(speed_centers))]
                        mean_speed, std_speed = mean_std_from_bins(counts, speed_centers)
                        v15 = percentile_from_bins(counts, speed_centers, 0.15)
                        v50 = percentile_from_bins(counts, speed_centers, 0.50)
                        v85 = percentile_from_bins(counts, speed_centers, 0.85)
                        infractions, inf_pct = infractions_from_bins(counts, speed_centers, vmax)
                        periods = []
                        for start_time, end_time in parsed_periods:
                            periods.append(get_period_count(df_day, start_time, end_time))
                        daily_rows.append({
                            'mean': mean_speed,
                            'std': std_speed,
                            'v15': v15,
                            'v50': v50,
                            'v85': v85,
                            'infractions': infractions,
                            'inf_pct': inf_pct,
                            'periods': periods,
                        })
                    return daily_rows

                def _avg(values):
                    return sum(values) / len(values) if values else 0.0

                def summarize_row(direction_label, vehicle_label):
                    df_dir = df_scope[df_scope['direction'] == direction_label]
                    if vehicle_label == 'TV':
                        df_cls = df_dir
                    else:
                        df_cls = df_dir[df_dir['vehicle_class'] == vehicle_label]

                    total = int(df_cls['count'].sum())
                    total_tv = int(df_dir['count'].sum()) if not df_dir.empty else 0
                    pct = (total / total_tv * 100) if total_tv > 0 else 0

                    scope_min = df_scope['timestamp'].min()
                    scope_max = df_scope['timestamp'].max()
                    duration_hours = (scope_max - scope_min).total_seconds() / 3600 if pd.notna(scope_min) else 0
                    if duration_hours <= 0:
                        duration_hours = 1

                    scope_days = df_scope['timestamp'].dt.date.nunique()
                    if scope_days <= 0:
                        scope_days = 1
                    tmj = total / scope_days
                    tmh = total / duration_hours

                    if use_daily_averages:
                        daily_rows = _daily_metrics(df_cls)
                        mean_speed = _avg([r['mean'] for r in daily_rows])
                        std_speed = _avg([r['std'] for r in daily_rows])
                        v15 = _avg([r['v15'] for r in daily_rows])
                        v50 = _avg([r['v50'] for r in daily_rows])
                        v85 = _avg([r['v85'] for r in daily_rows])
                        infractions = _avg([r['infractions'] for r in daily_rows])
                        inf_pct = _avg([r['inf_pct'] for r in daily_rows])
                        periods = []
                        for period_idx in range(3):
                            periods.append(_avg([r['periods'][period_idx] for r in daily_rows]))
                    else:
                        counts = [0] * len(speed_centers)
                        if not df_cls.empty:
                            bins_sum = df_cls[bin_cols].sum()
                            for i in range(len(speed_centers)):
                                counts[i] = int(bins_sum.iloc[i]) if i < len(bins_sum) else 0

                        mean_speed, std_speed = mean_std_from_bins(counts, speed_centers)
                        v15 = percentile_from_bins(counts, speed_centers, 0.15)
                        v50 = percentile_from_bins(counts, speed_centers, 0.50)
                        v85 = percentile_from_bins(counts, speed_centers, 0.85)
                        infractions, inf_pct = infractions_from_bins(counts, speed_centers, vmax)

                        periods = []
                        for start_time, end_time in parsed_periods:
                            periods.append(get_period_count(df_cls, start_time, end_time) / scope_days)

                    return {
                        'pct': pct,
                        'tmj': tmj,
                        'tmh': tmh,
                        'mean': mean_speed,
                        'v15': v15,
                        'v50': v50,
                        'v85': v85,
                        'std': std_speed,
                        'infractions': infractions,
                        'inf_pct': inf_pct,
                        'periods': periods,
                    }

                def summarize_direction(direction_label):
                    return {
                        'TV': summarize_row(direction_label, 'TV'),
                        'VL': summarize_row(direction_label, 'VL'),
                        'PL': summarize_row(direction_label, 'PL'),
                    }

                def summarize_sens3():
                    df_sens3 = df_scope[df_scope['direction'].isin(['Sens 1', 'Sens 2'])].copy()
                    if df_sens3.empty:
                        return {
                            'TV': summarize_row('Sens 1', 'TV'),
                            'VL': summarize_row('Sens 1', 'VL'),
                            'PL': summarize_row('Sens 1', 'PL'),
                        }

                    def summarize_row_sens3(vehicle_label):
                        if vehicle_label == 'TV':
                            df_cls = df_sens3
                        else:
                            df_cls = df_sens3[df_sens3['vehicle_class'] == vehicle_label]

                        total = int(df_cls['count'].sum())
                        total_tv = int(df_sens3['count'].sum()) if not df_sens3.empty else 0
                        pct = (total / total_tv * 100) if total_tv > 0 else 0

                        scope_min = df_scope['timestamp'].min()
                        scope_max = df_scope['timestamp'].max()
                        duration_hours = (scope_max - scope_min).total_seconds() / 3600 if pd.notna(scope_min) else 0
                        if duration_hours <= 0:
                            duration_hours = 1

                        scope_days = df_scope['timestamp'].dt.date.nunique()
                        if scope_days <= 0:
                            scope_days = 1
                        tmj = total / scope_days
                        tmh = total / duration_hours

                        if use_daily_averages:
                            daily_rows = _daily_metrics(df_cls)
                            mean_speed = _avg([r['mean'] for r in daily_rows])
                            std_speed = _avg([r['std'] for r in daily_rows])
                            v15 = _avg([r['v15'] for r in daily_rows])
                            v50 = _avg([r['v50'] for r in daily_rows])
                            v85 = _avg([r['v85'] for r in daily_rows])
                            infractions = _avg([r['infractions'] for r in daily_rows])
                            inf_pct = _avg([r['inf_pct'] for r in daily_rows])
                            periods = []
                            for period_idx in range(3):
                                periods.append(_avg([r['periods'][period_idx] for r in daily_rows]))
                        else:
                            counts = [0] * len(speed_centers)
                            if not df_cls.empty:
                                bins_sum = df_cls[bin_cols].sum()
                                for i in range(len(speed_centers)):
                                    counts[i] = int(bins_sum.iloc[i]) if i < len(bins_sum) else 0

                            mean_speed, std_speed = mean_std_from_bins(counts, speed_centers)
                            v15 = percentile_from_bins(counts, speed_centers, 0.15)
                            v50 = percentile_from_bins(counts, speed_centers, 0.50)
                            v85 = percentile_from_bins(counts, speed_centers, 0.85)
                            infractions, inf_pct = infractions_from_bins(counts, speed_centers, vmax)

                            periods = []
                            for start_time, end_time in parsed_periods:
                                periods.append(get_period_count(df_cls, start_time, end_time) / scope_days)

                        return {
                            'pct': pct,
                            'tmj': tmj,
                            'tmh': tmh,
                            'mean': mean_speed,
                            'v15': v15,
                            'v50': v50,
                            'v85': v85,
                            'std': std_speed,
                            'infractions': infractions,
                            'inf_pct': inf_pct,
                            'periods': periods,
                        }

                    return {
                        'TV': summarize_row_sens3('TV'),
                        'VL': summarize_row_sens3('VL'),
                        'PL': summarize_row_sens3('PL'),
                    }

                sens1 = summarize_direction('Sens 1')
                sens2 = summarize_direction('Sens 2')
                sens3 = summarize_sens3()

                table = doc_obj.add_table(rows=2, cols=15)
                table.style = 'Table Grid'

                header1 = table.rows[0].cells
                header1[0].text = ''
                header1[1].text = ''
                header1[2].text = 'Débits'
                header1[5].text = 'Vitesses (km/h)'
                header1[12].text = 'Périodes'
                header1[2].merge(header1[4])
                header1[5].merge(header1[11])
                header1[12].merge(header1[14])

                header2 = table.rows[1].cells
                header2[0].text = ''
                header2[1].text = ''
                header2[2].text = '%'
                header2[3].text = 'TMJ'
                header2[4].text = 'TMH'
                header2[5].text = 'Moyenne'
                header2[6].text = 'V15'
                header2[7].text = 'V50'
                header2[8].text = 'V85'
                header2[9].text = 'Ecart Type'
                header2[10].text = 'Infractions'
                header2[11].text = '%'
                header2[12].text = '1'
                header2[13].text = '2'
                header2[14].text = '3'

                def add_direction_block(direction_label, data, color_hex):
                    block_rows = []
                    for idx, vehicle_label in enumerate(['TV', 'VL', 'PL']):
                        row_cells = table.add_row().cells
                        block_rows.append(row_cells)
                        row_cells[0].text = direction_label if idx == 0 else ''
                        row_cells[1].text = 'TV (Tout véhicules)' if vehicle_label == 'TV' else ('VL (Véhicules légers)' if vehicle_label == 'VL' else 'PL (Poids lourds)')

                        metrics = data[vehicle_label]
                        row_cells[2].text = f"{metrics['pct']:.0f}%"
                        row_cells[3].text = f"{metrics['tmj']:.0f}"
                        row_cells[4].text = f"{metrics['tmh']:.1f}"
                        row_cells[5].text = f"{metrics['mean']:.1f}"
                        row_cells[6].text = f"{metrics['v15']:.1f}"
                        row_cells[7].text = f"{metrics['v50']:.1f}"
                        row_cells[8].text = f"{metrics['v85']:.1f}"
                        row_cells[9].text = f"{metrics['std']:.1f}"
                        row_cells[10].text = f"{metrics['infractions']:.0f}"
                        row_cells[11].text = f"{metrics['inf_pct']:.0f}%"
                        periods = metrics.get('periods', [])
                        row_cells[12].text = f"{periods[0] if len(periods) > 0 else 0:.0f}"
                        row_cells[13].text = f"{periods[1] if len(periods) > 1 else 0:.0f}"
                        row_cells[14].text = f"{periods[2] if len(periods) > 2 else 0:.0f}"

                    block_rows[0][0].merge(block_rows[2][0])
                    set_vmerge(block_rows[0][0], 'restart')
                    set_vmerge(block_rows[1][0], 'continue')
                    set_vmerge(block_rows[2][0], 'continue')
                    block_rows[1][0].text = ''
                    block_rows[2][0].text = ''
                    set_cell_shading(block_rows[0][0], color_hex)

                add_direction_block('Sens 1', sens1, '4F81BD')
                add_direction_block('Sens 2', sens2, 'FF0000')
                add_direction_block('Sens 3 (S1+S2)', sens3, '00B050')

                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.size = Pt(7)

                doc_obj.add_paragraph(f"Période 1 : {period_ranges[0]}")
                doc_obj.add_paragraph(f"Période 2 : {period_ranges[1]}")
                doc_obj.add_paragraph(f"Période 3 : {period_ranges[2]}")
                doc_obj.add_paragraph(f"Vitesse maximum autorisée : {vmax} km/h")

            for date_only in unique_dates:
                df_day = df[df['date_only'] == date_only].copy()
                doc = Document()
                section = doc.sections[0]
                section.orientation = WD_ORIENT.LANDSCAPE
                section.page_width = Mm(297)
                section.page_height = Mm(210)

                add_header_logo(doc)
                add_footer_page_number(doc)

                build_summary_section(doc, df, "Rapport global", use_daily_averages=True)
                doc.add_page_break()
                build_summary_section(doc, df_day, f"Rapport du {date_only.strftime('%d/%m/%Y')}", use_daily_averages=False)

                bin_cols = [f"Bin{i+1}" for i in range(12)]
                for col in bin_cols:
                    if col not in df_day.columns:
                        df_day.loc[:, col] = 0

                speed_centers = self.current_metadata.get('speed_bin_centers', [])
                if not speed_centers:
                    speed_centers = [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]

                df_day.loc[:, 'Date'] = df_day['timestamp'].dt.strftime('%d/%m/%Y')
                df_day.loc[:, 'Heure'] = df_day['timestamp'].dt.strftime('%H:%M')

                def compute_vmoy(row):
                    total = sum(row[col] for col in bin_cols)
                    if total <= 0:
                        return 0.0
                    return sum(row[bin_cols[i]] * speed_centers[i] for i in range(len(bin_cols))) / total

                def build_vitesse_day(direction_label, vehicle_class_label):
                    df_vitesse = df_day[(df_day['direction'] == direction_label) & (df_day['vehicle_class'] == vehicle_class_label)].copy()
                    grouped = df_vitesse.groupby(['Date', 'Heure'])[bin_cols].sum().reset_index()
                    if grouped.empty:
                        return grouped
                    grouped['Vmoy'] = grouped.apply(compute_vmoy, axis=1)
                    grouped['Débit'] = grouped[bin_cols].sum(axis=1)
                    grouped['Vmoy'] = grouped['Vmoy'].round(1)
                    return grouped[['Date', 'Heure'] + bin_cols + ['Vmoy', 'Débit']]

                def build_vitesse_charts(vitesse_df, bin_columns):
                    if vitesse_df.empty:
                        return None, None

                    chart_df = vitesse_df.copy()
                    chart_df['DateTime'] = pd.to_datetime(
                        chart_df['Date'] + ' ' + chart_df['Heure'],
                        dayfirst=True,
                        errors='coerce'
                    )
                    chart_df = chart_df.sort_values('DateTime')

                    x_labels = chart_df['Heure'].tolist()
                    debit_vals = chart_df['Débit'].astype(float).tolist()
                    vmoy_vals = chart_df['Vmoy'].astype(float).tolist()
                    x_vals = list(range(len(chart_df)))

                    fig1, ax1 = plt.subplots(figsize=(7.5, 2.4), dpi=200)
                    ax1.plot(x_vals, debit_vals, marker='o', linewidth=0.5, color='#1F77B4', label='Débit')
                    ax1.set_xlabel('Heure', fontsize=10)
                    ax1.set_ylabel('Débit', fontsize=10)
                    ax1.set_ylim(0, debit_ylim)
                    ax1.grid(True, linewidth=0.3, alpha=0.6)
                    ax1.tick_params(axis='both', labelsize=8)

                    ax1_right = ax1.twinx()
                    ax1_right.plot(x_vals, vmoy_vals, marker='s', linewidth=0.5, color='#FF7F0E', label='Vmoy')
                    ax1_right.set_ylabel('Vmoy', fontsize=10)
                    ax1_right.set_ylim(0, vmoy_ylim)
                    ax1_right.tick_params(axis='y', labelsize=8)

                    tick_count = min(8, len(x_vals))
                    if tick_count > 0:
                        step = max(1, len(x_vals) // tick_count)
                        tick_idx = list(range(0, len(x_vals), step))
                        ax1.set_xticks(tick_idx)
                        ax1.set_xticklabels([x_labels[i] for i in tick_idx], rotation=45, ha='right', fontsize=8)
                    else:
                        ax1.set_xticks([])

                    handles_left, labels_left = ax1.get_legend_handles_labels()
                    handles_right, labels_right = ax1_right.get_legend_handles_labels()
                    ax1.legend(handles_left + handles_right, labels_left + labels_right, fontsize=8, loc='upper left')

                    fig1.tight_layout()
                    buf1 = io.BytesIO()
                    fig1.savefig(buf1, format='png', bbox_inches='tight')
                    plt.close(fig1)

                    bin_sums = chart_df[bin_columns].sum()
                    bin_labels = list(bin_columns)
                    bin_counts = [float(bin_sums[col]) for col in bin_columns]

                    fig2, ax2 = plt.subplots(figsize=(7.5, 2.4), dpi=200)
                    ax2.bar(bin_labels, bin_counts, color='#4F81BD')
                    ax2.set_xlabel('Bins', fontsize=10)
                    ax2.set_ylabel('Nombre de vehicules', fontsize=10)
                    ax2.set_ylim(0, bin_ylim)
                    ax2.grid(True, axis='y', linewidth=0.3, alpha=0.6)
                    ax2.tick_params(axis='both', labelsize=8)
                    ax2.tick_params(axis='x', labelrotation=45)

                    fig2.tight_layout()
                    buf2 = io.BytesIO()
                    fig2.savefig(buf2, format='png', bbox_inches='tight')
                    plt.close(fig2)

                    return buf1, buf2

                page_order = [
                    ('Sens 1', 'VL'),
                    ('Sens 1', 'PL'),
                    ('Sens 2', 'VL'),
                    ('Sens 2', 'PL'),
                ]

                vitesse_map = {
                    (direction_label, vehicle_class_label): build_vitesse_day(direction_label, vehicle_class_label)
                    for direction_label, vehicle_class_label in page_order
                }

                debit_max = max(
                    [df_item['Débit'].max() for df_item in vitesse_map.values() if not df_item.empty] or [0]
                )
                vmoy_max = max(
                    [df_item['Vmoy'].max() for df_item in vitesse_map.values() if not df_item.empty] or [0]
                )
                bin_max = max(
                    [df_item[bin_cols].sum().max() for df_item in vitesse_map.values() if not df_item.empty] or [0]
                )

                pad = 1.05
                debit_ylim = max(1.0, float(debit_max) * pad)
                vmoy_ylim = max(1.0, float(vmoy_max) * pad)
                bin_ylim = max(1.0, float(bin_max) * pad)

                for idx, (direction_label, vehicle_class_label) in enumerate(page_order):
                    vitesse_day = vitesse_map[(direction_label, vehicle_class_label)]
                    doc.add_page_break()
                    page_title = doc.add_heading(
                        f"Vitesse {direction_label} {vehicle_class_label} - {date_only.strftime('%d/%m/%Y')}",
                        level=2
                    )
                    page_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    if vitesse_day.empty:
                        doc.add_paragraph("Aucune donnee pour cette combinaison.")
                        continue

                    table = doc.add_table(rows=1, cols=len(vitesse_day.columns))
                    table.style = 'Table Grid'
                    table.autofit = True

                    header_cells = table.rows[0].cells
                    for col_idx, col_name in enumerate(vitesse_day.columns):
                        header_cells[col_idx].text = str(col_name)

                    for _, row in vitesse_day.iterrows():
                        row_cells = table.add_row().cells
                        for col_idx, col_name in enumerate(vitesse_day.columns):
                            val = row[col_name]
                            if isinstance(val, float):
                                row_cells[col_idx].text = f"{val:.1f}" if col_name == 'Vmoy' else f"{int(val)}"
                            else:
                                row_cells[col_idx].text = str(val)

                    totals = {}
                    for col_name in vitesse_day.columns:
                        if col_name in ['Date', 'Heure']:
                            totals[col_name] = ''
                        elif col_name == 'Vmoy':
                            totals[col_name] = float(vitesse_day['Vmoy'].mean()) if not vitesse_day.empty else 0.0
                        elif col_name == 'Débit':
                            totals[col_name] = float(vitesse_day['Débit'].sum()) if not vitesse_day.empty else 0.0
                        else:
                            totals[col_name] = float(vitesse_day[col_name].sum())

                    total_cells = table.add_row().cells
                    total_cells[0].text = 'Total'
                    if len(total_cells) > 1:
                        total_cells[1].text = ''
                    for col_idx, col_name in enumerate(vitesse_day.columns):
                        if col_idx < 2:
                            continue
                        val = totals[col_name]
                        if col_name == 'Vmoy':
                            total_cells[col_idx].text = f"{val:.1f}"
                        else:
                            total_cells[col_idx].text = f"{int(val)}"

                    for table_row in table.rows:
                        for cell in table_row.cells:
                            for paragraph in cell.paragraphs:
                                for run in paragraph.runs:
                                    run.font.size = Pt(8)

                    chart1, chart2 = build_vitesse_charts(vitesse_day, bin_cols)
                    if chart1 and chart2:
                        charts_table = doc.add_table(rows=2, cols=1)
                        charts_table.autofit = True
                        chart_width = Mm(190.5)
                        for cell, chart in zip([charts_table.rows[0].cells[0], charts_table.rows[1].cells[0]], [chart1, chart2]):
                            paragraph = cell.paragraphs[0]
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = paragraph.add_run()
                            chart.seek(0)
                            run.add_picture(chart, width=chart_width)

                file_name = f"{date_only.strftime('%d-%m-%Y')}.docx"
                file_path = os.path.join(folder, file_name)
                doc.save(file_path)

            QMessageBox.information(self, "Succes", f"Rapports generes avec succes dans:\n{folder}")
        except Exception as exc:
            import traceback
            detail = traceback.format_exc()
            print(detail)
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la generation des rapports:\n{str(exc)}\n\n{detail}"
            )
    
    def _export_debit_vitesse(self):
        """Export data in Debit-Vitesse (Nordcompteur) format using template"""
        # Template file path
        template_path = r"C:\Users\royston.fernandes\Documents\isr-a\MasterCompte 6.40\Data_Nordcompteur\reference.xlsx"
        
        # Check if template exists
        if not os.path.exists(template_path):
            QMessageBox.warning(self, "Erreur", f"Le fichier template n'existe pas:\n{template_path}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter en format Débit-Vitesse",
            os.path.expanduser("~/Documents"),
            "Fichiers Excel (*.xlsx);;Tous les fichiers (*)"
        )

        if file_path and not file_path.endswith('.xlsx'):
            file_path += '.xlsx'
        
        if not file_path:
            return
        
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import Font, Color
            from datetime import datetime, timedelta
            from shutil import copy2
            
            df = self.current_df
            meta = self.current_metadata
            
            # Define all 12 speed bins
            speed_bins = [
                ('<30', 15), ('30-40', 35), ('40-50', 45), ('50-60', 55),
                ('60-70', 65), ('70-80', 75), ('80-90', 85), ('90-100', 95),
                ('100-110', 105), ('110-120', 115), ('120-130', 125), ('130-150', 140)
            ]
            
            # Copy template to output location
            copy2(template_path, file_path)

            # Open template and populate raw data for each direction
            wb = load_workbook(file_path)
            try:
                wb.calculationProperties.calcMode = "auto"
                wb.calculationProperties.fullCalcOnLoad = True
            except Exception:
                pass
            
            # Get raw data from metadata
            raw_data = meta.get('raw_data', [])
            rows_per_block = meta.get('rows_per_block', 1)
            sensor_map = meta.get('sensor_map', {})
            num_sensors = meta.get('num_sensors', 0)
            interval_minutes = meta.get('interval_minutes', 5)
            
            if not raw_data:
                QMessageBox.warning(self, "Erreur", "Pas de données brutes disponibles pour l'export template")
                return
            
            # Calculate start and end datetime from the data
            if meta.get('year'):
                start_dt = datetime(
                    meta['year'], meta['month'], meta['day'],
                    meta.get('start_hour', 0), meta.get('start_minute', 0)
                )
            else:
                start_dt = df['timestamp'].min()
            
            # Calculate end datetime based on number of data points
            num_measurements = len(df['timestamp'].unique())
            freq = meta.get('interval_minutes', 60)
            end_dt = start_dt + timedelta(minutes=freq * (num_measurements - 1))
            
            # Update cell Z3 in the first sheet (usually "Synthese_des_donnees") with actual date range
            first_sheet = wb.worksheets[0]
            second_sheet = wb.worksheets[1] if len(wb.worksheets) > 1 else None
            third_sheet = wb.worksheets[2] if len(wb.worksheets) > 2 else None
            fourth_sheet = wb.worksheets[3] if len(wb.worksheets) > 3 else None
            fifth_sheet = wb.worksheets[4] if len(wb.worksheets) > 4 else None
            
            # Function to safely write to a cell (handles merged cells without breaking format)
            def safe_write_cell(sheet, cell_ref, value, font=None):
                """Write to a cell, handling merged ranges properly by writing to top-left cell"""
                from openpyxl.utils import coordinate_to_tuple, get_column_letter
                
                # Find if this cell is part of a merged range
                target_cell = cell_ref
                for merged_range in sheet.merged_cells:
                    if cell_ref in merged_range:
                        # Write to the top-left cell of the merged range
                        min_row = merged_range.min_row
                        min_col = merged_range.min_col
                        target_cell = f"{get_column_letter(min_col)}{min_row}"
                        break
                
                # Write the value to the target cell
                sheet[target_cell] = value
                if font:
                    sheet[target_cell].font = font

            def safe_write_cell_rc(sheet, row, col, value):
                """Write to a cell by row/col, handling merged ranges properly"""
                from openpyxl.utils import get_column_letter

                target_row, target_col = row, col
                for merged_range in sheet.merged_cells:
                    if merged_range.min_row <= row <= merged_range.max_row and merged_range.min_col <= col <= merged_range.max_col:
                        target_row = merged_range.min_row
                        target_col = merged_range.min_col
                        break

                target_cell = f"{get_column_letter(target_col)}{target_row}"
                sheet[target_cell] = value

            def copy_range_with_styles(ws, src_min_row, src_max_row, src_min_col, src_max_col, row_offset):
                """Copy a rectangular range (values + styles + row heights + merged cells) down by row_offset."""
                from copy import copy as _copy
                from openpyxl.utils import get_column_letter
                import re

                def _shift_formula_rows(formula, offset):
                    if not formula or offset == 0:
                        return formula
                    def repl(match):
                        # Do not shift references that are explicitly tied to another sheet
                        if match.start() > 0 and formula[match.start() - 1] == '!':
                            return match.group(0)
                        col = match.group(1)
                        row_dollar = match.group(2) or ""
                        row = int(match.group(3))
                        return f"{col}{row_dollar}{row + offset}"
                    return re.sub(r"(\$?[A-Z]{1,3})(\$?)(\d+)", repl, formula)

                for r in range(src_min_row, src_max_row + 1):
                    for c in range(src_min_col, src_max_col + 1):
                        src = ws.cell(row=r, column=c)
                        tgt = ws.cell(row=r + row_offset, column=c)
                        # Only write values to top-left of merged ranges
                        is_merged = False
                        is_top_left = False
                        for merged_range in ws.merged_cells.ranges:
                            if (merged_range.min_row <= tgt.row <= merged_range.max_row and
                                merged_range.min_col <= tgt.column <= merged_range.max_col):
                                is_merged = True
                                is_top_left = (tgt.row == merged_range.min_row and tgt.column == merged_range.min_col)
                                break
                        if (not is_merged) or is_top_left:
                            if isinstance(src.value, str) and src.value.startswith('='):
                                tgt.value = _shift_formula_rows(src.value, row_offset)
                            else:
                                tgt.value = src.value
                                QMessageBox.information(self, "Succès", f"Fichier par jour exporté avec succès:\n{file_path2}")
                        if src.has_style:
                            if (not is_merged) or is_top_left:
                                tgt.font = _copy(src.font)
                                tgt.border = _copy(src.border)
                                tgt.fill = _copy(src.fill)
                                tgt.number_format = _copy(src.number_format)
                                tgt.protection = _copy(src.protection)
                                tgt.alignment = _copy(src.alignment)

                for r in range(src_min_row, src_max_row + 1):
                    src_dim = ws.row_dimensions[r]
                    tgt_dim = ws.row_dimensions[r + row_offset]
                    if src_dim.height is not None:
                        tgt_dim.height = src_dim.height
                    if src_dim.hidden is not None:
                        tgt_dim.hidden = src_dim.hidden
                    if src_dim.outlineLevel is not None:
                        tgt_dim.outlineLevel = src_dim.outlineLevel
                    if src_dim.collapsed is not None:
                        tgt_dim.collapsed = src_dim.collapsed

                for merged_range in list(ws.merged_cells.ranges):
                    if (src_min_row <= merged_range.min_row <= src_max_row and
                        src_min_col <= merged_range.min_col <= src_max_col):
                        new_range = (
                            f"{get_column_letter(merged_range.min_col)}{merged_range.min_row + row_offset}:"
                            f"{get_column_letter(merged_range.max_col)}{merged_range.max_row + row_offset}"
                        )
                        if new_range not in ws.merged_cells:
                            ws.merge_cells(new_range)
            
            date_range_text = f"du {start_dt.strftime('%d/%m/%Y %H:%M')} au {end_dt.strftime('%d/%m/%Y %H:%M')}"
            safe_write_cell(first_sheet, 'Z3', date_range_text, Font(name='Arial', size=12, bold=True, italic=True))
            if second_sheet is not None:
                safe_write_cell(second_sheet, 'Z3', date_range_text, Font(name='Arial', size=12, bold=True, italic=True))
            if third_sheet is not None:
                safe_write_cell(third_sheet, 'Z3', date_range_text, Font(name='Arial', size=12, bold=True, italic=True))
            if fourth_sheet is not None:
                safe_write_cell(fourth_sheet, 'Z3', date_range_text, Font(name='Arial', size=12, bold=True, italic=True))
            if fifth_sheet is not None:
                safe_write_cell(fifth_sheet, 'Z3', date_range_text, Font(name='Arial', size=12, bold=True, italic=True))
            
            # Update cell K5 with generic location text
            safe_write_cell(first_sheet, 'K5', 'Ville - Poste xx - rue/avenue/boulevard', Font(name='Arial', size=12, bold=True, italic=True))
            if second_sheet is not None:
                safe_write_cell(second_sheet, 'K5', 'Ville - Poste xx - rue/avenue/boulevard', Font(name='Arial', size=12, bold=True, italic=True))
            if third_sheet is not None:
                safe_write_cell(third_sheet, 'K5', 'Ville - Poste xx - rue/avenue/boulevard', Font(name='Arial', size=12, bold=True, italic=True))
            if fourth_sheet is not None:
                safe_write_cell(fourth_sheet, 'K5', 'Ville - Poste xx - rue/avenue/boulevard', Font(name='Arial', size=12, bold=True, italic=True))
            if fifth_sheet is not None:
                safe_write_cell(fifth_sheet, 'K5', 'Ville - Poste xx - rue/avenue/boulevard', Font(name='Arial', size=12, bold=True, italic=True))

            # Ensure "Sens 2" K5 and Z3 match "Sens 1"
            if 'Sens 1' in wb.sheetnames and 'Sens 2' in wb.sheetnames:
                sens1_sheet = wb['Sens 1']
                sens2_sheet = wb['Sens 2']
                safe_write_cell(sens2_sheet, 'K5', sens1_sheet['K5'].value)
                safe_write_cell(sens2_sheet, 'Z3', sens1_sheet['Z3'].value)

            # Ensure "Sens 3 (S1+S2)" K5 and Z3 match "Sens 1"
            if 'Sens 1' in wb.sheetnames and 'Sens 3 (S1+S2)' in wb.sheetnames:
                sens1_sheet = wb['Sens 1']
                sens3_sheet = wb['Sens 3 (S1+S2)']
                safe_write_cell(sens3_sheet, 'K5', sens1_sheet['K5'].value)
                safe_write_cell(sens3_sheet, 'Z3', sens1_sheet['Z3'].value)

            # Update T36 with authorized maximum speed (if provided)
            if self.max_speed_authorized is not None:
                safe_write_cell(first_sheet, 'T36', self.max_speed_authorized)
            
            # Calculate TMJ (Taux Moyen Journalier - Average Daily Rate) for each direction
            num_days = (end_dt - start_dt).days + 1
            if num_days == 0:
                num_days = 1
            
            # Calculate number of hours in the period for TMH
            num_hours = ((end_dt - start_dt).total_seconds() / 3600)
            if num_hours == 0:
                num_hours = 1
            
            # Group data by direction and vehicle class
            sens1_total_sum = df[(df['direction'].isin(['Sens 1', '1']))]['count'].sum()
            sens1_vl_sum = df[(df['direction'].isin(['Sens 1', '1'])) & (df['vehicle_class'] == 'VL')]['count'].sum()
            sens1_pl_sum = df[(df['direction'].isin(['Sens 1', '1'])) & (df['vehicle_class'] == 'PL')]['count'].sum()
            
            sens2_total_sum = df[(df['direction'].isin(['Sens 2', '2']))]['count'].sum()
            sens2_vl_sum = df[(df['direction'].isin(['Sens 2', '2'])) & (df['vehicle_class'] == 'VL')]['count'].sum()
            sens2_pl_sum = df[(df['direction'].isin(['Sens 2', '2'])) & (df['vehicle_class'] == 'PL')]['count'].sum()
            
            # TMJ calculations
            sens1_total_tmj = sens1_total_sum / num_days
            sens1_vl_tmj = sens1_vl_sum / num_days
            sens1_pl_tmj = sens1_pl_sum / num_days
            sens2_total_tmj = sens2_total_sum / num_days
            sens2_vl_tmj = sens2_vl_sum / num_days
            sens2_pl_tmj = sens2_pl_sum / num_days
            combined_total_tmj = (sens1_total_tmj + sens2_total_tmj)
            combined_vl_tmj = (sens1_vl_tmj + sens2_vl_tmj)
            combined_pl_tmj = (sens1_pl_tmj + sens2_pl_tmj)
            
            # TMH calculations (Taux Moyen Horaire - Average Hourly Rate)
            sens1_total_tmh = sens1_total_sum / num_hours
            sens1_vl_tmh = sens1_vl_sum / num_hours
            sens1_pl_tmh = sens1_pl_sum / num_hours
            sens2_total_tmh = sens2_total_sum / num_hours
            sens2_vl_tmh = sens2_vl_sum / num_hours
            sens2_pl_tmh = sens2_pl_sum / num_hours
            combined_total_tmh = (sens1_total_tmh + sens2_total_tmh)
            combined_vl_tmh = (sens1_vl_tmh + sens2_vl_tmh)
            combined_pl_tmh = (sens1_pl_tmh + sens2_pl_tmh)

            # TMJ between 10:00 and 12:00 (average daily counts in that window)
            df_10_12 = df[(df['timestamp'].dt.hour >= 10) & (df['timestamp'].dt.hour < 12)]

            # TMJ between 14:00 and 16:00
            df_14_16 = df[(df['timestamp'].dt.hour >= 14) & (df['timestamp'].dt.hour < 16)]

            # TMJ between 18:00 and 20:00
            df_18_20 = df[(df['timestamp'].dt.hour >= 18) & (df['timestamp'].dt.hour < 20)]

            sens1_total_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 1', '1']))]['count'].sum() / num_days
            sens1_vl_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 1', '1'])) & (df_10_12['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens1_pl_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 1', '1'])) & (df_10_12['vehicle_class'] == 'PL')]['count'].sum() / num_days

            sens2_total_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 2', '2']))]['count'].sum() / num_days
            sens2_vl_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 2', '2'])) & (df_10_12['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens2_pl_tmj_10_12 = df_10_12[(df_10_12['direction'].isin(['Sens 2', '2'])) & (df_10_12['vehicle_class'] == 'PL')]['count'].sum() / num_days

            combined_total_tmj_10_12 = sens1_total_tmj_10_12 + sens2_total_tmj_10_12
            combined_vl_tmj_10_12 = sens1_vl_tmj_10_12 + sens2_vl_tmj_10_12
            combined_pl_tmj_10_12 = sens1_pl_tmj_10_12 + sens2_pl_tmj_10_12

            sens1_total_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 1', '1']))]['count'].sum() / num_days
            sens1_vl_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 1', '1'])) & (df_14_16['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens1_pl_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 1', '1'])) & (df_14_16['vehicle_class'] == 'PL')]['count'].sum() / num_days

            sens2_total_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 2', '2']))]['count'].sum() / num_days
            sens2_vl_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 2', '2'])) & (df_14_16['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens2_pl_tmj_14_16 = df_14_16[(df_14_16['direction'].isin(['Sens 2', '2'])) & (df_14_16['vehicle_class'] == 'PL')]['count'].sum() / num_days

            combined_total_tmj_14_16 = sens1_total_tmj_14_16 + sens2_total_tmj_14_16
            combined_vl_tmj_14_16 = sens1_vl_tmj_14_16 + sens2_vl_tmj_14_16
            combined_pl_tmj_14_16 = sens1_pl_tmj_14_16 + sens2_pl_tmj_14_16

            sens1_total_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 1', '1']))]['count'].sum() / num_days
            sens1_vl_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 1', '1'])) & (df_18_20['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens1_pl_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 1', '1'])) & (df_18_20['vehicle_class'] == 'PL')]['count'].sum() / num_days

            sens2_total_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 2', '2']))]['count'].sum() / num_days
            sens2_vl_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 2', '2'])) & (df_18_20['vehicle_class'] == 'VL')]['count'].sum() / num_days
            sens2_pl_tmj_18_20 = df_18_20[(df_18_20['direction'].isin(['Sens 2', '2'])) & (df_18_20['vehicle_class'] == 'PL')]['count'].sum() / num_days

            combined_total_tmj_18_20 = sens1_total_tmj_18_20 + sens2_total_tmj_18_20
            combined_vl_tmj_18_20 = sens1_vl_tmj_18_20 + sens2_vl_tmj_18_20
            combined_pl_tmj_18_20 = sens1_pl_tmj_18_20 + sens2_pl_tmj_18_20
            
            # Write TMJ values to first sheet (column L)
            safe_write_cell(first_sheet, 'L41', round(sens1_total_tmj, 0))
            safe_write_cell(first_sheet, 'L42', round(sens1_vl_tmj, 0))
            safe_write_cell(first_sheet, 'L43', round(sens1_pl_tmj, 0))
            safe_write_cell(first_sheet, 'L45', round(sens2_total_tmj, 0))
            safe_write_cell(first_sheet, 'L46', round(sens2_vl_tmj, 0))
            safe_write_cell(first_sheet, 'L47', round(sens2_pl_tmj, 0))
            safe_write_cell(first_sheet, 'L49', round(combined_total_tmj, 0))
            safe_write_cell(first_sheet, 'L50', round(combined_vl_tmj, 0))
            safe_write_cell(first_sheet, 'L51', round(combined_pl_tmj, 0))
            
            # Write TMH values to first sheet (column N)
            safe_write_cell(first_sheet, 'N41', round(sens1_total_tmh, 0))
            safe_write_cell(first_sheet, 'N42', round(sens1_vl_tmh, 0))
            safe_write_cell(first_sheet, 'N43', round(sens1_pl_tmh, 0))
            safe_write_cell(first_sheet, 'N45', round(sens2_total_tmh, 0))
            safe_write_cell(first_sheet, 'N46', round(sens2_vl_tmh, 0))
            safe_write_cell(first_sheet, 'N47', round(sens2_pl_tmh, 0))
            safe_write_cell(first_sheet, 'N49', round(combined_total_tmh, 0))
            safe_write_cell(first_sheet, 'N50', round(combined_vl_tmh, 0))
            safe_write_cell(first_sheet, 'N51', round(combined_pl_tmh, 0))

            # Write TMJ 10:00-12:00 values to first sheet (column AC)
            safe_write_cell(first_sheet, 'AC41', round(sens1_total_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC42', round(sens1_vl_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC43', round(sens1_pl_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC45', round(sens2_total_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC46', round(sens2_vl_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC47', round(sens2_pl_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC49', round(combined_total_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC50', round(combined_vl_tmj_10_12, 0))
            safe_write_cell(first_sheet, 'AC51', round(combined_pl_tmj_10_12, 0))

            # Write TMJ 14:00-16:00 values to first sheet (column AD)
            safe_write_cell(first_sheet, 'AD41', round(sens1_total_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD42', round(sens1_vl_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD43', round(sens1_pl_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD45', round(sens2_total_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD46', round(sens2_vl_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD47', round(sens2_pl_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD49', round(combined_total_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD50', round(combined_vl_tmj_14_16, 0))
            safe_write_cell(first_sheet, 'AD51', round(combined_pl_tmj_14_16, 0))

            # Write TMJ 18:00-20:00 values to first sheet (column AE)
            safe_write_cell(first_sheet, 'AE41', round(sens1_total_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE42', round(sens1_vl_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE43', round(sens1_pl_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE45', round(sens2_total_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE46', round(sens2_vl_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE47', round(sens2_pl_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE49', round(combined_total_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE50', round(combined_vl_tmj_18_20, 0))
            safe_write_cell(first_sheet, 'AE51', round(combined_pl_tmj_18_20, 0))
            
            # Calculate mean speed from bin data
            def calculate_mean_speed(direction_filter, vehicle_filter):
                """Calculate mean speed from speed bin distribution"""
                # Speed bin centers for mean calculation
                bin_centers = [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]
                bin_counts = [0] * 12
                
                # Aggregate counts from raw_data
                if raw_data and sensor_map:
                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')
                        
                        # Filter by direction
                        if direction_filter == 'Sens 1' and sensor_dir not in ['Sens 1', '1']:
                            continue
                        if direction_filter == 'Sens 2' and sensor_dir not in ['Sens 2', '2']:
                            continue
                        if direction_filter == 'Combined' and sensor_dir not in ['Sens 1', '1', 'Sens 2', '2']:
                            continue
                        
                        # Filter by vehicle class (None means all classes)
                        if vehicle_filter and sensor_class != vehicle_filter:
                            continue
                        
                        # Sum bins for this sensor
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        for row_idx in range(start_row, end_row):
                            if row_idx < len(raw_data):
                                row_data = raw_data[row_idx]
                                for i in range(min(12, len(row_data))):
                                    bin_counts[i] += int(row_data[i]) if row_data[i] else 0
                
                # Calculate weighted mean
                total_count = sum(bin_counts)
                if total_count == 0:
                    return 0
                
                weighted_sum = sum(count * center for count, center in zip(bin_counts, bin_centers))
                mean_speed = weighted_sum / total_count
                return mean_speed
            
            # Calculate STD of speed from bin data
            def calculate_std_speed(direction_filter, vehicle_filter):
                """Calculate standard deviation of speed from speed bin distribution"""
                # Speed bin centers for STD calculation
                bin_centers = [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140]
                bin_counts = [0] * 12
                
                # Aggregate counts from raw_data
                if raw_data and sensor_map:
                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')
                        
                        # Filter by direction
                        if direction_filter == 'Sens 1' and sensor_dir not in ['Sens 1', '1']:
                            continue
                        if direction_filter == 'Sens 2' and sensor_dir not in ['Sens 2', '2']:
                            continue
                        if direction_filter == 'Combined' and sensor_dir not in ['Sens 1', '1', 'Sens 2', '2']:
                            continue
                        
                        # Filter by vehicle class (None means all classes)
                        if vehicle_filter and sensor_class != vehicle_filter:
                            continue
                        
                        # Sum bins for this sensor
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        for row_idx in range(start_row, end_row):
                            if row_idx < len(raw_data):
                                row_data = raw_data[row_idx]
                                for i in range(min(12, len(row_data))):
                                    bin_counts[i] += int(row_data[i]) if row_data[i] else 0
                
                total_count = sum(bin_counts)
                if total_count == 0:
                    return 0
                
                mean_speed = sum(count * center for count, center in zip(bin_counts, bin_centers)) / total_count
                variance = sum(count * ((center - mean_speed) ** 2) for count, center in zip(bin_counts, bin_centers)) / total_count
                return variance ** 0.5

            # Calculate number of vehicles above a threshold speed from bin data
            def calculate_count_above_speed(direction_filter, vehicle_filter, threshold_speed):
                """Calculate vehicles count above threshold speed using bin distribution"""
                if threshold_speed is None:
                    return 0

                # Speed bin boundaries (use metadata if available)
                speed_bins = meta.get('speed_bins', []) or []
                if len(speed_bins) >= 2:
                    upper_bounds = speed_bins[:12]
                else:
                    upper_bounds = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 150]
                bin_counts = [0] * 12

                # Aggregate counts from raw_data
                if raw_data and sensor_map:
                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')

                        # Filter by direction
                        if direction_filter == 'Sens 1' and sensor_dir not in ['Sens 1', '1']:
                            continue
                        if direction_filter == 'Sens 2' and sensor_dir not in ['Sens 2', '2']:
                            continue
                        if direction_filter == 'Combined' and sensor_dir not in ['Sens 1', '1', 'Sens 2', '2']:
                            continue

                        # Filter by vehicle class (None means all classes)
                        if vehicle_filter:
                            if sensor_class == 'ALL' and vehicle_filter == 'VL':
                                pass
                            elif sensor_class != vehicle_filter:
                                continue

                        # Sum bins for this sensor
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        for row_idx in range(start_row, end_row):
                            if row_idx < len(raw_data):
                                row_data = raw_data[row_idx]
                                for i in range(min(12, len(row_data))):
                                    bin_counts[i] += int(row_data[i]) if row_data[i] else 0

                total_above = 0
                for bin_upper, count in zip(upper_bounds, bin_counts):
                    if count == 0:
                        continue
                    if bin_upper > threshold_speed:
                        total_above += count

                return total_above

            def calculate_total_count(direction_filter, vehicle_filter):
                """Calculate total vehicle count from speed bin distribution"""
                bin_counts = [0] * 12

                if raw_data and sensor_map:
                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')

                        # Filter by direction
                        if direction_filter == 'Sens 1' and sensor_dir not in ['Sens 1', '1']:
                            continue
                        if direction_filter == 'Sens 2' and sensor_dir not in ['Sens 2', '2']:
                            continue
                        if direction_filter == 'Combined' and sensor_dir not in ['Sens 1', '1', 'Sens 2', '2']:
                            continue

                        # Filter by vehicle class (None means all classes)
                        if vehicle_filter:
                            if sensor_class == 'ALL' and vehicle_filter == 'VL':
                                pass
                            elif sensor_class != vehicle_filter:
                                continue

                        # Sum bins for this sensor
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        for row_idx in range(start_row, end_row):
                            if row_idx < len(raw_data):
                                row_data = raw_data[row_idx]
                                for i in range(min(12, len(row_data))):
                                    bin_counts[i] += int(row_data[i]) if row_data[i] else 0

                return sum(bin_counts)
            
            # Calculate V15 (15th percentile speed) from bin data
            def calculate_percentile_speed(direction_filter, vehicle_filter, percentile=15):
                """Calculate percentile speed from speed bin distribution"""
                # Speed bin boundaries (not centers)
                bin_boundaries = [(0, 30), (30, 40), (40, 50), (50, 60), (60, 70), (70, 80),
                                  (80, 90), (90, 100), (100, 110), (110, 120), (120, 130), (130, 150)]
                bin_counts = [0] * 12
                
                # Aggregate counts from raw_data
                if raw_data and sensor_map:
                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')
                        
                        # Filter by direction
                        if direction_filter == 'Sens 1' and sensor_dir not in ['Sens 1', '1']:
                            continue
                        if direction_filter == 'Sens 2' and sensor_dir not in ['Sens 2', '2']:
                            continue
                        if direction_filter == 'Combined' and sensor_dir not in ['Sens 1', '1', 'Sens 2', '2']:
                            continue
                        
                        # Filter by vehicle class (None means all classes)
                        if vehicle_filter and sensor_class != vehicle_filter:
                            continue
                        
                        # Sum bins for this sensor
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        for row_idx in range(start_row, end_row):
                            if row_idx < len(raw_data):
                                row_data = raw_data[row_idx]
                                for i in range(min(12, len(row_data))):
                                    bin_counts[i] += int(row_data[i]) if row_data[i] else 0
                
                # Calculate percentile using cumulative distribution
                total_count = sum(bin_counts)
                if total_count == 0:
                    return 0
                
                cumulative = 0
                target_count = total_count * (percentile / 100.0)
                
                for i, count in enumerate(bin_counts):
                    prev_cumulative = cumulative
                    cumulative += count
                    
                    if cumulative >= target_count:
                        # The target percentile falls within this bin
                        bin_lower, bin_upper = bin_boundaries[i]
                        
                        if count == 0:
                            # No vehicles in this bin, return lower boundary
                            return bin_lower
                        
                        # Calculate how far into this bin the percentile falls
                        excess = target_count - prev_cumulative
                        fraction = excess / count
                        
                        # Linear interpolation within the bin
                        percentile_speed = bin_lower + fraction * (bin_upper - bin_lower)
                        return percentile_speed
                
                # If we get here, return the upper bound of the last bin
                return bin_boundaries[-1][1]
            
            # Calculate V15 for each direction and vehicle class
            sens1_total_v15 = calculate_percentile_speed('Sens 1', None, 15)
            sens1_vl_v15 = calculate_percentile_speed('Sens 1', 'VL', 15)
            sens1_pl_v15 = calculate_percentile_speed('Sens 1', 'PL', 15)
            
            sens2_total_v15 = calculate_percentile_speed('Sens 2', None, 15)
            sens2_vl_v15 = calculate_percentile_speed('Sens 2', 'VL', 15)
            sens2_pl_v15 = calculate_percentile_speed('Sens 2', 'PL', 15)
            
            combined_total_v15 = calculate_percentile_speed('Combined', None, 15)
            combined_vl_v15 = calculate_percentile_speed('Combined', 'VL', 15)
            combined_pl_v15 = calculate_percentile_speed('Combined', 'PL', 15)
            
            # Write V15 values to first sheet (column R)
            safe_write_cell(first_sheet, 'R41', round(sens1_total_v15, 0))
            safe_write_cell(first_sheet, 'R42', round(sens1_vl_v15, 0))
            safe_write_cell(first_sheet, 'R43', round(sens1_pl_v15, 0))
            safe_write_cell(first_sheet, 'R45', round(sens2_total_v15, 0))
            safe_write_cell(first_sheet, 'R46', round(sens2_vl_v15, 0))
            safe_write_cell(first_sheet, 'R47', round(sens2_pl_v15, 0))
            safe_write_cell(first_sheet, 'R49', round(combined_total_v15, 0))
            safe_write_cell(first_sheet, 'R50', round(combined_vl_v15, 0))
            safe_write_cell(first_sheet, 'R51', round(combined_pl_v15, 0))
            
            # Calculate V50 (50th percentile/median speed)
            sens1_total_v50 = calculate_percentile_speed('Sens 1', None, 50)
            sens1_vl_v50 = calculate_percentile_speed('Sens 1', 'VL', 50)
            sens1_pl_v50 = calculate_percentile_speed('Sens 1', 'PL', 50)
            
            sens2_total_v50 = calculate_percentile_speed('Sens 2', None, 50)
            sens2_vl_v50 = calculate_percentile_speed('Sens 2', 'VL', 50)
            sens2_pl_v50 = calculate_percentile_speed('Sens 2', 'PL', 50)
            
            combined_total_v50 = calculate_percentile_speed('Combined', None, 50)
            combined_vl_v50 = calculate_percentile_speed('Combined', 'VL', 50)
            combined_pl_v50 = calculate_percentile_speed('Combined', 'PL', 50)
            
            # Calculate mean speeds for each direction and vehicle class
            sens1_total_mean = calculate_mean_speed('Sens 1', None)
            sens1_vl_mean = calculate_mean_speed('Sens 1', 'VL')
            sens1_pl_mean = calculate_mean_speed('Sens 1', 'PL')
            
            sens2_total_mean = calculate_mean_speed('Sens 2', None)
            sens2_vl_mean = calculate_mean_speed('Sens 2', 'VL')
            sens2_pl_mean = calculate_mean_speed('Sens 2', 'PL')
            
            combined_total_mean = calculate_mean_speed('Combined', None)
            combined_vl_mean = calculate_mean_speed('Combined', 'VL')
            combined_pl_mean = calculate_mean_speed('Combined', 'PL')
            
            # Write mean speed values to first sheet (column P)
            safe_write_cell(first_sheet, 'P41', round(sens1_total_mean, 0))
            safe_write_cell(first_sheet, 'P42', round(sens1_vl_mean, 0))
            safe_write_cell(first_sheet, 'P43', round(sens1_pl_mean, 0))
            safe_write_cell(first_sheet, 'P45', round(sens2_total_mean, 0))
            safe_write_cell(first_sheet, 'P46', round(sens2_vl_mean, 0))
            safe_write_cell(first_sheet, 'P47', round(sens2_pl_mean, 0))
            safe_write_cell(first_sheet, 'P49', round(combined_total_mean, 0))
            safe_write_cell(first_sheet, 'P50', round(combined_vl_mean, 0))
            safe_write_cell(first_sheet, 'P51', round(combined_pl_mean, 0))

            # Calculate STD of speed for each direction and vehicle class
            sens1_total_std = calculate_std_speed('Sens 1', None)
            sens1_vl_std = calculate_std_speed('Sens 1', 'VL')
            sens1_pl_std = calculate_std_speed('Sens 1', 'PL')
            
            sens2_total_std = calculate_std_speed('Sens 2', None)
            sens2_vl_std = calculate_std_speed('Sens 2', 'VL')
            sens2_pl_std = calculate_std_speed('Sens 2', 'PL')
            
            combined_total_std = calculate_std_speed('Combined', None)
            combined_vl_std = calculate_std_speed('Combined', 'VL')
            combined_pl_std = calculate_std_speed('Combined', 'PL')
            
            # Write STD of speed values to first sheet (column X)
            safe_write_cell(first_sheet, 'X41', round(sens1_total_std, 0))
            safe_write_cell(first_sheet, 'X42', round(sens1_vl_std, 0))
            safe_write_cell(first_sheet, 'X43', round(sens1_pl_std, 0))
            safe_write_cell(first_sheet, 'X45', round(sens2_total_std, 0))
            safe_write_cell(first_sheet, 'X46', round(sens2_vl_std, 0))
            safe_write_cell(first_sheet, 'X47', round(sens2_pl_std, 0))
            safe_write_cell(first_sheet, 'X49', round(combined_total_std, 0))
            safe_write_cell(first_sheet, 'X50', round(combined_vl_std, 0))
            safe_write_cell(first_sheet, 'X51', round(combined_pl_std, 0))

            # Column Z: vehicles with speed greater than T36
            if self.max_speed_authorized is not None:
                threshold_speed = self.max_speed_authorized
            else:
                threshold_speed = first_sheet['T36'].value
                try:
                    threshold_speed = float(str(threshold_speed).replace(',', '.'))
                except (TypeError, ValueError):
                    threshold_speed = None

            sens1_total_above = calculate_count_above_speed('Sens 1', None, threshold_speed)
            sens1_vl_above = calculate_count_above_speed('Sens 1', 'VL', threshold_speed)
            sens1_pl_above = calculate_count_above_speed('Sens 1', 'PL', threshold_speed)

            sens2_total_above = calculate_count_above_speed('Sens 2', None, threshold_speed)
            sens2_vl_above = calculate_count_above_speed('Sens 2', 'VL', threshold_speed)
            sens2_pl_above = calculate_count_above_speed('Sens 2', 'PL', threshold_speed)

            combined_total_above = calculate_count_above_speed('Combined', None, threshold_speed)
            combined_vl_above = calculate_count_above_speed('Combined', 'VL', threshold_speed)
            combined_pl_above = calculate_count_above_speed('Combined', 'PL', threshold_speed)

            sens1_total_all = calculate_total_count('Sens 1', None)
            sens1_vl_all = calculate_total_count('Sens 1', 'VL')
            sens1_pl_all = calculate_total_count('Sens 1', 'PL')

            sens2_total_all = calculate_total_count('Sens 2', None)
            sens2_vl_all = calculate_total_count('Sens 2', 'VL')
            sens2_pl_all = calculate_total_count('Sens 2', 'PL')

            combined_total_all = calculate_total_count('Combined', None)
            combined_vl_all = calculate_total_count('Combined', 'VL')
            combined_pl_all = calculate_total_count('Combined', 'PL')

            def _pct_daily(above_total, tmj_value):
                if not tmj_value:
                    return 0
                return (above_total / num_days) / tmj_value

            safe_write_cell(first_sheet, 'Z41', round(sens1_total_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z42', round(sens1_vl_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z43', round(sens1_pl_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z45', round(sens2_total_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z46', round(sens2_vl_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z47', round(sens2_pl_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z49', round(combined_total_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z50', round(combined_vl_above / num_days, 0))
            safe_write_cell(first_sheet, 'Z51', round(combined_pl_above / num_days, 0))

            # Column AB: percentage of vehicles above threshold speed
            safe_write_cell(first_sheet, 'AB41', round(_pct_daily(sens1_total_above, sens1_total_tmj), 4))
            safe_write_cell(first_sheet, 'AB42', round(_pct_daily(sens1_vl_above, sens1_vl_tmj), 4))
            safe_write_cell(first_sheet, 'AB43', round(_pct_daily(sens1_pl_above, sens1_pl_tmj), 4))
            safe_write_cell(first_sheet, 'AB45', round(_pct_daily(sens2_total_above, sens2_total_tmj), 4))
            safe_write_cell(first_sheet, 'AB46', round(_pct_daily(sens2_vl_above, sens2_vl_tmj), 4))
            safe_write_cell(first_sheet, 'AB47', round(_pct_daily(sens2_pl_above, sens2_pl_tmj), 4))
            safe_write_cell(first_sheet, 'AB49', round(_pct_daily(combined_total_above, combined_total_tmj), 4))
            safe_write_cell(first_sheet, 'AB50', round(_pct_daily(combined_vl_above, combined_vl_tmj), 4))
            safe_write_cell(first_sheet, 'AB51', round(_pct_daily(combined_pl_above, combined_pl_tmj), 4))
            
            # Write V50 values to first sheet (column T)
            safe_write_cell(first_sheet, 'T41', round(sens1_total_v50, 0))
            safe_write_cell(first_sheet, 'T42', round(sens1_vl_v50, 0))
            safe_write_cell(first_sheet, 'T43', round(sens1_pl_v50, 0))
            safe_write_cell(first_sheet, 'T45', round(sens2_total_v50, 0))
            safe_write_cell(first_sheet, 'T46', round(sens2_vl_v50, 0))
            safe_write_cell(first_sheet, 'T47', round(sens2_pl_v50, 0))
            safe_write_cell(first_sheet, 'T49', round(combined_total_v50, 0))
            safe_write_cell(first_sheet, 'T50', round(combined_vl_v50, 0))
            safe_write_cell(first_sheet, 'T51', round(combined_pl_v50, 0))
            
            # Calculate V85 (85th percentile speed)
            sens1_total_v85 = calculate_percentile_speed('Sens 1', None, 85)
            sens1_vl_v85 = calculate_percentile_speed('Sens 1', 'VL', 85)
            sens1_pl_v85 = calculate_percentile_speed('Sens 1', 'PL', 85)
            
            sens2_total_v85 = calculate_percentile_speed('Sens 2', None, 85)
            sens2_vl_v85 = calculate_percentile_speed('Sens 2', 'VL', 85)
            sens2_pl_v85 = calculate_percentile_speed('Sens 2', 'PL', 85)
            
            combined_total_v85 = calculate_percentile_speed('Combined', None, 85)
            combined_vl_v85 = calculate_percentile_speed('Combined', 'VL', 85)
            combined_pl_v85 = calculate_percentile_speed('Combined', 'PL', 85)
            
            # Write V85 values to first sheet (column V)
            safe_write_cell(first_sheet, 'V41', round(sens1_total_v85, 0))
            safe_write_cell(first_sheet, 'V42', round(sens1_vl_v85, 0))
            safe_write_cell(first_sheet, 'V43', round(sens1_pl_v85, 0))
            safe_write_cell(first_sheet, 'V45', round(sens2_total_v85, 0))
            safe_write_cell(first_sheet, 'V46', round(sens2_vl_v85, 0))
            safe_write_cell(first_sheet, 'V47', round(sens2_pl_v85, 0))
            safe_write_cell(first_sheet, 'V49', round(combined_total_v85, 0))
            safe_write_cell(first_sheet, 'V50', round(combined_vl_v85, 0))
            safe_write_cell(first_sheet, 'V51', round(combined_pl_v85, 0))
            
            for sheet_name in ['Sens1', 'Sens2', 'Sens3', 'Sens 3 (S1+S2)']:
                if sheet_name not in wb.sheetnames:
                    continue
                
                ws = wb[sheet_name]
                
                # Find sensors for this direction
                is_combined = sheet_name in ['Sens3', 'Sens 3 (S1+S2)']

                if sheet_name == 'Sens1':
                    dir_labels = ['Sens 1', '1']
                elif sheet_name == 'Sens2':
                    dir_labels = ['Sens 2', '2']
                else:
                    dir_labels = ['Sens 1', '1', 'Sens 2', '2']
                direction_sensors = [sid for sid, sinfo in sensor_map.items() if sinfo.get('direction') in dir_labels]
                
                if not direction_sensors:
                    continue
                
                # Group sensors by vehicle class for this direction
                vl_sensors = [sid for sid in direction_sensors if sensor_map.get(sid, {}).get('class') == 'VL']
                pl_sensors = [sid for sid in direction_sensors if sensor_map.get(sid, {}).get('class') == 'PL']
                
                # Get base timestamp
                from datetime import datetime, timedelta
                if meta.get('year'):
                    base_time = datetime(
                        meta['year'], meta['month'], meta['day'],
                        meta.get('start_hour', 0), meta.get('start_minute', 0)
                    )
                else:
                    base_time = datetime.now()

                # Hourly mean counts per bin (rows 11-34), VL/PL per bin
                hourly_vl = [[0] * 12 for _ in range(24)]
                hourly_pl = [[0] * 12 for _ in range(24)]

                for sensor_id in range(num_sensors):
                    sensor_info = sensor_map.get(sensor_id, {})
                    sensor_dir = sensor_info.get('direction', '')
                    sensor_class = sensor_info.get('class', '')

                    if sensor_dir not in dir_labels:
                        continue

                    start_row = sensor_id * rows_per_block
                    end_row = min(start_row + rows_per_block, len(raw_data))
                    if start_row >= len(raw_data):
                        continue

                    block = raw_data[start_row:end_row]
                    for idx, row_vals in enumerate(block):
                        timestamp = base_time + timedelta(minutes=interval_minutes * idx)
                        hour = timestamp.hour

                        for i in range(12):
                            val = int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                            if sensor_class == 'PL':
                                hourly_pl[hour][i] += val
                            else:
                                # Treat 'VL' and 'ALL' as VL for bin counts
                                hourly_vl[hour][i] += val

                # Write hourly mean values (divide by num_days)
                for hour in range(24):
                    row_idx = 11 + hour
                    col_idx = 3  # Column C
                    for bin_idx in range(12):
                        vl_val = hourly_vl[hour][bin_idx] / num_days
                        pl_val = hourly_pl[hour][bin_idx] / num_days
                        safe_write_cell_rc(ws, row_idx, col_idx, round(vl_val, 0))
                        col_idx += 1
                        safe_write_cell_rc(ws, row_idx, col_idx, round(pl_val, 0))
                        col_idx += 1

                # Build additional pages for each date (only if data exists for that day)
                if sheet_name == 'Sens1':
                    dir_labels = ['Sens 1', '1']
                elif sheet_name == 'Sens2':
                    dir_labels = ['Sens 2', '2']
                else:
                    dir_labels = ['Sens 1', '1', 'Sens 2', '2']

                def _get_active_dates(labels):
                    day_totals = {}
                    for sensor_id in range(num_sensors):
                        sinfo = sensor_map.get(sensor_id, {})
                        if sinfo.get('direction') not in labels:
                            continue
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        if start_row >= len(raw_data):
                            continue
                        block = raw_data[start_row:end_row]
                        for idx_row, row_vals in enumerate(block):
                            total = 0
                            for i in range(12):
                                total += int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                            if total == 0:
                                continue
                            ts = base_time + timedelta(minutes=interval_minutes * idx_row)
                            day_totals[ts.date()] = day_totals.get(ts.date(), 0) + total
                    return sorted([d for d, t in day_totals.items() if t > 0])

                date_list = _get_active_dates(dir_labels)

                last_chart_row = -1
                for ch in list(ws._charts):
                    try:
                        if ch.anchor is not None and ch.anchor._from.row > last_chart_row:
                            last_chart_row = ch.anchor._from.row
                    except Exception:
                        continue
                last_chart_page = (last_chart_row // 56) + 1 if last_chart_row >= 0 else 1
                base_page_start = 1 + 56 * (last_chart_page - 1)
                base_page_end = 56 * last_chart_page
                base_page_charts = []
                for ch in list(ws._charts):
                    try:
                        if ch.anchor is not None and ch.anchor._from.row >= (base_page_start - 1) and ch.anchor._from.row < base_page_end:
                            base_page_charts.append(ch)
                    except Exception:
                        continue

                def _remove_page_charts(page_start, page_end):
                    kept = []
                    for ch in list(ws._charts):
                        try:
                            row = ch.anchor._from.row if ch.anchor and ch.anchor._from else -1
                        except Exception:
                            row = -1
                        if row < page_start - 1 or row >= page_end:
                            kept.append(ch)
                    ws._charts = kept

                def _shift_formula_rows(formula, offset):
                    import re
                    if not formula:
                        return formula
                    def repl(match):
                        col = match.group(1)
                        row_dollar = match.group(2) or ""
                        row = int(match.group(3))
                        return f"{col}{row_dollar}{row + offset}"
                    return re.sub(r"(\$?[A-Z]{1,3})(\$?)(\d+)", repl, formula)

                def _clone_chart_with_offset(chart, offset):
                    from copy import deepcopy
                    ch = deepcopy(chart)
                    # Explicitly preserve chart styling
                    try:
                        ch.style = chart.style
                    except Exception:
                        pass
                    try:
                        ch.graphicalProperties = deepcopy(chart.graphicalProperties)
                    except Exception:
                        pass
                    try:
                        ch.title = deepcopy(chart.title)
                    except Exception:
                        pass
                    try:
                        ch.legend = deepcopy(chart.legend)
                    except Exception:
                        pass
                    try:
                        ch.x_axis = deepcopy(chart.x_axis)
                        ch.y_axis = deepcopy(chart.y_axis)
                    except Exception:
                        pass
                    try:
                        for i, s in enumerate(ch.series):
                            if i < len(chart.series):
                                s.graphicalProperties = deepcopy(chart.series[i].graphicalProperties)
                                s.marker = deepcopy(chart.series[i].marker)
                                s.dLbls = deepcopy(chart.series[i].dLbls)
                    except Exception:
                        pass
                    if (getattr(ch, 'anchor', None) is None) and getattr(chart, 'anchor', None) is not None:
                        try:
                            ch.anchor = deepcopy(chart.anchor)
                        except Exception:
                            pass
                    if hasattr(ch, 'anchor') and ch.anchor is not None:
                        try:
                            ch.anchor._from.row += offset
                            ch.anchor.to.row += offset
                        except Exception:
                            pass
                    for s in ch.series:
                        val = getattr(s, 'val', None)
                        cat = getattr(s, 'cat', None)
                        if val is not None and getattr(val, 'numRef', None) is not None:
                            val.numRef.f = _shift_formula_rows(val.numRef.f, offset)
                        if cat is not None:
                            if getattr(cat, 'numRef', None) is not None:
                                cat.numRef.f = _shift_formula_rows(cat.numRef.f, offset)
                            if getattr(cat, 'strRef', None) is not None:
                                cat.strRef.f = _shift_formula_rows(cat.strRef.f, offset)
                    return ch

                def set_hour_formulas(offset):
                    bins_row = 8 + offset
                    for hour in range(24):
                        r = 11 + offset + hour
                        aa = (
                            f"=IF(AC{r}=0,\"\",(C{r}*(C${bins_row}+D${bins_row})/2+E{r}*(E${bins_row}+F${bins_row})/2+"
                            f"G{r}*(G${bins_row}+H${bins_row})/2+I{r}*(I${bins_row}+J${bins_row})/2+K{r}*(K${bins_row}+L${bins_row})/2+"
                            f"M{r}*(M${bins_row}+N${bins_row})/2+O{r}*(O${bins_row}+P${bins_row})/2+Q{r}*(Q${bins_row}+R${bins_row})/2+"
                            f"S{r}*(S${bins_row}+T${bins_row})/2+U{r}*(U${bins_row}+V${bins_row})/2+W{r}*(W${bins_row}+X${bins_row})/2+"
                            f"Y{r}*(Y${bins_row}+Z${bins_row})/2)/AC{r})"
                        )
                        ab = (
                            f"=IF(AD{r}=0,\"\",(D{r}*(D${bins_row}+C${bins_row})/2+F{r}*(F${bins_row}+E${bins_row})/2+"
                            f"H{r}*(H${bins_row}+G${bins_row})/2+J{r}*(J${bins_row}+I${bins_row})/2+L{r}*(L${bins_row}+K${bins_row})/2+"
                            f"N{r}*(N${bins_row}+M${bins_row})/2+P{r}*(P${bins_row}+O${bins_row})/2+R{r}*(R${bins_row}+Q${bins_row})/2+"
                            f"T{r}*(T${bins_row}+S${bins_row})/2+V{r}*(V${bins_row}+U${bins_row})/2+X{r}*(X${bins_row}+W${bins_row})/2+"
                            f"Z{r}*(Z${bins_row}+Y${bins_row})/2)/AD{r})"
                        )
                        ac = f"=SUM(C{r},E{r},G{r},I{r},K{r},M{r},O{r},Q{r},S{r},U{r},W{r},Y{r})"
                        ad = f"=SUM(D{r},F{r},H{r},J{r},L{r},N{r},P{r},R{r},T{r},V{r},X{r},Z{r})"
                        ae = f"=AC{r}+AD{r}"
                        safe_write_cell_rc(ws, r, 27, aa)
                        safe_write_cell_rc(ws, r, 28, ab)
                        safe_write_cell_rc(ws, r, 29, ac)
                        safe_write_cell_rc(ws, r, 30, ad)
                        safe_write_cell_rc(ws, r, 31, ae)

                def set_totals_and_cumulatives(offset):
                    total_row = 36 + offset
                    percent_row = 37 + offset
                    cumul_vl_row = 38 + offset
                    cumul_pl_row = 39 + offset
                    cumul_tv_row = 40 + offset
                    bins_row = 8 + offset
                    for col_letter, col_idx in zip(
                        ['C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'],
                        range(3, 27)
                    ):
                        safe_write_cell_rc(ws, total_row, col_idx, f"=SUM({col_letter}{11+offset}:{col_letter}{34+offset})")

                    aa_total = (
                        f"=IF(AC{total_row}=0,\"\",(C{total_row}*(C${bins_row}+D${bins_row})/2+E{total_row}*(E${bins_row}+F${bins_row})/2+"
                        f"G{total_row}*(G${bins_row}+H${bins_row})/2+I{total_row}*(I${bins_row}+J${bins_row})/2+K{total_row}*(K${bins_row}+L${bins_row})/2+"
                        f"M{total_row}*(M${bins_row}+N${bins_row})/2+O{total_row}*(O${bins_row}+P${bins_row})/2+Q{total_row}*(Q${bins_row}+R${bins_row})/2+"
                        f"S{total_row}*(S${bins_row}+T${bins_row})/2+U{total_row}*(U${bins_row}+V${bins_row})/2+W{total_row}*(W${bins_row}+X${bins_row})/2+"
                        f"Y{total_row}*(Y${bins_row}+Z${bins_row})/2)/AC{total_row})"
                    )
                    ab_total = (
                        f"=IF(AD{total_row}=0,\"\",(D{total_row}*(D${bins_row}+C${bins_row})/2+F{total_row}*(F${bins_row}+E${bins_row})/2+"
                        f"H{total_row}*(H${bins_row}+G${bins_row})/2+J{total_row}*(J${bins_row}+I${bins_row})/2+L{total_row}*(L${bins_row}+K${bins_row})/2+"
                        f"N{total_row}*(N${bins_row}+M${bins_row})/2+P{total_row}*(P${bins_row}+O${bins_row})/2+R{total_row}*(R${bins_row}+Q${bins_row})/2+"
                        f"T{total_row}*(T${bins_row}+S${bins_row})/2+V{total_row}*(V${bins_row}+U${bins_row})/2+X{total_row}*(X${bins_row}+W${bins_row})/2+"
                        f"Z{total_row}*(Z${bins_row}+Y${bins_row})/2)/AD{total_row})"
                    )
                    safe_write_cell_rc(ws, total_row, 27, aa_total)
                    safe_write_cell_rc(ws, total_row, 28, ab_total)
                    safe_write_cell_rc(ws, total_row, 29, f"=SUM(AC{11+offset}:AC{34+offset})")
                    safe_write_cell_rc(ws, total_row, 30, f"=SUM(AD{11+offset}:AD{34+offset})")
                    safe_write_cell_rc(ws, total_row, 31, f"=SUM(AE{11+offset}:AE{34+offset})")

                    safe_write_cell_rc(ws, percent_row, 2, "%")
                    for col_letter, col_idx in zip(
                        ['C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'],
                        range(3, 27)
                    ):
                        safe_write_cell_rc(ws, percent_row, col_idx, f"=100*{col_letter}{total_row}/$AE{total_row}")
                    safe_write_cell_rc(ws, percent_row, 29, f"=AC{total_row}/AE{total_row}")
                    safe_write_cell_rc(ws, percent_row, 30, f"=AD{total_row}/AE{total_row}")

                    safe_write_cell_rc(ws, cumul_vl_row, 2, "% cumul VL")
                    safe_write_cell_rc(ws, cumul_vl_row, 3, f"=100*C{total_row}/$AC{total_row}")
                    for col_letter, prev_letter, col_idx in [
                        ('E','C',5), ('G','E',7), ('I','G',9), ('K','I',11), ('M','K',13), ('O','M',15),
                        ('Q','O',17), ('S','Q',19), ('U','S',21), ('W','U',23), ('Y','W',25)
                    ]:
                        safe_write_cell_rc(ws, cumul_vl_row, col_idx, f"=100*{col_letter}{total_row}/$AC{total_row}+{prev_letter}{cumul_vl_row}")

                    safe_write_cell_rc(ws, cumul_pl_row, 1, "% cumul PL")
                    safe_write_cell_rc(ws, cumul_pl_row, 4, f"=100*D{total_row}/$AD{total_row}")
                    for col_letter, prev_letter, col_idx in [
                        ('F','D',6), ('H','F',8), ('J','H',10), ('L','J',12), ('N','L',14), ('P','N',16),
                        ('R','P',18), ('T','R',20), ('V','T',22), ('X','V',24), ('Z','X',26)
                    ]:
                        safe_write_cell_rc(ws, cumul_pl_row, col_idx, f"=100*{col_letter}{total_row}/$AD{total_row}+{prev_letter}{cumul_pl_row}")

                    safe_write_cell_rc(ws, cumul_tv_row, 2, "% cumul TV")
                    for col_letter_vl, col_letter_pl, col_idx in [
                        ('C','D',3), ('E','F',5), ('G','H',7), ('I','J',9), ('K','L',11), ('M','N',13),
                        ('O','P',15), ('Q','R',17), ('S','T',19), ('U','V',21), ('W','X',23), ('Y','Z',25)
                    ]:
                        safe_write_cell_rc(ws, cumul_tv_row, col_idx, f"=({col_letter_vl}{cumul_vl_row}*$AC{total_row}+{col_letter_pl}{cumul_pl_row}*$AD{total_row})/$AE{total_row}")

                def set_summary_rows(offset):
                    base_row = 43 + offset
                    total_row = 36 + offset
                    vl_row = 48 + offset
                    pl_row = 50 + offset
                    tv_row = 46 + offset
                    helper_row = 47 + offset

                    safe_write_cell_rc(ws, tv_row, 30, f"=AE{total_row}")
                    safe_write_cell_rc(ws, tv_row, 31, f"=AD{tv_row}/AH{base_row}")
                    safe_write_cell_rc(ws, tv_row, 32, f"=(AF{vl_row}*AD{vl_row}+AF{pl_row}*AD{pl_row})/AD{tv_row}")

                    safe_write_cell_rc(ws, tv_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row})+((0.15*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AG{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AG{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row})+((0.5*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AH{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AH{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row})+((0.85*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AI{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AI{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 36, f"=AJ{vl_row}+AJ{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 37, f"=AK{vl_row}+AK{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 38, f"=AL{vl_row}+AL{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 39, f"=AM{vl_row}+AM{pl_row}")

                    safe_write_cell_rc(ws, vl_row, 30, f"=AC{total_row}")
                    safe_write_cell_rc(ws, vl_row, 31, f"=AD{vl_row}/AH{base_row}")
                    safe_write_cell_rc(ws, vl_row, 32, f"=AA{total_row}")
                    safe_write_cell_rc(ws, vl_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1})+((0.15*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AG{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1})+((0.5*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AH{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1})+((0.85*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AI{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 36, f"=SUMIFS(C{total_row}:Z{total_row},C{10+offset}:Z{10+offset},\"VL\",D{8+offset}:AA{8+offset},\">\"&AD{base_row})")
                    safe_write_cell_rc(ws, vl_row, 37, f"=SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{52+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{52+offset})")
                    safe_write_cell_rc(ws, vl_row, 38, f"=SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{53+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{53+offset})")
                    safe_write_cell_rc(ws, vl_row, 39, f"=IF(AM{54+offset}=AK{54+offset},0,IF($AK${54+offset}<$AM${54+offset},SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset}),SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset})+SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset})))")

                    safe_write_cell_rc(ws, pl_row, 30, f"=AD{total_row}")
                    safe_write_cell_rc(ws, pl_row, 31, f"=AD{pl_row}/AH{base_row}")
                    safe_write_cell_rc(ws, pl_row, 32, f"=AB{total_row}")
                    safe_write_cell_rc(ws, pl_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1}-1)+((0.15*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AG{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1}-1)+((0.5*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AH{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1}-1)+((0.85*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AI{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 36, f"=SUMIFS(C{total_row}:Z{total_row},C{10+offset}:Z{10+offset},\"PL\",C{8+offset}:Z{8+offset},\">\"&AD{base_row})")
                    safe_write_cell_rc(ws, pl_row, 37, f"=SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{52+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{52+offset})")
                    safe_write_cell_rc(ws, pl_row, 38, f"=SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{53+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{53+offset})")
                    safe_write_cell_rc(ws, pl_row, 39, f"=IF(AM{54+offset}=AK{54+offset},0,IF($AK${54+offset}<$AM${54+offset},SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset}),SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset})+SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset})))")

                base_page8_start = 1 + 56 * 7
                base_page8_end = 56 * 8
                base_page8_charts = []
                last_chart_row = -1
                for ch in list(ws._charts):
                    try:
                        if ch.anchor is not None and ch.anchor._from.row >= (base_page8_start - 1) and ch.anchor._from.row < base_page8_end:
                            base_page8_charts.append(ch)
                        if ch.anchor is not None and ch.anchor._from.row > last_chart_row:
                            last_chart_row = ch.anchor._from.row
                    except Exception:
                        continue
                last_chart_page = (last_chart_row // 56) + 1 if last_chart_row >= 0 else 1

                def _shift_formula_rows(formula, offset):
                    import re
                    if not formula:
                        return formula
                    def repl(match):
                        col = match.group(1)
                        row_dollar = match.group(2) or ""
                        row = int(match.group(3))
                        return f"{col}{row_dollar}{row + offset}"
                    return re.sub(r"(\$?[A-Z]{1,3})(\$?)(\d+)", repl, formula)

                def _clone_chart_with_offset(chart, offset):
                    from copy import deepcopy
                    ch = deepcopy(chart)
                    try:
                        ch.style = chart.style
                    except Exception:
                        pass
                    try:
                        ch.graphicalProperties = deepcopy(chart.graphicalProperties)
                    except Exception:
                        pass
                    try:
                        ch.title = deepcopy(chart.title)
                    except Exception:
                        pass
                    try:
                        ch.legend = deepcopy(chart.legend)
                    except Exception:
                        pass
                    try:
                        ch.x_axis = deepcopy(chart.x_axis)
                        ch.y_axis = deepcopy(chart.y_axis)
                    except Exception:
                        pass
                    try:
                        for i, s in enumerate(ch.series):
                            if i < len(chart.series):
                                s.graphicalProperties = deepcopy(chart.series[i].graphicalProperties)
                                s.marker = deepcopy(chart.series[i].marker)
                                s.dLbls = deepcopy(chart.series[i].dLbls)
                    except Exception:
                        pass
                    if (getattr(ch, 'anchor', None) is None) and getattr(chart, 'anchor', None) is not None:
                        try:
                            ch.anchor = deepcopy(chart.anchor)
                        except Exception:
                            pass
                    if hasattr(ch, 'anchor') and ch.anchor is not None:
                        try:
                            ch.anchor._from.row += offset
                            ch.anchor.to.row += offset
                        except Exception:
                            pass
                    for s in ch.series:
                        val = getattr(s, 'val', None)
                        cat = getattr(s, 'cat', None)
                        if val is not None and getattr(val, 'numRef', None) is not None:
                            val.numRef.f = _shift_formula_rows(val.numRef.f, offset)
                        if cat is not None:
                            if getattr(cat, 'numRef', None) is not None:
                                cat.numRef.f = _shift_formula_rows(cat.numRef.f, offset)
                            if getattr(cat, 'strRef', None) is not None:
                                cat.strRef.f = _shift_formula_rows(cat.strRef.f, offset)
                    return ch

                base_page1_charts = []
                base_page8_charts = []
                last_chart_row = -1
                for ch in list(ws._charts):
                    try:
                        if ch.anchor is not None and ch.anchor._from.row < 56:
                            base_page1_charts.append(ch)
                        if ch.anchor is not None and ch.anchor._from.row >= (base_page8_start - 1) and ch.anchor._from.row < base_page8_end:
                            base_page8_charts.append(ch)
                        if ch.anchor is not None and ch.anchor._from.row > last_chart_row:
                            last_chart_row = ch.anchor._from.row
                    except Exception:
                        continue

                last_chart_page = (last_chart_row // 56) + 1 if last_chart_row >= 0 else 1
                if not base_page1_charts and ws._charts:
                    base_page1_charts = list(ws._charts)
                if not base_page8_charts:
                    base_page8_charts = base_page1_charts
                template_pages = (ws.max_row + 55) // 56

                def _trim_pages(target_ws, keep_pages):
                    from openpyxl.utils import get_column_letter
                    max_row_keep = 56 * keep_pages
                    kept_charts = []
                    for ch in list(target_ws._charts):
                        try:
                            row = ch.anchor._from.row if ch.anchor and ch.anchor._from else 0
                        except Exception:
                            row = 0
                        if row < max_row_keep:
                            kept_charts.append(ch)
                    target_ws._charts = kept_charts

                    if target_ws.max_row > max_row_keep:
                        target_ws.delete_rows(max_row_keep + 1, target_ws.max_row - max_row_keep)

                    for mr in list(target_ws.merged_cells.ranges):
                        if mr.min_row > max_row_keep:
                            target_ws.merged_cells.ranges.remove(mr)
                        elif mr.max_row > max_row_keep:
                            target_ws.merged_cells.ranges.remove(mr)
                            new_max = max_row_keep
                            new_range = f"{get_column_letter(mr.min_col)}{mr.min_row}:{get_column_letter(mr.max_col)}{new_max}"
                            target_ws.merge_cells(new_range)

                    last_col = get_column_letter(target_ws.max_column)
                    target_ws.print_area = f"A1:{last_col}{max_row_keep}"
                    try:
                        target_ws.row_breaks = []
                        target_ws.col_breaks = []
                    except Exception:
                        pass

                for idx, date_val in enumerate(date_list):
                    offset = 56 * (idx + 1)
                    # Only copy page layout if the template doesn't already contain this page
                    if (idx + 1) >= template_pages:
                        if idx >= 7:
                            delta = offset - (56 * 7)
                            copy_range_with_styles(ws, base_page8_start, base_page8_end, 1, 40, delta)
                        else:
                            copy_range_with_styles(ws, 1, 56, 1, 40, offset)

                    if idx >= 7:
                        delta = offset - (56 * 7)
                        for ch in (base_page8_charts or base_page1_charts):
                            try:
                                ws.add_chart(_clone_chart_with_offset(ch, delta))
                            except Exception:
                                continue

                    weekday_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][date_val.weekday()]
                    date_label = f"{date_val.strftime('%d/%m/%Y')} {weekday_fr}"
                    safe_write_cell_rc(ws, 58 + offset, 7, date_label)
                    for r in range(1 + offset, 57 + offset):
                        for c in range(1, 41):
                            cell = ws.cell(row=r, column=c)
                            if isinstance(cell.value, str) and 'MOYENNE DE LA PERIODE DE RELEVE' in cell.value:
                                safe_write_cell_rc(ws, r, c, date_label)

                    if is_combined and 'Sens1' in wb.sheetnames and 'Sens2' in wb.sheetnames:
                        sens1_sheet = wb['Sens1']
                        sens2_sheet = wb['Sens2']
                        sens1_label = sens1_sheet.cell(row=58 + offset, column=7).value
                        if sens1_label:
                            safe_write_cell_rc(ws, 58 + offset, 7, sens1_label)

                        for hour in range(24):
                            row_idx = 11 + offset + hour
                            for col_idx in range(3, 27):
                                v1 = sens1_sheet.cell(row=row_idx, column=col_idx).value or 0
                                v2 = sens2_sheet.cell(row=row_idx, column=col_idx).value or 0
                                safe_write_cell_rc(ws, row_idx, col_idx, float(v1) + float(v2))
                    else:
                        daily_vl = [[0] * 12 for _ in range(24)]
                        daily_pl = [[0] * 12 for _ in range(24)]

                        for sensor_id in range(num_sensors):
                            sensor_info = sensor_map.get(sensor_id, {})
                            sensor_dir = sensor_info.get('direction', '')
                            sensor_class = sensor_info.get('class', '')

                            if sensor_dir not in dir_labels:
                                continue

                            start_row = sensor_id * rows_per_block
                            end_row = min(start_row + rows_per_block, len(raw_data))
                            if start_row >= len(raw_data):
                                continue

                            block = raw_data[start_row:end_row]
                            for idx_row, row_vals in enumerate(block):
                                timestamp = base_time + timedelta(minutes=interval_minutes * idx_row)
                                if timestamp.date() != date_val:
                                    continue
                                hour = timestamp.hour
                                for i in range(12):
                                    val = int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                                    if sensor_class == 'PL':
                                        daily_pl[hour][i] += val
                                    else:
                                        daily_vl[hour][i] += val

                        for hour in range(24):
                            row_idx = 11 + offset + hour
                            col_idx = 3
                            for bin_idx in range(12):
                                safe_write_cell_rc(ws, row_idx, col_idx, round(daily_vl[hour][bin_idx], 0))
                                col_idx += 1
                                safe_write_cell_rc(ws, row_idx, col_idx, round(daily_pl[hour][bin_idx], 0))
                                col_idx += 1

                    set_hour_formulas(offset)
                    set_totals_and_cumulatives(offset)
                    set_summary_rows(offset)

                    if idx >= 1:
                        page_start = 1 + offset
                        page_end = 56 + offset
                        _remove_page_charts(page_start, page_end)
                        for ch in base_page_charts:
                            try:
                                if hasattr(ch, 'anchor') and ch.anchor is not None and ch.anchor._from.row < 56:
                                    ws.add_chart(_clone_chart_with_offset(ch, offset))
                            except Exception:
                                continue

                def _trim_pages(target_ws, keep_pages):
                    from openpyxl.utils import get_column_letter
                    max_row_keep = 56 * keep_pages
                    kept_charts = []
                    for ch in list(target_ws._charts):
                        try:
                            row = ch.anchor._from.row if ch.anchor and ch.anchor._from else 0
                        except Exception:
                            row = 0
                        if row < max_row_keep:
                            kept_charts.append(ch)
                    target_ws._charts = kept_charts

                    if target_ws.max_row > max_row_keep:
                        target_ws.delete_rows(max_row_keep + 1, target_ws.max_row - max_row_keep)

                    for mr in list(target_ws.merged_cells.ranges):
                        if mr.min_row > max_row_keep:
                            target_ws.merged_cells.ranges.remove(mr)
                        elif mr.max_row > max_row_keep:
                            target_ws.merged_cells.ranges.remove(mr)
                            new_max = max_row_keep
                            new_range = f"{get_column_letter(mr.min_col)}{mr.min_row}:{get_column_letter(mr.max_col)}{new_max}"
                            target_ws.merge_cells(new_range)

                    last_col = get_column_letter(target_ws.max_column)
                    target_ws.print_area = f"A1:{last_col}{max_row_keep}"
                    try:
                        target_ws.row_breaks = []
                        target_ws.col_breaks = []
                    except Exception:
                        pass

                # Rebuild conditional formatting ranges for hourly blocks with page stride
                try:
                    from copy import copy as _copy
                    base_rules = None
                    for rng, rules in list(ws.conditional_formatting._cf_rules.items()):
                        if str(rng) == "B11:AE34":
                            base_rules = [_copy(r) for r in rules]
                        # Clear existing rules (template has fixed 56-row stride)
                    ws.conditional_formatting._cf_rules = {}
                    if base_rules:
                        page_stride = 56
                        for page_idx in range(0, len(date_list) + 1):
                            offset = page_stride * page_idx
                            target = f"B{11+offset}:AE{34+offset}"
                            for rule in base_rules:
                                ws.conditional_formatting.add(target, _copy(rule))
                except Exception:
                    pass

                keep_pages = max(1, 1 + len(date_list))
                _trim_pages(ws, keep_pages)
                
                # Page sheets (Sens1/Sens2) do not write raw data blocks here

            # Populate raw data in sheets "Sens 1", "Sens 2", and "Sens 3" for Graphiques
            for sheet_name in ['Sens 1', 'Sens 2', 'Sens 3', 'Sens 3 (S1+S2)']:
                if sheet_name not in wb.sheetnames:
                    continue

                ws = wb[sheet_name]

                # Get base timestamp
                from datetime import datetime, timedelta
                if meta.get('year'):
                    base_time = datetime(
                        meta['year'], meta['month'], meta['day'],
                        meta.get('start_hour', 0), meta.get('start_minute', 0)
                    )
                else:
                    base_time = datetime.now()

                # Find sensors for this direction
                if sheet_name == 'Sens 1':
                    dir_labels = ['Sens 1', '1']
                elif sheet_name == 'Sens 2':
                    dir_labels = ['Sens 2', '2']
                else:
                    dir_labels = ['Sens 1', '1', 'Sens 2', '2']
                direction_sensors = [sid for sid, sinfo in sensor_map.items() if sinfo.get('direction') in dir_labels]
                if not direction_sensors:
                    continue

                # Group sensors by vehicle class for this direction
                vl_sensors = [sid for sid in direction_sensors if sensor_map.get(sid, {}).get('class') == 'VL']
                pl_sensors = [sid for sid in direction_sensors if sensor_map.get(sid, {}).get('class') == 'PL']

                # Determine the number of rows to process
                if sheet_name in ['Sens 3', 'Sens 3 (S1+S2)']:
                    max_rows = 0
                    for sensor_id in direction_sensors:
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        max_rows = max(max_rows, end_row - start_row)
                    num_rows = max_rows
                elif vl_sensors:
                    vl_sensor_id = vl_sensors[0]
                    vl_start_row = vl_sensor_id * rows_per_block
                    vl_end_row = min(vl_start_row + rows_per_block, len(raw_data))
                    num_rows = vl_end_row - vl_start_row
                else:
                    num_rows = 0

                # Build additional pages for each date (page 2+), only if data exists for that day
                if sheet_name == 'Sens 1':
                    dir_labels = ['Sens 1', '1']
                elif sheet_name == 'Sens 2':
                    dir_labels = ['Sens 2', '2']
                else:
                    dir_labels = ['Sens 1', '1', 'Sens 2', '2']

                def _get_active_dates(labels):
                    day_totals = {}
                    for sensor_id in range(num_sensors):
                        sinfo = sensor_map.get(sensor_id, {})
                        if sinfo.get('direction') not in labels:
                            continue
                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        if start_row >= len(raw_data):
                            continue
                        block = raw_data[start_row:end_row]
                        for idx_row, row_vals in enumerate(block):
                            total = 0
                            for i in range(12):
                                total += int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                            if total == 0:
                                continue
                            ts = base_time + timedelta(minutes=interval_minutes * idx_row)
                            day_totals[ts.date()] = day_totals.get(ts.date(), 0) + total
                    return sorted([d for d, t in day_totals.items() if t > 0])

                date_list = _get_active_dates(dir_labels)

                def set_hour_formulas(offset):
                    bins_row = 8 + offset
                    for hour in range(24):
                        r = 11 + offset + hour
                        aa = (
                            f"=IF(AC{r}=0,\"\",(C{r}*(C${bins_row}+D${bins_row})/2+E{r}*(E${bins_row}+F${bins_row})/2+"
                            f"G{r}*(G${bins_row}+H${bins_row})/2+I{r}*(I${bins_row}+J${bins_row})/2+K{r}*(K${bins_row}+L${bins_row})/2+"
                            f"M{r}*(M${bins_row}+N${bins_row})/2+O{r}*(O${bins_row}+P${bins_row})/2+Q{r}*(Q${bins_row}+R${bins_row})/2+"
                            f"S{r}*(S${bins_row}+T${bins_row})/2+U{r}*(U${bins_row}+V${bins_row})/2+W{r}*(W${bins_row}+X${bins_row})/2+"
                            f"Y{r}*(Y${bins_row}+Z${bins_row})/2)/AC{r})"
                        )
                        ab = (
                            f"=IF(AD{r}=0,\"\",(D{r}*(D${bins_row}+C${bins_row})/2+F{r}*(F${bins_row}+E${bins_row})/2+"
                            f"H{r}*(H${bins_row}+G${bins_row})/2+J{r}*(J${bins_row}+I${bins_row})/2+L{r}*(L${bins_row}+K${bins_row})/2+"
                            f"N{r}*(N${bins_row}+M${bins_row})/2+P{r}*(P${bins_row}+O${bins_row})/2+R{r}*(R${bins_row}+Q${bins_row})/2+"
                            f"T{r}*(T${bins_row}+S${bins_row})/2+V{r}*(V${bins_row}+U${bins_row})/2+X{r}*(X${bins_row}+W${bins_row})/2+"
                            f"Z{r}*(Z${bins_row}+Y${bins_row})/2)/AD{r})"
                        )
                        ac = f"=SUM(C{r},E{r},G{r},I{r},K{r},M{r},O{r},Q{r},S{r},U{r},W{r},Y{r})"
                        ad = f"=SUM(D{r},F{r},H{r},J{r},L{r},N{r},P{r},R{r},T{r},V{r},X{r},Z{r})"
                        ae = f"=AC{r}+AD{r}"
                        safe_write_cell_rc(ws, r, 27, aa)
                        safe_write_cell_rc(ws, r, 28, ab)
                        safe_write_cell_rc(ws, r, 29, ac)
                        safe_write_cell_rc(ws, r, 30, ad)
                        safe_write_cell_rc(ws, r, 31, ae)

                def set_totals_and_cumulatives(offset):
                    total_row = 36 + offset
                    percent_row = 37 + offset
                    cumul_vl_row = 38 + offset
                    cumul_pl_row = 39 + offset
                    cumul_tv_row = 40 + offset
                    bins_row = 8 + offset
                    for col_letter, col_idx in zip(
                        ['C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'],
                        range(3, 27)
                    ):
                        safe_write_cell_rc(ws, total_row, col_idx, f"=SUM({col_letter}{11+offset}:{col_letter}{34+offset})")

                    aa_total = (
                        f"=IF(AC{total_row}=0,\"\",(C{total_row}*(C${bins_row}+D${bins_row})/2+E{total_row}*(E${bins_row}+F${bins_row})/2+"
                        f"G{total_row}*(G${bins_row}+H${bins_row})/2+I{total_row}*(I${bins_row}+J${bins_row})/2+K{total_row}*(K${bins_row}+L${bins_row})/2+"
                        f"M{total_row}*(M${bins_row}+N${bins_row})/2+O{total_row}*(O${bins_row}+P${bins_row})/2+Q{total_row}*(Q${bins_row}+R${bins_row})/2+"
                        f"S{total_row}*(S${bins_row}+T${bins_row})/2+U{total_row}*(U${bins_row}+V${bins_row})/2+W{total_row}*(W${bins_row}+X${bins_row})/2+"
                        f"Y{total_row}*(Y${bins_row}+Z${bins_row})/2)/AC{total_row})"
                    )
                    ab_total = (
                        f"=IF(AD{total_row}=0,\"\",(D{total_row}*(D${bins_row}+C${bins_row})/2+F{total_row}*(F${bins_row}+E${bins_row})/2+"
                        f"H{total_row}*(H${bins_row}+G${bins_row})/2+J{total_row}*(J${bins_row}+I${bins_row})/2+L{total_row}*(L${bins_row}+K${bins_row})/2+"
                        f"N{total_row}*(N${bins_row}+M${bins_row})/2+P{total_row}*(P${bins_row}+O${bins_row})/2+R{total_row}*(R${bins_row}+Q${bins_row})/2+"
                        f"T{total_row}*(T${bins_row}+S${bins_row})/2+V{total_row}*(V${bins_row}+U${bins_row})/2+X{total_row}*(X${bins_row}+W${bins_row})/2+"
                        f"Z{total_row}*(Z${bins_row}+Y${bins_row})/2)/AD{total_row})"
                    )
                    safe_write_cell_rc(ws, total_row, 27, aa_total)
                    safe_write_cell_rc(ws, total_row, 28, ab_total)
                    safe_write_cell_rc(ws, total_row, 29, f"=SUM(AC{11+offset}:AC{34+offset})")
                    safe_write_cell_rc(ws, total_row, 30, f"=SUM(AD{11+offset}:AD{34+offset})")
                    safe_write_cell_rc(ws, total_row, 31, f"=SUM(AE{11+offset}:AE{34+offset})")

                    safe_write_cell_rc(ws, percent_row, 2, "%")
                    for col_letter, col_idx in zip(
                        ['C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'],
                        range(3, 27)
                    ):
                        safe_write_cell_rc(ws, percent_row, col_idx, f"=100*{col_letter}{total_row}/$AE{total_row}")
                    safe_write_cell_rc(ws, percent_row, 29, f"=AC{total_row}/AE{total_row}")
                    safe_write_cell_rc(ws, percent_row, 30, f"=AD{total_row}/AE{total_row}")

                    safe_write_cell_rc(ws, cumul_vl_row, 2, "% cumul VL")
                    safe_write_cell_rc(ws, cumul_vl_row, 3, f"=100*C{total_row}/$AC{total_row}")
                    for col_letter, prev_letter, col_idx in [
                        ('E','C',5), ('G','E',7), ('I','G',9), ('K','I',11), ('M','K',13), ('O','M',15),
                        ('Q','O',17), ('S','Q',19), ('U','S',21), ('W','U',23), ('Y','W',25)
                    ]:
                        safe_write_cell_rc(ws, cumul_vl_row, col_idx, f"=100*{col_letter}{total_row}/$AC{total_row}+{prev_letter}{cumul_vl_row}")

                    safe_write_cell_rc(ws, cumul_pl_row, 1, "% cumul PL")
                    safe_write_cell_rc(ws, cumul_pl_row, 4, f"=100*D{total_row}/$AD{total_row}")
                    for col_letter, prev_letter, col_idx in [
                        ('F','D',6), ('H','F',8), ('J','H',10), ('L','J',12), ('N','L',14), ('P','N',16),
                        ('R','P',18), ('T','R',20), ('V','T',22), ('X','V',24), ('Z','X',26)
                    ]:
                        safe_write_cell_rc(ws, cumul_pl_row, col_idx, f"=100*{col_letter}{total_row}/$AD{total_row}+{prev_letter}{cumul_pl_row}")

                    safe_write_cell_rc(ws, cumul_tv_row, 2, "% cumul TV")
                    for col_letter_vl, col_letter_pl, col_idx in [
                        ('C','D',3), ('E','F',5), ('G','H',7), ('I','J',9), ('K','L',11), ('M','N',13),
                        ('O','P',15), ('Q','R',17), ('S','T',19), ('U','V',21), ('W','X',23), ('Y','Z',25)
                    ]:
                        safe_write_cell_rc(ws, cumul_tv_row, col_idx, f"=({col_letter_vl}{cumul_vl_row}*$AC{total_row}+{col_letter_pl}{cumul_pl_row}*$AD{total_row})/$AE{total_row}")

                def set_summary_rows(offset):
                    base_row = 43 + offset
                    total_row = 36 + offset
                    vl_row = 48 + offset
                    pl_row = 50 + offset
                    tv_row = 46 + offset
                    helper_row = 47 + offset

                    safe_write_cell_rc(ws, tv_row, 30, f"=AE{total_row}")
                    safe_write_cell_rc(ws, tv_row, 31, f"=AD{tv_row}/AH{base_row}")
                    safe_write_cell_rc(ws, tv_row, 32, f"=(AF{vl_row}*AD{vl_row}+AF{pl_row}*AD{pl_row})/AD{tv_row}")

                    safe_write_cell_rc(ws, tv_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row})+((0.15*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AG{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AG{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AG{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row})+((0.5*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AH{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AH{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AH{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row})+((0.85*AD{tv_row}-(INDEX($A{40+offset}:$Z{40+offset},1,AI{helper_row})*AD{tv_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{helper_row})+INDEX($C{total_row}:$Z{total_row},1,AI{helper_row}+1))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AI{helper_row})))")
                    safe_write_cell_rc(ws, tv_row, 36, f"=AJ{vl_row}+AJ{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 37, f"=AK{vl_row}+AK{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 38, f"=AL{vl_row}+AL{pl_row}")
                    safe_write_cell_rc(ws, tv_row, 39, f"=AM{vl_row}+AM{pl_row}")

                    safe_write_cell_rc(ws, vl_row, 30, f"=AC{total_row}")
                    safe_write_cell_rc(ws, vl_row, 31, f"=AD{vl_row}/AH{base_row}")
                    safe_write_cell_rc(ws, vl_row, 32, f"=AA{total_row}")
                    safe_write_cell_rc(ws, vl_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1})+((0.15*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AG{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AG{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1})+((0.5*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AH{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AH{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1})+((0.85*AD{vl_row}-(INDEX($A{38+offset}:$Z{38+offset},1,AI{vl_row+1})*AD{vl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{vl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1}+1)-INDEX($C{8+offset}:$Z{8+offset},1,AI{vl_row+1})))")
                    safe_write_cell_rc(ws, vl_row, 36, f"=SUMIFS(C{total_row}:Z{total_row},C{10+offset}:Z{10+offset},\"VL\",D{8+offset}:AA{8+offset},\">\"&AD{base_row})")
                    safe_write_cell_rc(ws, vl_row, 37, f"=SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{52+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{52+offset})")
                    safe_write_cell_rc(ws, vl_row, 38, f"=SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{53+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{53+offset})")
                    safe_write_cell_rc(ws, vl_row, 39, f"=IF(AM{54+offset}=AK{54+offset},0,IF($AK${54+offset}<$AM${54+offset},SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset}),SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset})+SUMIFS(AC{11+offset}:AC{34+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset})))")

                    safe_write_cell_rc(ws, pl_row, 30, f"=AD{total_row}")
                    safe_write_cell_rc(ws, pl_row, 31, f"=AD{pl_row}/AH{base_row}")
                    safe_write_cell_rc(ws, pl_row, 32, f"=AB{total_row}")
                    safe_write_cell_rc(ws, pl_row, 33, f"=INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1}-1)+((0.15*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AG{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AG{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AG{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 34, f"=INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1}-1)+((0.5*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AH{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AH{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AH{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 35, f"=INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1}-1)+((0.85*AD{pl_row}-(INDEX($A{39+offset}:$Z{39+offset},1,AI{pl_row+1})*AD{pl_row}/100))/(INDEX($C{total_row}:$Z{total_row},1,AI{pl_row+1}))*(INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1})-INDEX($C{8+offset}:$Z{8+offset},1,AI{pl_row+1}-1)))")
                    safe_write_cell_rc(ws, pl_row, 36, f"=SUMIFS(C{total_row}:Z{total_row},C{10+offset}:Z{10+offset},\"PL\",C{8+offset}:Z{8+offset},\">\"&AD{base_row})")
                    safe_write_cell_rc(ws, pl_row, 37, f"=SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{52+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{52+offset})")
                    safe_write_cell_rc(ws, pl_row, 38, f"=SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{53+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{53+offset})")
                    safe_write_cell_rc(ws, pl_row, 39, f"=IF(AM{54+offset}=AK{54+offset},0,IF($AK${54+offset}<$AM${54+offset},SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset}),SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\">=\"&AK{54+offset})+SUMIFS(AD{11+offset}:AD{34+offset},AO{11+offset}:AO{34+offset},\"<\"&AM{54+offset})))")

                gap_rows_after_page8 = 3
                gap_start_idx = 7  # idx 6 = page 8, idx 7 = page 9
                for idx, date_val in enumerate(date_list):
                    gap_offset = gap_rows_after_page8 if idx >= gap_start_idx else 0
                    offset = 56 * (idx + 1) + gap_offset
                    copy_range_with_styles(ws, 1, 56, 1, 40, offset)

                    # Add charts for pages beyond the last charted page (page 8)
                    # idx 0 corresponds to page 2, so use (idx + 2) for page number
                    if (idx + 2) > last_chart_page:
                        if base_page8_charts:
                            delta = offset - (56 * 7)
                            source_charts = base_page8_charts
                        else:
                            delta = offset
                            source_charts = base_page1_charts
                        for ch in source_charts:
                            try:
                                ws.add_chart(_clone_chart_with_offset(ch, delta))
                            except Exception:
                                continue

                    weekday_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][date_val.weekday()]
                    date_label = f"{date_val.strftime('%d/%m/%Y')} {weekday_fr}"
                    safe_write_cell_rc(ws, 58 + offset, 7, date_label)
                    for r in range(1 + offset, 57 + offset):
                        for c in range(1, 41):
                            cell = ws.cell(row=r, column=c)
                            if isinstance(cell.value, str) and 'MOYENNE DE LA PERIODE DE RELEVE' in cell.value:
                                safe_write_cell_rc(ws, r, c, date_label)

                    daily_vl = [[0] * 12 for _ in range(24)]
                    daily_pl = [[0] * 12 for _ in range(24)]

                    for sensor_id in range(num_sensors):
                        sensor_info = sensor_map.get(sensor_id, {})
                        sensor_dir = sensor_info.get('direction', '')
                        sensor_class = sensor_info.get('class', '')

                        if sensor_dir not in dir_labels:
                            continue

                        start_row = sensor_id * rows_per_block
                        end_row = min(start_row + rows_per_block, len(raw_data))
                        if start_row >= len(raw_data):
                            continue

                        block = raw_data[start_row:end_row]
                        for idx_row, row_vals in enumerate(block):
                            timestamp = base_time + timedelta(minutes=interval_minutes * idx_row)
                            if timestamp.date() != date_val:
                                continue
                            hour = timestamp.hour
                            for i in range(12):
                                val = int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                                if sensor_class == 'PL':
                                    daily_pl[hour][i] += val
                                else:
                                    daily_vl[hour][i] += val

                    for hour in range(24):
                        row_idx = 11 + offset + hour
                        col_idx = 3
                        for bin_idx in range(12):
                            safe_write_cell_rc(ws, row_idx, col_idx, round(daily_vl[hour][bin_idx], 0))
                            col_idx += 1
                            safe_write_cell_rc(ws, row_idx, col_idx, round(daily_pl[hour][bin_idx], 0))
                            col_idx += 1

                    set_hour_formulas(offset)
                    set_totals_and_cumulatives(offset)
                    set_summary_rows(offset)

                # Write hourly mean values directly (rows 11-34, columns C-Z)
                hourly_vl = [[0] * 12 for _ in range(24)]
                hourly_pl = [[0] * 12 for _ in range(24)]
                for sensor_id in range(num_sensors):
                    sensor_info = sensor_map.get(sensor_id, {})
                    sensor_dir = sensor_info.get('direction', '')
                    sensor_class = sensor_info.get('class', '')

                    if sensor_dir not in dir_labels:
                        continue

                    start_row = sensor_id * rows_per_block
                    end_row = min(start_row + rows_per_block, len(raw_data))
                    if start_row >= len(raw_data):
                        continue

                    block = raw_data[start_row:end_row]
                    for idx_row, row_vals in enumerate(block):
                        timestamp = base_time + timedelta(minutes=interval_minutes * idx_row)
                        hour = timestamp.hour
                        for i in range(12):
                            val = int(row_vals[i]) if i < len(row_vals) and row_vals[i] else 0
                            if sensor_class == 'PL':
                                hourly_pl[hour][i] += val
                            else:
                                hourly_vl[hour][i] += val

                day_divisor = max(num_days, 1)
                for hour in range(24):
                    row_idx = 11 + hour
                    col_idx = 3
                    for bin_idx in range(12):
                        vl_val = hourly_vl[hour][bin_idx] / day_divisor
                        pl_val = hourly_pl[hour][bin_idx] / day_divisor
                        safe_write_cell_rc(ws, row_idx, col_idx, round(vl_val, 0))
                        col_idx += 1
                        safe_write_cell_rc(ws, row_idx, col_idx, round(pl_val, 0))
                        col_idx += 1

            # Rebuild charts on "Graphiques" sheet
            if 'Graphiques' in wb.sheetnames:
                from openpyxl.chart import LineChart, BarChart, Reference
                from openpyxl.chart.series import Series

                ws_graph = wb['Graphiques']
                ws_graph._charts = []

                # Build data tables for speed-bin bar charts
                bin_labels = ['<20', '20 - 30', '30 - 40', '40 - 50', '50 - 60', '60 - 70',
                              '70 - 80', '80 - 90', '90 - 100', '100 - 110', '110 - 120', '>120']

                # Clear area for tables
                for r in range(1, 30):
                    for c in range(1, 4):
                        safe_write_cell_rc(ws_graph, r, c, None)

                # VL table (rows 1-13)
                safe_write_cell_rc(ws_graph, 1, 1, 'Bin')
                safe_write_cell_rc(ws_graph, 1, 2, 'VL Sens 1')
                safe_write_cell_rc(ws_graph, 1, 3, 'VL Sens 2')
                vl_cols = ['C', 'E', 'G', 'I', 'K', 'M', 'O', 'Q', 'S', 'U', 'W', 'Y']
                for i, label in enumerate(bin_labels, start=2):
                    safe_write_cell_rc(ws_graph, i, 1, label)
                    safe_write_cell_rc(ws_graph, i, 2, f"=IFERROR('Sens 1'!{vl_cols[i-2]}$36,0)")
                    safe_write_cell_rc(ws_graph, i, 3, f"=IFERROR('Sens 2'!{vl_cols[i-2]}$36,0)")

                # PL table (rows 16-28)
                safe_write_cell_rc(ws_graph, 16, 1, 'Bin')
                safe_write_cell_rc(ws_graph, 16, 2, 'PL Sens 1')
                safe_write_cell_rc(ws_graph, 16, 3, 'PL Sens 2')
                pl_cols = ['D', 'F', 'H', 'J', 'L', 'N', 'P', 'R', 'T', 'V', 'X', 'Z']
                for i, label in enumerate(bin_labels, start=17):
                    safe_write_cell_rc(ws_graph, i, 1, label)
                    safe_write_cell_rc(ws_graph, i, 2, f"=IFERROR('Sens 1'!{pl_cols[i-17]}$36,0)")
                    safe_write_cell_rc(ws_graph, i, 3, f"=IFERROR('Sens 2'!{pl_cols[i-17]}$36,0)")

                # Line chart: VL debit (Sens 1 blue, Sens 2 red)
                chart_vl = LineChart()
                chart_vl.title = 'Débit VL (Sens 1 & 2)'
                chart_vl.y_axis.title = 'Véhicules'
                chart_vl.x_axis.title = 'Heure'
                cats = Reference(wb['Sens 1'], min_col=2, min_row=11, max_row=34)
                data_s1 = Reference(wb['Sens 1'], min_col=29, min_row=10, max_row=34)  # AC
                data_s2 = Reference(wb['Sens 2'], min_col=29, min_row=10, max_row=34)  # AC
                from openpyxl.chart.series import SeriesLabel
                chart_vl.add_data(data_s1, titles_from_data=False)
                chart_vl.series[0].tx = SeriesLabel(v='Sens 1')
                chart_vl.add_data(data_s2, titles_from_data=False)
                chart_vl.series[1].tx = SeriesLabel(v='Sens 2')
                chart_vl.set_categories(cats)

                # Line chart: PL debit
                chart_pl = LineChart()
                chart_pl.title = 'Débit PL (Sens 1 & 2)'
                chart_pl.y_axis.title = 'Véhicules'
                chart_pl.x_axis.title = 'Heure'
                data_s1_pl = Reference(wb['Sens 1'], min_col=30, min_row=10, max_row=34)  # AD
                data_s2_pl = Reference(wb['Sens 2'], min_col=30, min_row=10, max_row=34)  # AD
                chart_pl.add_data(data_s1_pl, titles_from_data=False)
                chart_pl.series[0].tx = SeriesLabel(v='Sens 1')
                chart_pl.add_data(data_s2_pl, titles_from_data=False)
                chart_pl.series[1].tx = SeriesLabel(v='Sens 2')
                chart_pl.set_categories(cats)

                # Bar chart: VL bins
                chart_vl_bins = BarChart()
                chart_vl_bins.type = 'col'
                chart_vl_bins.title = 'Répartition VL par classe de vitesse'
                chart_vl_bins.y_axis.title = 'Véhicules'
                chart_vl_bins.x_axis.title = 'Classe de vitesse'
                data_vl_bins = Reference(ws_graph, min_col=2, max_col=3, min_row=1, max_row=13)
                cats_vl_bins = Reference(ws_graph, min_col=1, min_row=2, max_row=13)
                chart_vl_bins.add_data(data_vl_bins, titles_from_data=True)
                chart_vl_bins.set_categories(cats_vl_bins)

                # Bar chart: PL bins
                chart_pl_bins = BarChart()
                chart_pl_bins.type = 'col'
                chart_pl_bins.title = 'Répartition PL par classe de vitesse'
                chart_pl_bins.y_axis.title = 'Véhicules'
                chart_pl_bins.x_axis.title = 'Classe de vitesse'
                data_pl_bins = Reference(ws_graph, min_col=2, max_col=3, min_row=16, max_row=28)
                cats_pl_bins = Reference(ws_graph, min_col=1, min_row=17, max_row=28)
                chart_pl_bins.add_data(data_pl_bins, titles_from_data=True)
                chart_pl_bins.set_categories(cats_pl_bins)

                # Layout: 2x2 fit to page
                chart_vl.width = 9.5
                chart_vl.height = 5.5
                chart_pl.width = 9.5
                chart_pl.height = 5.5
                chart_vl_bins.width = 9.5
                chart_vl_bins.height = 5.5
                chart_pl_bins.width = 9.5
                chart_pl_bins.height = 5.5

                ws_graph.add_chart(chart_vl, 'A1')
                ws_graph.add_chart(chart_pl, 'A20')
                ws_graph.add_chart(chart_vl_bins, 'J1')
                ws_graph.add_chart(chart_pl_bins, 'J20')

                # Ensure page 1 summary/percentile formulas are set
                set_hour_formulas(0)
                set_totals_and_cumulatives(0)
                set_summary_rows(0)
            
            # Save the populated template
            wb.save(file_path)

            QMessageBox.information(self, "Succès", f"Données Débit-Vitesse exportées avec succès:\n{file_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export Débit-Vitesse:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def analyse_data(self):
        # Analyse functionality removed.
        pass


    def _analyse_to_excel(self):
        # Analyse functionality removed.
        pass

    def _analyse_to_pdf(self):
        # Analyse functionality removed.
        pass

    def _analyse_to_docx(self):
        # Analyse functionality removed.
        pass
    
    def _create_velocity_analysis_charts(self, ax1, ax2, ax3, direction: str):
        """Create velocity analysis charts for a specific direction (used by both PDF and DOCX)"""
        import numpy as np
        
        # Speed bin labels and colors
        speed_bins_labels = [
            '0-30', '30-40', '40-50', '50-60', '60-70', '70-80',
            '80-90', '90-100', '100-110', '110-120', '120-130', '130-150'
        ]
        speed_bin_colors = plt.cm.tab20(np.linspace(0, 1, 12))
        
        # Extract velocity bin data
        vl_counts = np.zeros(12)
        pl_counts = np.zeros(12)
        
        meta = self.current_metadata
        raw_data = meta.get('raw_data', [])
        sensor_map = meta.get('sensor_map', {})
        num_sensors = meta.get('num_sensors', 0)
        rows_per_block = meta.get('rows_per_block', 0)
        
        if raw_data and sensor_map:
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                if sensor_direction != direction:
                    continue
                
                for row_vals in block:
                    for i in range(12):
                        try:
                            val = row_vals[i] if i < len(row_vals) else 0
                            bin_count = int(val) if val else 0
                            if vehicle_class == 'VL':
                                vl_counts[i] += bin_count
                            elif vehicle_class == 'PL':
                                pl_counts[i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        # Chart 1: Velocity Bin Analysis (VL vs PL)
        x = np.arange(len(speed_bins_labels))
        width = 0.35
        ax1.bar(x - width/2, vl_counts, width, label='VL', color='#0066cc', alpha=0.8)
        ax1.bar(x + width/2, pl_counts, width, label='PL', color='#ff9800', alpha=0.8)
        ax1.set_ylabel('Nombre de Véhicules', fontsize=10)
        ax1.set_xlabel('Classes de vitesse (km/h)', fontsize=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(speed_bins_labels, rotation=0, ha='right', fontsize=8)
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # Chart 2 & 3: Hourly breakdown (same as PDF)
        vl_hourly_bins = np.zeros((24, 12))
        pl_hourly_bins = np.zeros((24, 12))
        
        if raw_data and sensor_map:
            base_time = self.analysis_start_dt
            
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                if sensor_direction != direction:
                    continue
                
                freq = self.current_metadata.get('freq', 15)
                
                for row_idx, row_vals in enumerate(block):
                    try:
                        timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                        hour = timestamp.hour
                        
                        for i in range(12):
                            val = row_vals[i] if i < len(row_vals) else 0
                            bin_count = int(val) if val else 0
                            if vehicle_class == 'VL':
                                vl_hourly_bins[hour, i] += bin_count
                            elif vehicle_class == 'PL':
                                pl_hourly_bins[hour, i] += bin_count
                    except (TypeError, ValueError, IndexError):
                        pass
        
        # Stacked bar charts for hourly data
        hours = np.arange(24)
        
        # VL hourly breakdown
        bottom_vl = np.zeros(24)
        for bin_idx in range(12):
            ax2.bar(hours, vl_hourly_bins[:, bin_idx], bottom=bottom_vl, 
                   label=f'{speed_bins_labels[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom_vl += vl_hourly_bins[:, bin_idx]
        
        ax2.set_ylabel('Nombre de Véhicules (VL)', fontsize=10)
        ax2.set_xlabel('Heure de la journée', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax2.legend(fontsize=6, loc='upper left', ncol=6, bbox_to_anchor=(0, 1.02))
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # PL hourly breakdown
        bottom_pl = np.zeros(24)
        for bin_idx in range(12):
            ax3.bar(hours, pl_hourly_bins[:, bin_idx], bottom=bottom_pl, 
                   label=f'{speed_bins_labels[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom_pl += pl_hourly_bins[:, bin_idx]
        
        ax3.set_ylabel('Nombre de Véhicules (PL)', fontsize=10)
        ax3.set_xlabel('Heure de la journée', fontsize=10)
        ax3.set_xticks(range(0, 24, 2))
        ax3.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    def _create_mean_speed_chart(self, ax):
        """Create mean speed analysis visualization - this is a placeholder, actual page 5 should use full PDF implementation"""
        # This method should not be used for DOCX. Instead, we'll use the full PDF implementation.
        # For now, just create a simple placeholder.
        ax.text(0.5, 0.5, 'Mean Speed Analysis\n(See PDF for full page 5)', 
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.axis('off')
    
    def _create_page5_charts(self, ax1, ax2, ax3):
        """Create Page 5 analysis charts: mean speeds by hour for Sens 1 & 2, and débit with dual axes"""
        import numpy as np
        
        hours = np.arange(24)
        meta = self.current_metadata
        raw_data = meta.get('raw_data', [])
        sensor_map = meta.get('sensor_map', {})
        num_sensors = meta.get('num_sensors', 0)
        rows_per_block = meta.get('rows_per_block', 0)
        speed_bin_centers = meta.get('speed_bin_centers', [])
        freq = meta.get('freq', 15)
        
        # === CHART 1: Mean Speed by Hour for Sens 1 (VL and PL) ===
        vl_mean_by_hour_s1 = np.zeros(24)
        pl_mean_by_hour_s1 = np.zeros(24)
        
        if raw_data and sensor_map and speed_bin_centers:
            vl_numerator_s1 = {h: 0 for h in range(24)}
            vl_denominator_s1 = {h: 0 for h in range(24)}
            pl_numerator_s1 = {h: 0 for h in range(24)}
            pl_denominator_s1 = {h: 0 for h in range(24)}
            
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                if sensor_direction != 'Sens 1':
                    continue
                
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                        
                        if vehicle_class == 'VL':
                            vl_numerator_s1[hour] += count * speed_center
                            vl_denominator_s1[hour] += count
                        elif vehicle_class == 'PL':
                            pl_numerator_s1[hour] += count * speed_center
                            pl_denominator_s1[hour] += count
            
            for hour in range(24):
                if vl_denominator_s1[hour] > 0:
                    vl_mean_by_hour_s1[hour] = vl_numerator_s1[hour] / vl_denominator_s1[hour]
                if pl_denominator_s1[hour] > 0:
                    pl_mean_by_hour_s1[hour] = pl_numerator_s1[hour] / pl_denominator_s1[hour]
        
        ax1.plot(hours, vl_mean_by_hour_s1, label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5)
        ax1.plot(hours, pl_mean_by_hour_s1, label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5)
        ax1.set_ylabel('Vitesse moyenne (km/h)', fontsize=10, labelpad=5)
        ax1.set_xlabel('Heure du jour', fontsize=10)
        ax1.set_title('Vitesse moyenne par heure - Sens 1', fontsize=10)
        ax1.set_xticks(range(0, 24, 2))
        ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax1.set_xlim(-0.5, 23.5)
        ax1.margins(y=0.1)
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax1.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # === CHART 2: Mean Speed by Hour for Sens 2 (VL and PL) ===
        vl_mean_by_hour_s2 = np.zeros(24)
        pl_mean_by_hour_s2 = np.zeros(24)
        
        if raw_data and sensor_map and speed_bin_centers:
            vl_numerator_s2 = {h: 0 for h in range(24)}
            vl_denominator_s2 = {h: 0 for h in range(24)}
            pl_numerator_s2 = {h: 0 for h in range(24)}
            pl_denominator_s2 = {h: 0 for h in range(24)}
            
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                if sensor_direction != 'Sens 2':
                    continue
                
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                        
                        if vehicle_class == 'VL':
                            vl_numerator_s2[hour] += count * speed_center
                            vl_denominator_s2[hour] += count
                        elif vehicle_class == 'PL':
                            pl_numerator_s2[hour] += count * speed_center
                            pl_denominator_s2[hour] += count
            
            for hour in range(24):
                if vl_denominator_s2[hour] > 0:
                    vl_mean_by_hour_s2[hour] = vl_numerator_s2[hour] / vl_denominator_s2[hour]
                if pl_denominator_s2[hour] > 0:
                    pl_mean_by_hour_s2[hour] = pl_numerator_s2[hour] / pl_denominator_s2[hour]
        
        ax2.plot(hours, vl_mean_by_hour_s2, label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5)
        ax2.plot(hours, pl_mean_by_hour_s2, label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5)
        ax2.set_ylabel('Vitesse moyenne (km/h)', fontsize=10, labelpad=5)
        ax2.set_xlabel('Heure du jour', fontsize=10)
        ax2.set_title('Vitesse moyenne par heure - Sens 2', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax2.set_xlim(-0.5, 23.5)
        ax2.margins(y=0.1)
        ax2.legend(fontsize=8, loc='upper right')
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax2.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # === CHART 3: Débit with Dual Y-Axes ===
        vl_debit_s1 = np.zeros(24)
        pl_debit_s1 = np.zeros(24)
        vl_debit_s2 = np.zeros(24)
        pl_debit_s2 = np.zeros(24)
        
        if raw_data and sensor_map:
            vl_total_s1 = {h: 0 for h in range(24)}
            vl_occ_s1 = {h: 0 for h in range(24)}
            pl_total_s1 = {h: 0 for h in range(24)}
            pl_occ_s1 = {h: 0 for h in range(24)}
            vl_total_s2 = {h: 0 for h in range(24)}
            vl_occ_s2 = {h: 0 for h in range(24)}
            pl_total_s2 = {h: 0 for h in range(24)}
            pl_occ_s2 = {h: 0 for h in range(24)}
            
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    hour_count = sum([int(row_vals[i]) if i < len(row_vals) else 0 for i in range(min(12, len(row_vals)))])
                    
                    if sensor_direction == 'Sens 1':
                        if vehicle_class == 'VL':
                            vl_total_s1[hour] += hour_count
                            vl_occ_s1[hour] += 1
                        elif vehicle_class == 'PL':
                            pl_total_s1[hour] += hour_count
                            pl_occ_s1[hour] += 1
                    elif sensor_direction == 'Sens 2':
                        if vehicle_class == 'VL':
                            vl_total_s2[hour] += hour_count
                            vl_occ_s2[hour] += 1
                        elif vehicle_class == 'PL':
                            pl_total_s2[hour] += hour_count
                            pl_occ_s2[hour] += 1
            
            for hour in range(24):
                if vl_occ_s1[hour] > 0:
                    vl_debit_s1[hour] = vl_total_s1[hour] / vl_occ_s1[hour]
                if pl_occ_s1[hour] > 0:
                    pl_debit_s1[hour] = pl_total_s1[hour] / pl_occ_s1[hour]
                if vl_occ_s2[hour] > 0:
                    vl_debit_s2[hour] = vl_total_s2[hour] / vl_occ_s2[hour]
                if pl_occ_s2[hour] > 0:
                    pl_debit_s2[hour] = pl_total_s2[hour] / pl_occ_s2[hour]
        
        # Plot débit with dual y-axes
        ax3_twin = ax3.twinx()
        
        # Left axis (VL)
        ax3.plot(hours, vl_debit_s1, label='VL Sens 1', color='#0066cc', linewidth=1.0, linestyle='-', marker='o', markersize=4)
        ax3.plot(hours, vl_debit_s2, label='VL Sens 2', color='#0066cc', linewidth=1.0, linestyle='--', marker='o', markersize=4)
        ax3.set_ylabel('Débit VL (véh/15min)', fontsize=10, color='#0066cc', labelpad=5)
        ax3.tick_params(axis='y', labelcolor='#0066cc')
        
        # Right axis (PL)
        ax3_twin.plot(hours, pl_debit_s1, label='PL Sens 1', color='#ff9800', linewidth=1.0, linestyle='-', marker='s', markersize=4)
        ax3_twin.plot(hours, pl_debit_s2, label='PL Sens 2', color='#ff9800', linewidth=1.0, linestyle='--', marker='s', markersize=4)
        ax3_twin.set_ylabel('Débit PL (véh/15min)', fontsize=10, color='#ff9800', labelpad=5)
        ax3_twin.tick_params(axis='y', labelcolor='#ff9800')
        
        ax3.set_xlabel('Heure du jour', fontsize=10)
        ax3.set_title('Débit moyen par heure (VL/PL Sens 1 & 2)', fontsize=10)
        ax3.set_xticks(range(0, 24, 2))
        ax3.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax3.set_xlim(-0.5, 23.5)
        ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax3.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Combined legend
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper left', ncol=2)



    def _calculate_analysis_statistics(self, ts_data: dict) -> dict:
        """
        Calculate traffic statistics for analysis table.
        Returns dict with statistics for Sens 1, Sens 2, and cumulative.
        """
        stats = {}
        
        # Helper function to calculate stats for a single dataframe
        def calc_stats(df):
            if df is None or df.empty:
                return {
                    'Total': 0,
                    'Daily Avg': 0,
                    'Hourly Avg': 0,
                    'Daily Avg Day': 0,
                    'Daily Avg Night': 0,
                    'Daily Avg Working': 0,
                    'Avg Monday-Saturday': 0,
                    'Avg Saturday': 0,
                    'Avg Sunday': 0,
                    'PL Percentage': 0
                }
            
            total = df['count'].sum()
            num_unique_dates = len(df['timestamp'].dt.date.unique())
            num_unique_hours = len(df['timestamp'].dt.hour.unique())
            
            daily_avg = total / max(num_unique_dates, 1)
            hourly_avg = total / max(num_unique_hours, 1)
            
            # Day period (6h-22h), Night (22h-6h)
            df_copy = df.copy()
            df_copy['hour'] = df_copy['timestamp'].dt.hour
            df_copy['date'] = df_copy['timestamp'].dt.date
            df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek  # 0=Mon, 6=Sun
            
            day_data = df_copy[(df_copy['hour'] >= 6) & (df_copy['hour'] < 22)]
            night_data = df_copy[(df_copy['hour'] >= 22) | (df_copy['hour'] < 6)]
            
            day_avg = (day_data['count'].sum() / max(len(day_data['date'].unique()), 1)) if len(day_data) > 0 else 0
            night_avg = (night_data['count'].sum() / max(len(night_data['date'].unique()), 1)) if len(night_data) > 0 else 0
            
            # French public holidays for automatic detection
            date_range = df_copy['date'].unique()
            if len(date_range) > 0:
                min_year = pd.Timestamp(date_range[0]).year
                max_year = pd.Timestamp(date_range[-1]).year
                fr_holidays = holidays.France(years=range(min_year, max_year + 1))
            else:
                fr_holidays = {}
            
            # Working days (Mon-Fri, excluding French public holidays)
            working_data = df_copy[(df_copy['day_of_week'] < 5) & 
                                   (~df_copy['date'].isin([date for date in df_copy['date'].unique() if date in fr_holidays]))]
            working_avg = (working_data['count'].sum() / max(len(working_data['date'].unique()), 1)) if len(working_data) > 0 else 0
            
            # Monday-Saturday
            mon_sat_data = df_copy[df_copy['day_of_week'] < 6]
            mon_sat_avg = (mon_sat_data['count'].sum() / max(len(mon_sat_data['date'].unique()), 1)) if len(mon_sat_data) > 0 else 0
            
            # Saturday only
            sat_data = df_copy[df_copy['day_of_week'] == 5]
            sat_avg = (sat_data['count'].sum() / max(len(sat_data['date'].unique()), 1)) if len(sat_data) > 0 else 0
            
            # Sunday only
            sun_data = df_copy[df_copy['day_of_week'] == 6]
            sun_avg = (sun_data['count'].sum() / max(len(sun_data['date'].unique()), 1)) if len(sun_data) > 0 else 0
            
            return {
                'Total': int(total),
                'Daily Avg': int(daily_avg),
                'Hourly Avg': int(hourly_avg),
                'Daily Avg Day': int(day_avg),
                'Daily Avg Night': int(night_avg),
                'Daily Avg Working': int(working_avg),
                'Avg Monday-Saturday': int(mon_sat_avg),
                'Avg Saturday': int(sat_avg),
                'Avg Sunday': int(sun_avg),
                'PL Percentage': 0
            }
        
        # Calculate for each type
        for vehicle_type in ['VL', 'PL', 'Total']:
            sens1_df = ts_data[vehicle_type].get('Sens 1')
            sens2_df = ts_data[vehicle_type].get('Sens 2')
            cumul_df = ts_data[vehicle_type].get('Cumul')
            
            stats[vehicle_type] = {
                'Sens 1': calc_stats(sens1_df),
                'Sens 2': calc_stats(sens2_df),
                'Cumul': calc_stats(cumul_df)
            }
        
        return stats
    
    def _add_analysis_table_to_sheet(self, ws, ts_data: dict):
        """Add analysis statistics table to Excel worksheet"""
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        # Add date range header in cell Z3
        if self.analysis_start_dt and self.analysis_end_dt:
            date_range_text = f"du {self.analysis_start_dt.strftime('%d/%m/%Y %H:%M')} au {self.analysis_end_dt.strftime('%d/%m/%Y %H:%M')}"
            ws['Z3'] = date_range_text
            ws['Z3'].font = Font(name='Arial', size=12, bold=True, italic=True)
        
        row = 1
        
        # Create analysis for each vehicle type
        for vehicle_type in ['VL', 'PL', 'Total']:
            # Title
            ws[f'A{row}'] = f'Analyse - {vehicle_type}'
            ws[f'A{row}'].font = Font(bold=True, size=12)
            row += 1
            
            # Headers
            headers = ['Métrique', 'Sens 1', 'Sens 2', 'Deux sens cumulés']
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=row, column=col)
                cell.value = header
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            row += 1
            
            # Statistics rows
            stats = self._calculate_analysis_statistics(ts_data)
            
            metrics = [
                ('Débit total sur la période', 'Total'),
                ('Débit Moyen Journalier', 'Daily Avg'),
                ('Débit Moyen horaire', 'Hourly Avg'),
                ('Débit Moyen de Jour', 'Daily Avg Day'),
                ('Débit Moyen de Nuit', 'Daily Avg Night'),
                ('Débit Moyen Jours Ouvrés', 'Daily Avg Working'),
                ('Débit Moyen Lundi --> Samedi', 'Avg Monday-Saturday'),
                ('Débit  Samedi', 'Avg Saturday'),
                ('Débit  Dimanche', 'Avg Sunday'),
            ]
            
            for metric_label, metric_key in metrics:
                ws[f'A{row}'] = metric_label
                for col_idx, direction in enumerate(['Sens 1', 'Sens 2', 'Cumul'], start=2):
                    value = stats[vehicle_type][direction].get(metric_key, 0)
                    ws.cell(row=row, column=col_idx).value = value
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")
                row += 1
            
            # Add PL percentage row only for Total type
            if vehicle_type == 'Total':
                ws[f'A{row}'] = '% PL - Bus'
                pl_stats = stats['PL']
                total_stats = stats['Total']
                for col_idx, direction in enumerate(['Sens 1', 'Sens 2', 'Cumul'], start=2):
                    pl_total = pl_stats[direction]['Total']
                    tot_total = total_stats[direction]['Total']
                    percentage = (pl_total / tot_total * 100) if tot_total > 0 else 0
                    ws.cell(row=row, column=col_idx).value = f"{percentage:.2f}%"
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")
                row += 1
            
            row += 2  # Add spacing between tables
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        for col in ['B', 'C', 'D']:
            ws.column_dimensions[col].width = 18
    
    def _add_page_border(self, fig):
        """Add standard page spacing margins for technical report format"""
        # A4 page dimensions with 0.5 inch margins are already handled in figure setup
        # This method reserves space for consistent borders without drawing visible lines
        pass
    
    def _add_footer_with_logo(self, fig):
        """Add footer with logo image and clickable link text to PDF page"""
        logo_path = r'C:\Users\royston.fernandes\Documents\CodeVBA_fim\Nordcomptages.jpg'
        
        if not os.path.exists(logo_path):
            # If logo not found, just skip footer
            return
        
        try:
            # Load the logo image
            img = Image.open(logo_path)
            # Resize logo to fit in footer (height ~0.45 inches, maintain aspect ratio)
            logo_height_inches = 0.45
            aspect_ratio = img.width / img.height
            logo_width_inches = logo_height_inches * aspect_ratio
            
            # Convert to normalized coordinates for figure (A4: 8.27" x 11.69")
            logo_x_norm = 0.05  # 5% from left
            logo_y_norm = 0.01  # 1% from bottom
            logo_width_norm = logo_width_inches / 8.27
            logo_height_norm = logo_height_inches / 11.69
            
            # Add logo image to footer
            ax_logo = fig.add_axes([logo_x_norm, logo_y_norm, logo_width_norm, logo_height_norm])
            ax_logo.imshow(img)
            ax_logo.axis('off')
            
            # Add text "Nord Comptage Routier" next to logo
            text_x = logo_x_norm + logo_width_norm + 0.01
            text_y = logo_y_norm + (logo_height_norm / 2)
            fig.text(text_x, text_y, 'Nord Comptage Routier', 
                    fontsize=10, color='#7CBF33',
                    va='center')
        except Exception as e:
            # Silently skip footer if image loading fails
            pass
    
    def _add_pdf_link_annotation(self, pdf_path, page_num, rect_coords, url):
        """Add clickable link annotation to PDF using PyPDF2
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            rect_coords: [x1, y1, x2, y2] in page coordinates
            url: URL to link to
        """
        try:
            from PyPDF2 import PdfWriter, PdfReader
            from PyPDF2.generic import DictionaryObject, ArrayObject, NumberObject, NameObject, TextStringObject
            
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            # Add all pages
            for i, page in enumerate(reader.pages):
                writer.add_page(page)
                
                # Add link annotation to specific page
                if i == page_num:
                    # Create link annotation
                    link_annotation = DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Annot"),
                            NameObject("/Subtype"): NameObject("/Link"),
                            NameObject("/Rect"): ArrayObject([NumberObject(x) for x in rect_coords]),
                            NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
                            NameObject("/A"): DictionaryObject(
                                {
                                    NameObject("/S"): NameObject("/URI"),
                                    NameObject("/URI"): TextStringObject(url),
                                }
                            ),
                        }
                    )
                    
                    # Add annotation to page
                    if "/Annots" not in page:
                        page[NameObject("/Annots")] = ArrayObject()
                    page["/Annots"].append(writer._add_object(link_annotation))
            
            # Write modified PDF
            with open(pdf_path, 'wb') as output_file:
                writer.write(output_file)
        except Exception as e:
            # Silently fail if PyPDF2 operations don't work
            pass
    
    def _add_link_to_pdf_page(self, writer, page, rect_coords, url):
        """Add clickable link annotation to a PDF page object
        
        Args:
            writer: PyPDF2 PdfWriter instance
            page: PDF page object
            rect_coords: [x1, y1, x2, y2] in page coordinates
            url: URL to link to
        """
        try:
            from PyPDF2.generic import DictionaryObject, ArrayObject, NumberObject, NameObject, TextStringObject, IndirectObject
            
            # Ensure rectangle coordinates are floats
            rect_coords = [float(x) for x in rect_coords]
            
            # Create URI action
            uri_action = DictionaryObject()
            uri_action[NameObject("/S")] = NameObject("/URI")
            uri_action[NameObject("/URI")] = TextStringObject(url)
            
            # Create link annotation
            link_annotation = DictionaryObject()
            link_annotation[NameObject("/Type")] = NameObject("/Annot")
            link_annotation[NameObject("/Subtype")] = NameObject("/Link")
            link_annotation[NameObject("/Rect")] = ArrayObject([
                NumberObject(rect_coords[0]),
                NumberObject(rect_coords[1]),
                NumberObject(rect_coords[2]),
                NumberObject(rect_coords[3])
            ])
            link_annotation[NameObject("/Border")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)])
            link_annotation[NameObject("/A")] = uri_action
            link_annotation[NameObject("/F")] = NumberObject(4)  # No zoom flag
            
            # Get or create Annots array on the page
            if "/Annots" not in page:
                page[NameObject("/Annots")] = ArrayObject()
            
            # Add the annotation object
            annots = page["/Annots"]
            if annots is None:
                annots = ArrayObject()
                page[NameObject("/Annots")] = annots
            
            # Add annotation as indirect object
            annot_ref = writer._add_object(link_annotation)
            annots.append(annot_ref)
            
        except Exception as e:
            print(f"Error adding link annotation: {str(e)}")
            pass
    
    def _add_analysis_page_to_pdf(self, pdf, ts_data: dict):
        """Add analysis statistics page to PDF with proper A4 formatting"""
        import matplotlib.pyplot as plt
        from matplotlib.table import Table
        import matplotlib.patches as mpatches
        
        # A4 page dimensions: 8.27 x 11.69 inches (210 x 297 mm)
        # Margins: Top 25mm (0.984"), Bottom 25mm (0.984"), Left 30mm (1.181"), Right 25mm (0.984")
        fig = plt.figure(figsize=(8.27, 11.69))
        # Left: 1.181" / 8.27" = 0.1428, Width: (8.27 - 1.181 - 0.984) / 8.27 = 0.7742
        # Bottom: 0.984" / 11.69" = 0.0841, Height: (11.69 - 0.984 - 0.984) / 11.69 = 0.8318
        ax = fig.add_axes([0.143, 0.084, 0.774, 0.832])  # Left, Bottom, Width, Height
        ax.axis('off')
        
        # Add page border for technical report format
        self._add_page_border(fig)
        
        # Add title with margin from top (respect 25mm top margin)
        title_y = 0.93
        fig.text(0.5, title_y, 'Synthèse débit', 
                ha='center', fontsize=14)
        
        y_position = 0.90
        stats = self._calculate_analysis_statistics(ts_data)
        
        # Create tables for each vehicle type
        # Reduced table height to fit all 3 tables on one page
        table_height = 0.20  # Height allocated per table (reduced from 0.23)
        
        for idx, vehicle_type in enumerate(['VL', 'PL', 'Total']):
            # Prepare table data with title as first row
            table_data = [[f'Analyse - {vehicle_type}', '', '', '']]
            table_data.append(['Métrique', 'Sens 1', 'Sens 2', 'Deux sens cumulés'])
            
            metrics = [
                ('Débit total sur la période', 'Total'),
                ('Débit Moyen Journalier', 'Daily Avg'),
                ('Débit Moyen horaire', 'Hourly Avg'),
                ('Débit Moyen de Jour', 'Daily Avg Day'),
                ('Débit Moyen de Nuit', 'Daily Avg Night'),
                ('Débit Moyen Jours Ouvrés', 'Daily Avg Working'),
                ('Débit Moyen Lundi --> Samedi', 'Avg Monday-Saturday'),
                ('Débit Samedi', 'Avg Saturday'),
                ('Débit Dimanche', 'Avg Sunday'),
            ]
            
            for metric_label, metric_key in metrics:
                row = [metric_label]
                for direction in ['Sens 1', 'Sens 2', 'Cumul']:
                    value = stats[vehicle_type][direction].get(metric_key, 0)
                    row.append(str(value))
                table_data.append(row)
            
            # Add PL percentage for Total type
            if vehicle_type == 'Total':
                row = ['% PL - Bus']
                pl_stats = stats['PL']
                total_stats = stats['Total']
                for direction in ['Sens 1', 'Sens 2', 'Cumul']:
                    pl_total = pl_stats[direction]['Total']
                    tot_total = total_stats[direction]['Total']
                    percentage = (pl_total / tot_total * 100) if tot_total > 0 else 0
                    row.append(f"{percentage:.2f}%")
                table_data.append(row)
            
            # Create table with column widths: first column 2x wider than others
            # Column width ratio: 2:1:1:1 (first column is twice as wide)
            # Table bbox respects margins: right margin respected, slight left margin violation for better table width
            # Place table top very close to title (y_position), with table extending downward
            table_top = y_position - 0.01  # Small gap from title
            table_bottom = table_top - table_height  # Table extends downward from here
            table = ax.table(cellText=table_data, loc='upper left',
                           bbox=[0.055, table_bottom, 0.89, table_height - 0.015])
            table.auto_set_font_size(False)
            table.set_fontsize(8.5)
            table.scale(1, 1.5)
            
            # Set column widths: adjust first and last columns
            for i in range(len(table_data)):
                table[(i, 0)].set_width(0.42)  # First column slightly narrower
                table[(i, 1)].set_width(0.167)  # Column 2 unchanged
                table[(i, 2)].set_width(0.167)  # Column 3 unchanged
                table[(i, 3)].set_width(0.246)  # Last column wider (proportionally increased)
            
            # Style title row (row 0) - light gray background
            for i in range(4):
                table[(0, i)].set_facecolor('#E8E8E8')
                table[(0, i)].set_text_props(weight='bold', fontsize=10)
                table[(0, i)].set_edgecolor('lightgray')
                table[(0, i)].set_linewidth(0.5)
            
            # Style header row (row 1) - green background, white text
            for i in range(4):
                table[(1, i)].set_facecolor('#00B050')
                table[(1, i)].set_text_props(weight='bold', color='white', ha='center')
                table[(1, i)].set_edgecolor('black')
                table[(1, i)].set_linewidth(1)
            
            # Style data rows with alternating colors (starting from row 2)
            for i in range(2, len(table_data)):
                for j in range(4):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#F0F0F0')
                    else:
                        table[(i, j)].set_facecolor('#FFFFFF')
                    
                    # Right-align numeric columns
                    if j > 0:
                        table[(i, j)].set_text_props(ha='right')
                    else:
                        table[(i, j)].set_text_props(ha='left')
                    
                    table[(i, j)].set_edgecolor('lightgray')
                    table[(i, j)].set_linewidth(0.5)
            
            # Move y_position to bottom of table + consistent spacing for next title
            y_position = table_bottom - 0.02
        
        # Add footer with logo and text
        self._add_footer_with_logo(fig)
        
        # Add page number at bottom right (respect 25mm bottom margin)
        fig.text(0.88, 0.06, 'Page 2', ha='right', fontsize=9, style='italic', color='gray')
        
        # Save without tight bbox to preserve exact margin positioning
        pdf.savefig(fig, bbox_inches=None, pad_inches=0)
        plt.close(fig)

    
    def _add_velocity_analysis_page_to_pdf(self, pdf, ts_data: dict, direction: str = 'Sens 1', page_number: int = 3):
        """Add velocity bin analysis page to PDF with bar chart comparing VL and PL for specified direction"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Speed bin labels and colors
        speed_bins_labels = [
            '0-30', '30-40', '40-50', '50-60', '60-70', '70-80',
            '80-90', '90-100', '100-110', '110-120', '120-130', '130-150'
        ]
        # Generate 12 distinct colors for speed bins
        speed_bin_colors = plt.cm.tab20(np.linspace(0, 1, 12))
        
        # Create figure with A4 dimensions
        fig = plt.figure(figsize=(8.27, 11.69))
        
        # Add page border for technical report format
        self._add_page_border(fig)
        
        # Add title
        fig.suptitle(f'Analyses des vitesses - {direction}', fontsize=14, y=0.93)
        
        # Create three stacked subplots vertically - reduced heights with increased spacing
        # Top: Velocity bin analysis (VL vs PL)
        # Middle: Hourly breakdown by speed bins for VL
        # Bottom: Hourly breakdown by speed bins for PL
        ax1 = fig.add_axes([0.143, 0.67, 0.774, 0.20])  # Top: velocity bins
        ax2 = fig.add_axes([0.143, 0.40, 0.774, 0.20])  # Middle: VL hourly by bins
        ax3 = fig.add_axes([0.143, 0.13, 0.774, 0.20])  # Bottom: PL hourly by bins
        
        # === CHART 1: Velocity Bin Analysis (VL vs PL) ===
        # Extract real speed bin counts from raw data
        vl_counts = np.zeros(12)
        pl_counts = np.zeros(12)
        
        meta = self.current_metadata
        raw_data = meta.get('raw_data', [])
        sensor_map = meta.get('sensor_map', {})
        num_sensors = meta.get('num_sensors', 0)
        rows_per_block = meta.get('rows_per_block', 0)
        
        if raw_data and sensor_map:
            # Aggregate all speed bin counts by direction and vehicle class
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process sensors matching the specified direction
                if sensor_direction != direction:
                    continue
                
                # Sum all 12 speed bins for this sensor block - filter by direction
                for row_vals in block:
                    for i in range(12):
                        try:
                            val = row_vals[i] if i < len(row_vals) else 0
                            bin_count = int(val) if val else 0
                            if vehicle_class == 'VL':
                                vl_counts[i] += bin_count
                            elif vehicle_class == 'PL':
                                pl_counts[i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        x = np.arange(len(speed_bins_labels))
        width = 0.35
        ax1.bar(x - width/2, vl_counts, width, label='VL', color='#0066cc', alpha=0.8)
        ax1.bar(x + width/2, pl_counts, width, label='PL', color='#ff9800', alpha=0.8)
        ax1.set_ylabel('Nombre de Véhicules', fontsize=10)
        ax1.set_xlabel('Classes de vitesse (km/h)', fontsize=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(speed_bins_labels, rotation=0, ha='right', fontsize=8)
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # === CHART 2: VL Hourly Breakdown by Speed Bins ===
        vl_hourly_bins = np.zeros((24, 12))
        
        if raw_data and sensor_map:
            # Extract hourly speed bin counts for VL
            base_time = self.analysis_start_dt
            
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process if this is a VL sensor in the specified direction
                if vehicle_class == 'VL' and sensor_direction == direction:
                    freq = self.current_metadata.get('freq', 15)
                    
                    for row_idx, row_vals in enumerate(block):
                        try:
                            timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                            hour = timestamp.hour
                            
                            for i in range(12):
                                val = row_vals[i] if i < len(row_vals) else 0
                                bin_count = int(val) if val else 0
                                vl_hourly_bins[hour, i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        hours = np.arange(24)
        bottom = np.zeros(24)
        speed_ranges = ['0-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100', '100-110', '110-120', '120-130', '130-150']
        for bin_idx in range(12):
            ax2.bar(hours, vl_hourly_bins[:, bin_idx], bottom=bottom, 
                   label=f'{speed_ranges[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom += vl_hourly_bins[:, bin_idx]
        
        ax2.set_ylabel('Nombre de Véhicules (VL)', fontsize=10, labelpad=5)
        ax2.set_xlabel('Heure de la journée', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax2.legend(fontsize=6, loc='upper left', ncol=6, bbox_to_anchor=(0, 1.02))
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # === CHART 3: PL Hourly Breakdown by Speed Bins ===
        pl_hourly_bins = np.zeros((24, 12))
        
        if raw_data and sensor_map:
            # Extract hourly speed bin counts for PL
            base_time = self.analysis_start_dt
            
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process if this is a PL sensor in the specified direction
                if vehicle_class == 'PL' and sensor_direction == direction:
                    freq = self.current_metadata.get('freq', 15)
                    
                    for row_idx, row_vals in enumerate(block):
                        try:
                            timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                            hour = timestamp.hour
                            
                            for i in range(12):
                                val = row_vals[i] if i < len(row_vals) else 0
                                bin_count = int(val) if val else 0
                                pl_hourly_bins[hour, i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        bottom = np.zeros(24)
        for bin_idx in range(12):
            ax3.bar(hours, pl_hourly_bins[:, bin_idx], bottom=bottom,
                   label=f'{speed_ranges[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom += pl_hourly_bins[:, bin_idx]
        
        ax3.set_xlabel('Heure de la journée', fontsize=10)
        ax3.set_ylabel('Nombre de Véhicules (PL)', fontsize=10, labelpad=5)
        ax3.set_xticks(range(0, 24, 2))
        ax3.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax3.legend(fontsize=6, loc='upper left', ncol=6, bbox_to_anchor=(0, 1.02))
        ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # Add footer with logo and text
        self._add_footer_with_logo(fig)
        
        # Add page number at bottom right (middle of footer area vertically)
        fig.text(0.88, 0.045, f'Page {page_number}', ha='right', fontsize=9, style='italic', color='gray', va='center')
        
        # Save without tight bbox to preserve exact margin positioning
        pdf.savefig(fig, bbox_inches=None, pad_inches=0)
        plt.close(fig)

    
    def _add_velocity_analysis_to_excel_sheet(self, ws, ts_data: dict, direction: str = 'Sens 1'):
        """Add velocity analysis chart to Excel worksheet as image"""
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        from openpyxl.drawing.image import Image as XLImage
        
        # Speed bin labels and colors
        speed_bins_labels = [
            '0-30', '30-40', '40-50', '50-60', '60-70', '70-80',
            '80-90', '90-100', '100-110', '110-120', '120-130', '130-150'
        ]
        speed_bin_colors = plt.cm.tab20(np.linspace(0, 1, 12))
        
        # Create figure with A4 dimensions, similar to PDF
        fig = plt.figure(figsize=(8.27, 11.69))
        
        # Add title with direction
        fig.suptitle(f'Analyses des vitesses - {direction}', fontsize=14, y=0.93)
        
        # Create three stacked subplots vertically
        ax1 = fig.add_axes([0.143, 0.67, 0.774, 0.20])  # Top: velocity bins
        ax2 = fig.add_axes([0.143, 0.40, 0.774, 0.20])  # Middle: VL hourly by bins
        ax3 = fig.add_axes([0.143, 0.13, 0.774, 0.20])  # Bottom: PL hourly by bins
        
        # === CHART 1: Velocity Bin Analysis (VL vs PL) ===
        # Extract real speed bin counts from raw data
        vl_counts = np.zeros(12)
        pl_counts = np.zeros(12)
        
        meta = self.current_metadata
        raw_data = meta.get('raw_data', [])
        sensor_map = meta.get('sensor_map', {})
        num_sensors = meta.get('num_sensors', 0)
        rows_per_block = meta.get('rows_per_block', 0)
        
        if raw_data and sensor_map:
            # Aggregate all speed bin counts by direction and vehicle class
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Sum all 12 speed bins for this sensor block - filter by direction
                if sensor_direction != direction:
                    continue
                
                for row_vals in block:
                    for i in range(12):
                        try:
                            val = row_vals[i] if i < len(row_vals) else 0
                            bin_count = int(val) if val else 0
                            if vehicle_class == 'VL':
                                vl_counts[i] += bin_count
                            elif vehicle_class == 'PL':
                                pl_counts[i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        x = np.arange(len(speed_bins_labels))
        width = 0.35
        ax1.bar(x - width/2, vl_counts, width, label='VL', color='#0066cc', alpha=0.8)
        ax1.bar(x + width/2, pl_counts, width, label='PL', color='#ff9800', alpha=0.8)
        ax1.set_ylabel('Nombre de Véhicules', fontsize=10)
        ax1.set_xlabel('Classes de vitesse (km/h)', fontsize=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(speed_bins_labels, rotation=45, ha='right', fontsize=8)
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # === CHART 2: VL Hourly Breakdown by Speed Bins ===
        vl_hourly_bins = np.zeros((24, 12))
        
        if raw_data and sensor_map:
            # Extract hourly speed bin counts for VL
            base_time = self.analysis_start_dt
            
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process if this is a VL sensor in the specified direction
                if vehicle_class == 'VL' and sensor_direction == direction:
                    freq = self.current_metadata.get('freq', 15)
                    
                    for row_idx, row_vals in enumerate(block):
                        try:
                            timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                            hour = timestamp.hour
                            
                            for i in range(12):
                                val = row_vals[i] if i < len(row_vals) else 0
                                bin_count = int(val) if val else 0
                                vl_hourly_bins[hour, i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        hours = np.arange(24)
        bottom = np.zeros(24)
        speed_ranges = ['0-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100', '100-110', '110-120', '120-130', '130-150']
        for bin_idx in range(12):
            ax2.bar(hours, vl_hourly_bins[:, bin_idx], bottom=bottom, 
                   label=f'{speed_ranges[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom += vl_hourly_bins[:, bin_idx]
        
        ax2.set_ylabel('Nombre de Véhicules (VL)', fontsize=10, labelpad=5)
        ax2.set_xlabel('Heure de la journée', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax2.legend(fontsize=6, loc='upper left', ncol=6, bbox_to_anchor=(0, 1.02))
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # === CHART 3: PL Hourly Breakdown by Speed Bins ===
        pl_hourly_bins = np.zeros((24, 12))
        
        if raw_data and sensor_map:
            # Extract hourly speed bin counts for PL
            base_time = self.analysis_start_dt
            
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process if this is a PL sensor in the specified direction
                if vehicle_class == 'PL' and sensor_direction == direction:
                    freq = self.current_metadata.get('freq', 15)
                    
                    for row_idx, row_vals in enumerate(block):
                        try:
                            timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                            hour = timestamp.hour
                            
                            for i in range(12):
                                val = row_vals[i] if i < len(row_vals) else 0
                                bin_count = int(val) if val else 0
                                pl_hourly_bins[hour, i] += bin_count
                        except (TypeError, ValueError, IndexError):
                            pass
        
        hours = np.arange(24)
        bottom = np.zeros(24)
        for bin_idx in range(12):
            ax3.bar(hours, pl_hourly_bins[:, bin_idx], bottom=bottom, 
                   label=f'{speed_ranges[bin_idx]} km/h', color=speed_bin_colors[bin_idx], alpha=0.85)
            bottom += pl_hourly_bins[:, bin_idx]
        
        ax3.set_ylabel('Nombre de Véhicules (PL)', fontsize=10, labelpad=5)
        ax3.set_xlabel('Heure de la journée', fontsize=10)
        ax3.set_xticks(range(0, 24, 2))
        ax3.set_xticklabels([f'{h:02d}h' for h in range(0, 24, 2)], fontsize=8)
        ax3.legend(fontsize=6, loc='upper left', ncol=6, bbox_to_anchor=(0, 1.02))
        ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
        
        # Convert figure to image and embed in Excel
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Add image to Excel worksheet
        img = XLImage(img_buffer)
        img.width = 545   # ~7.27 inches at 96 DPI
        img.height = 643  # ~10.69 inches at 96 DPI
        ws.add_image(img, 'A1')

    
    def _generate_timeseries_data(self) -> dict:
        """
        Generate time series data for analysis.
        Returns dict with 'VL', 'PL', 'Total' keys, each containing timeseries data grouped by direction.
        Filters data by analysis_start_dt and analysis_end_dt if set.
        """
        if self.current_df is None or self.current_metadata is None:
            raise ValueError("No data loaded")
        
        df = self.current_df.copy()
        
        # Filter by selected date range if set
        if self.analysis_start_dt is not None and self.analysis_end_dt is not None:
            df = df[
                (df['timestamp'] >= self.analysis_start_dt) & 
                (df['timestamp'] <= self.analysis_end_dt)
            ]
        meta = self.current_metadata
        
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            raise ValueError("No timestamp column in data")
        
        # Group by timestamp and direction, sum the counts
        ts_data = {
            'VL': {},
            'PL': {},
            'Total': {}
        }
        
        # VL data
        vl_data = df[df['vehicle_class'] == 'VL'].groupby(['timestamp', 'direction'])['count'].sum().reset_index()
        for direction in vl_data['direction'].unique():
            dir_data = vl_data[vl_data['direction'] == direction].sort_values('timestamp')
            ts_data['VL'][direction] = dir_data
        
        # Calculate cumulative (total) for VL
        vl_cumul = df[df['vehicle_class'] == 'VL'].groupby('timestamp')['count'].sum().reset_index()
        vl_cumul['direction'] = 'Cumul'
        ts_data['VL']['Cumul'] = vl_cumul
        
        # PL data
        pl_data = df[df['vehicle_class'] == 'PL'].groupby(['timestamp', 'direction'])['count'].sum().reset_index()
        for direction in pl_data['direction'].unique():
            dir_data = pl_data[pl_data['direction'] == direction].sort_values('timestamp')
            ts_data['PL'][direction] = dir_data
        
        # Calculate cumulative (total) for PL
        pl_cumul = df[df['vehicle_class'] == 'PL'].groupby('timestamp')['count'].sum().reset_index()
        pl_cumul['direction'] = 'Cumul'
        ts_data['PL']['Cumul'] = pl_cumul
        
        # Total vehicles (VL + PL)
        total_data = df.groupby(['timestamp', 'direction'])['count'].sum().reset_index()
        for direction in total_data['direction'].unique():
            dir_data = total_data[total_data['direction'] == direction].sort_values('timestamp')
            ts_data['Total'][direction] = dir_data
        
        # Calculate cumulative (total) for all vehicles
        total_cumul = df.groupby('timestamp')['count'].sum().reset_index()
        total_cumul['direction'] = 'Cumul'
        ts_data['Total']['Cumul'] = total_cumul
        
        return ts_data
    
    def _plot_timeseries(self, ax, ts_data: dict, vehicle_class: str, title: str, is_last_subplot: bool = False):
        """
        Plot time series graph for a specific vehicle class.
        
        Args:
            ax: matplotlib axis to plot on
            ts_data: dict with timeseries data
            vehicle_class: 'VL', 'PL', or 'Total'
            title: title for the graph
            is_last_subplot: True if this is the last (bottom) subplot
        """
        # Color scheme (colorblind-proof)
        colors = {
            'Sens 1': '#0173B2',  # blue
            'Sens 2': '#DE8F05',  # orange
            'Cumul': '#CC78BC'    # purple
        }
        
        line_styles = {
            'Sens 1': '-',
            'Sens 2': '-',
            'Cumul': '-'
        }
        
        # Plot data for each direction without markers
        for direction, df_dir in ts_data[vehicle_class].items():
            if direction == 'Cumul':  # Skip cumulative line
                continue
            if df_dir is not None and not df_dir.empty:
                ax.plot(
                    df_dir['timestamp'],
                    df_dir['count'],
                    label=direction,
                    color=colors.get(direction, '#000000'),
                    linestyle=line_styles.get(direction, '-'),
                    linewidth=1.0,
                    alpha=0.85
                )
        
        # Set x-axis limits to start at first available datetime
        all_timestamps = []
        for direction, df_dir in ts_data[vehicle_class].items():
            if direction == 'Cumul':  # Skip cumulative data
                continue
            if df_dir is not None and not df_dir.empty:
                all_timestamps.extend(df_dir['timestamp'].tolist())
        
        if all_timestamps:
            min_time = min(all_timestamps)
            max_time = max(all_timestamps)
            # Add small padding (1% of the range) to the right side
            time_range = max_time - min_time
            ax.set_xlim(left=min_time, right=max_time + time_range * 0.01)
            
            # Create custom tick positions: first datetime + first datetime of each subsequent day
            tick_positions = [min_time]
            current_day = min_time.replace(hour=0, minute=0, second=0, microsecond=0)
            next_day = current_day + timedelta(days=1)
            
            while next_day <= max_time:
                tick_positions.append(next_day)
                next_day += timedelta(days=1)
            
            # Set custom tick positions
            ax.set_xticks(tick_positions)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
        else:
            # Fallback if no timestamps available
            ax.xaxis.set_major_locator(MaxNLocator(nbins=12))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
        
        # Set minor ticks (every 1 hour, no labels)
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_minor_formatter(NullFormatter())
        
        # Make tick markers longer
        ax.tick_params(axis='x', which='major', length=12, width=1.0)
        ax.tick_params(axis='x', which='minor', length=7, width=1.0)
        
        # Show tick markers on all subplots, but only show tick labels on the last subplot
        if not is_last_subplot:
            # Hide tick labels but keep tick markers visible
            ax.tick_params(axis='x', labelbottom=False, bottom=True, which='both')
        else:
            # Show all ticks and labels, rotated to 90 degrees on last subplot
            ax.tick_params(axis='x', labelbottom=True, bottom=True, which='both')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
            plt.setp(ax.xaxis.get_minorticklabels(), rotation=90)
        
        # Labels and title
        ax.set_ylabel('Débit', fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.7)
        ax.grid(True, axis='x', which='major', alpha=0.3, linestyle='-', linewidth=0.7)
        legend = ax.legend(loc='upper left', fontsize=10)
        legend.set_alpha(0.8)  # Make legend slightly transparent
        ax.set_ylim(bottom=0)  # Set lower limit to 0 (must be after all other y-axis operations)
        
        # Only show x-axis label on the last subplot
        if is_last_subplot:
            ax.set_xlabel('Date / Heure', fontsize=10)


    def _add_mean_speed_analysis_page_to_pdf(self, pdf, ts_data: dict, direction: str = 'Sens 1'):
        """Add mean speed analysis page to PDF with time series of mean speeds for VL and PL"""
        # A4 page dimensions: 8.27 x 11.69 inches (210 x 297 mm)
        fig = plt.figure(figsize=(8.27, 11.69))
        
        # Add page border for technical report format
        self._add_page_border(fig)
        
        # Create three subplots vertically
        # Subplot 1: Mean speed for Sens 1
        # Subplot 2: Mean speed for Sens 2
        # Subplot 3: Mean débit with dual y-axes (VL left, PL right) for Sens 1 & 2
        ax1 = fig.add_axes([0.143, 0.66, 0.774, 0.18])  # Top: Sens 1 mean speeds
        ax2 = fig.add_axes([0.143, 0.42, 0.774, 0.18])  # 2nd: Sens 2 mean speeds
        ax3 = fig.add_axes([0.143, 0.18, 0.774, 0.18])  # Bottom: Débit with dual axes
        
        # === SUBPLOT 1: Mean Speed by Hour of Day for VL and PL ===
        # Calculate real mean speeds from actual data using speed bins
        hours = np.arange(24)
        vl_mean_by_hour = np.zeros(24)
        pl_mean_by_hour = np.zeros(24)
        
        # Extract speed data from metadata
        meta = self.current_metadata
        raw_data = meta.get('raw_data', []) if meta else []
        sensor_map = meta.get('sensor_map', {}) if meta else {}
        num_sensors = meta.get('num_sensors', 0) if meta else 0
        rows_per_block = meta.get('rows_per_block', 0) if meta else 0
        speed_bin_centers = meta.get('speed_bin_centers', []) if meta else []
        freq = meta.get('freq', 15) if meta else 15
        
        if raw_data and sensor_map and speed_bin_centers:
            # Track global hourly accumulators: hour -> {numerator: sum(count*speed), denominator: sum(count)}
            # Volume-weighted across ALL occurrences of each hour in the entire dataset
            vl_hourly_numerator = {h: 0 for h in range(24)}  # sum of count*speed across all days
            vl_hourly_denominator = {h: 0 for h in range(24)}  # total count across all days
            pl_hourly_numerator = {h: 0 for h in range(24)}
            pl_hourly_denominator = {h: 0 for h in range(24)}
            
            # Process each sensor block
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process sensors matching the specified direction
                if sensor_direction != direction:
                    continue
                
                # Process each row in this sensor's block
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    # Accumulate volume-weighted speeds for this hour across all days
                    for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                        
                        if vehicle_class == 'VL':
                            vl_hourly_numerator[hour] += count * speed_center
                            vl_hourly_denominator[hour] += count
                        elif vehicle_class == 'PL':
                            pl_hourly_numerator[hour] += count * speed_center
                            pl_hourly_denominator[hour] += count
            
            # Calculate mean speeds for each hour: total(count*speed) / total(count)
            for hour in range(24):
                if vl_hourly_denominator[hour] > 0:
                    vl_mean_by_hour[hour] = vl_hourly_numerator[hour] / vl_hourly_denominator[hour]
                if pl_hourly_denominator[hour] > 0:
                    pl_mean_by_hour[hour] = pl_hourly_numerator[hour] / pl_hourly_denominator[hour]
            
            # DEBUG: Print calculated values
            print("\n=== PAGE 4 CALCULATED SPEEDS ===")
            for hour in range(24):
                if vl_mean_by_hour[hour] > 0 or pl_mean_by_hour[hour] > 0:
                    vl_str = f"{vl_mean_by_hour[hour]:.1f}" if vl_mean_by_hour[hour] > 0 else "--"
                    pl_str = f"{pl_mean_by_hour[hour]:.1f}" if pl_mean_by_hour[hour] > 0 else "--"
                    print(f"Hour {hour:02d}: VL={vl_str} | PL={pl_str}")
            
            # Plot with real data (no alpha transparency)
            ax1.plot(hours, vl_mean_by_hour, 
                    label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5)
            ax1.plot(hours, pl_mean_by_hour, 
                    label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5)
            # Calculate dynamic y-limits from data
            all_values = np.concatenate([vl_mean_by_hour[vl_mean_by_hour > 0], pl_mean_by_hour[pl_mean_by_hour > 0]])
            if len(all_values) > 0:
                min_val = np.min(all_values)
                max_val = np.max(all_values)
                y_lower = 0  # Always set lower limit to 0
                y_upper = round(max_val + 5)
            else:
                y_lower = 0
                y_upper = 10
        else:
            # Fallback if no data available
            ax1.plot(hours, vl_mean_by_hour, 
                    label='VL (Véhicules Légers)', color='#0066cc', linewidth=1.0, marker='o', markersize=5, alpha=0.3)
            ax1.plot(hours, pl_mean_by_hour, 
                    label='PL (Poids Lourds)', color='#ff9800', linewidth=1.0, marker='s', markersize=5, alpha=0.3)
            y_lower = 0
            y_upper = 10
        
        ax1.set_ylabel('Vitesse moyenne (km/h)', fontsize=10, labelpad=5)
        ax1.set_xlabel('Heure du jour', fontsize=10)
        ax1.set_title('Vitesse moyenne par heure - Sens 1', fontsize=10)
        ax1.set_xticks(range(0, 24, 2))
        ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax1.set_xlim(-0.5, 23.5)
        ax1.margins(y=0.1)  # Add 10% margin above and below
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax1.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        ax1.set_ylim(y_lower, y_upper)  # Set dynamic limits based on data
        
        # === SUBPLOT 2: Mean Speed by Hour of Day for VL and PL for Sens 2 ===
        # Calculate mean speeds for Sens 2
        vl_mean_by_hour_sens2 = np.zeros(24)
        pl_mean_by_hour_sens2 = np.zeros(24)
        
        if raw_data and sensor_map and speed_bin_centers:
            # Track global hourly accumulators: hour -> {numerator: sum(count*speed), denominator: sum(count)}
            # Volume-weighted across ALL occurrences of each hour in the entire dataset
            vl_hourly_numerator_2 = {h: 0 for h in range(24)}
            vl_hourly_denominator_2 = {h: 0 for h in range(24)}
            pl_hourly_numerator_2 = {h: 0 for h in range(24)}
            pl_hourly_denominator_2 = {h: 0 for h in range(24)}
            
            # Process each sensor block for Sens 2
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Only process sensors matching Sens 2
                if sensor_direction != 'Sens 2':
                    continue
                
                # Process each row in this sensor's block
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    # Accumulate weighted speeds for this hour across all days
                    for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                        
                        if vehicle_class == 'VL':
                            vl_hourly_numerator_2[hour] += count * speed_center
                            vl_hourly_denominator_2[hour] += count
                        elif vehicle_class == 'PL':
                            pl_hourly_numerator_2[hour] += count * speed_center
                            pl_hourly_denominator_2[hour] += count
            
            # Calculate mean speeds for each hour: total(count*speed) / total(count)
            for hour in range(24):
                if vl_hourly_denominator_2[hour] > 0:
                    vl_mean_by_hour_sens2[hour] = vl_hourly_numerator_2[hour] / vl_hourly_denominator_2[hour]
                if pl_hourly_denominator_2[hour] > 0:
                    pl_mean_by_hour_sens2[hour] = pl_hourly_numerator_2[hour] / pl_hourly_denominator_2[hour]
            
            # Plot with real data (no alpha transparency)
            ax2.plot(hours, vl_mean_by_hour_sens2, 
                    label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5)
            ax2.plot(hours, pl_mean_by_hour_sens2, 
                    label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5)
            # Calculate dynamic y-limits from data
            all_values = np.concatenate([vl_mean_by_hour_sens2[vl_mean_by_hour_sens2 > 0], pl_mean_by_hour_sens2[pl_mean_by_hour_sens2 > 0]])
            if len(all_values) > 0:
                min_val = np.min(all_values)
                max_val = np.max(all_values)
                y_lower_2 = 0  # Always set lower limit to 0
                y_upper_2 = round(max_val + 5)
            else:
                y_lower_2 = 0
                y_upper_2 = 10
        else:
            # Fallback if no data available
            ax2.plot(hours, vl_mean_by_hour_sens2, 
                    label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5, alpha=0.3)
            ax2.plot(hours, pl_mean_by_hour_sens2, 
                    label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5, alpha=0.3)
            y_lower_2 = 0
            y_upper_2 = 10
        
        ax2.set_ylabel('Vitesse moyenne (km/h)', fontsize=10, labelpad=5)
        ax2.set_xlabel('Heure du jour', fontsize=10)
        ax2.set_title('Vitesse moyenne par heure - Sens 2 (moyenne sur tous les jours)', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax2.set_xlim(-0.5, 23.5)
        ax2.margins(y=0.1)  # Add 10% margin above and below
        ax2.legend(fontsize=8, loc='upper right')
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax2.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        ax2.set_ylim(y_lower_2, y_upper_2)  # Set dynamic limits based on data
        
        # === SUBPLOT 3: Mean Débit with Dual Y-Axes (VL left, PL right) ===
        # Calculate hourly mean débit across all days for both Sens 1 and Sens 2
        # Débit = total(count) / number_of_times_that_hour_appears_in_dataset
        vl_debit_sens1 = np.zeros(24)
        pl_debit_sens1 = np.zeros(24)
        vl_debit_sens2 = np.zeros(24)
        pl_debit_sens2 = np.zeros(24)
        
        if raw_data and sensor_map:
            # Track total counts and number of occurrences per hour per direction per vehicle class
            vl_total_counts_s1 = {h: 0 for h in range(24)}  # sum of all counts across all days
            vl_occurrences_s1 = {h: 0 for h in range(24)}  # number of times hour appears
            pl_total_counts_s1 = {h: 0 for h in range(24)}
            pl_occurrences_s1 = {h: 0 for h in range(24)}
            vl_total_counts_s2 = {h: 0 for h in range(24)}
            vl_occurrences_s2 = {h: 0 for h in range(24)}
            pl_total_counts_s2 = {h: 0 for h in range(24)}
            pl_occurrences_s2 = {h: 0 for h in range(24)}
            
            # Process each sensor block
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                sensor_direction = sensor_info.get('direction', 'Sens 1')
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Process each row in this sensor's block
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    # Sum all speed bins to get total vehicle count for this hour
                    hour_count = 0
                    for i in range(min(12, len(row_vals))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        hour_count += count
                    
                    # Accumulate by direction and vehicle class
                    if sensor_direction == 'Sens 1':
                        if vehicle_class == 'VL':
                            vl_total_counts_s1[hour] += hour_count
                            vl_occurrences_s1[hour] += 1
                        elif vehicle_class == 'PL':
                            pl_total_counts_s1[hour] += hour_count
                            pl_occurrences_s1[hour] += 1
                    elif sensor_direction == 'Sens 2':
                        if vehicle_class == 'VL':
                            vl_total_counts_s2[hour] += hour_count
                            vl_occurrences_s2[hour] += 1
                        elif vehicle_class == 'PL':
                            pl_total_counts_s2[hour] += hour_count
                            pl_occurrences_s2[hour] += 1
            
            # Calculate mean débit for each hour: total(count) / number_of_occurrences
            for hour in range(24):
                if vl_occurrences_s1[hour] > 0:
                    vl_debit_sens1[hour] = vl_total_counts_s1[hour] / vl_occurrences_s1[hour]
                if pl_occurrences_s1[hour] > 0:
                    pl_debit_sens1[hour] = pl_total_counts_s1[hour] / pl_occurrences_s1[hour]
                if vl_occurrences_s2[hour] > 0:
                    vl_debit_sens2[hour] = vl_total_counts_s2[hour] / vl_occurrences_s2[hour]
                if pl_occurrences_s2[hour] > 0:
                    pl_debit_sens2[hour] = pl_total_counts_s2[hour] / pl_occurrences_s2[hour]
        
        # Create dual y-axis plot
        ax3_twin = ax3.twinx()
        
        # Plot VL data on left y-axis (ax3) with continuous line for Sens 1 and dashed for Sens 2
        line1_vl = ax3.plot(hours, vl_debit_sens1, 
                    label='VL Sens 1', color='#0066cc', linewidth=1.0, linestyle='-', marker='o', markersize=4)
        line2_vl = ax3.plot(hours, vl_debit_sens2, 
                    label='VL Sens 2', color='#0066cc', linewidth=1.0, linestyle='--', marker='o', markersize=4)
        
        # Plot PL data on right y-axis (ax3_twin) with continuous line for Sens 1 and dashed for Sens 2
        line1_pl = ax3_twin.plot(hours, pl_debit_sens1, 
                    label='PL Sens 1', color='#ff9800', linewidth=1.0, linestyle='-', marker='s', markersize=4)
        line2_pl = ax3_twin.plot(hours, pl_debit_sens2, 
                    label='PL Sens 2', color='#ff9800', linewidth=1.0, linestyle='--', marker='s', markersize=4)
        
        # Calculate dynamic y-limits
        vl_values = np.concatenate([vl_debit_sens1[vl_debit_sens1 > 0], vl_debit_sens2[vl_debit_sens2 > 0]])
        pl_values = np.concatenate([pl_debit_sens1[pl_debit_sens1 > 0], pl_debit_sens2[pl_debit_sens2 > 0]])
        
        if len(vl_values) > 0:
            vl_max = np.max(vl_values)
            vl_y_upper = round(vl_max * 1.1)
        else:
            vl_y_upper = 100
        
        if len(pl_values) > 0:
            pl_max = np.max(pl_values)
            pl_y_upper = round(pl_max * 1.1)
        else:
            pl_y_upper = 100
        
        # Configure left y-axis (VL)
        ax3.set_ylabel('Débit VL', fontsize=10, labelpad=5, color='#0066cc')
        ax3.tick_params(axis='y', labelcolor='#0066cc', labelsize=9)
        ax3.set_ylim(0, vl_y_upper)
        
        # Configure right y-axis (PL)
        ax3_twin.set_ylabel('Débit PL', fontsize=10, labelpad=5, color='#ff9800')
        ax3_twin.tick_params(axis='y', labelcolor='#ff9800', labelsize=9)
        ax3_twin.set_ylim(0, pl_y_upper)
        
        # Configure x-axis
        ax3.set_xlabel('Heure du jour', fontsize=10)
        ax3.set_title('Débit moyen par heure - Sens 1 (ligne continue) & Sens 2 (ligne tiretée)', fontsize=10)
        ax3.set_xticks(range(0, 24, 2))
        ax3.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax3.set_xlim(-0.5, 23.5)
        ax3.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax3.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Combine legends from both axes
        lines = line1_vl + line2_vl + line1_pl + line2_pl
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, fontsize=8, loc='upper left')
        
        # Add footer with logo and text
        self._add_footer_with_logo(fig)
        
        # Add page number at bottom right
        fig.text(0.88, 0.045, 'Page 5', ha='right', fontsize=9, style='italic', color='gray', va='center')
        
        # Save without tight bbox to preserve exact margin positioning
        pdf.savefig(fig, bbox_inches=None, pad_inches=0)
        plt.close(fig)

    
    def _add_mean_speed_analysis_to_excel_sheet(self, ws, ts_data: dict):
        """Add mean speed analysis chart to Excel worksheet as image"""
        from openpyxl.drawing.image import Image as XLImage
        
        # Create figure with A4 dimensions
        fig = plt.figure(figsize=(8.27, 11.69))
        
        # Add title
        fig.suptitle('Analyse des Vitesses Moyennes', fontsize=14, y=0.93)
        
        # Create three subplots vertically
        ax1 = fig.add_axes([0.143, 0.60, 0.774, 0.25])  # Top: mean speeds over time
        ax2 = fig.add_axes([0.143, 0.35, 0.774, 0.20])  # Middle
        ax3 = fig.add_axes([0.143, 0.10, 0.774, 0.20])  # Bottom
        
        # === SUBPLOT 1: Mean Speed by Hour of Day for VL and PL ===
        # Calculate real mean speeds from actual data using speed bins
        hours = np.arange(24)
        vl_mean_by_hour = np.zeros(24)
        pl_mean_by_hour = np.zeros(24)
        
        # Extract speed data from metadata
        meta = self.current_metadata
        raw_data = meta.get('raw_data', [])
        sensor_map = meta.get('sensor_map', {})
        num_sensors = meta.get('num_sensors', 0)
        rows_per_block = meta.get('rows_per_block', 0)
        speed_bin_centers = meta.get('speed_bin_centers', [])
        freq = meta.get('freq', 15)
        
        if raw_data and sensor_map and speed_bin_centers:
            # Initialize accumulators for each hour (all data combined)
            vl_numerator = np.zeros(24)  # sum of count*speed for VL
            vl_denominator = np.zeros(24)  # total count for VL
            pl_numerator = np.zeros(24)  # sum of count*speed for PL
            pl_denominator = np.zeros(24)  # total count for PL
            
            # Process each sensor block
            base_time = self.analysis_start_dt
            for sensor_id in range(num_sensors):
                start_row = sensor_id * rows_per_block
                end_row = min(start_row + rows_per_block, len(raw_data))
                
                if start_row >= len(raw_data):
                    break
                
                block = raw_data[start_row:end_row]
                sensor_info = sensor_map.get(sensor_id, {})
                vehicle_class = sensor_info.get('class', 'ALL')
                
                # Process each row in this sensor's block
                for row_idx, row_vals in enumerate(block):
                    timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                    hour = timestamp.hour
                    
                    # Calculate weighted speed (sum of count * speed_center)
                    for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                        count = int(row_vals[i]) if i < len(row_vals) else 0
                        speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                        
                        # Only accumulate for matching vehicle class - don't double count 'ALL'
                        if vehicle_class == 'VL':
                            vl_numerator[hour] += count * speed_center
                            vl_denominator[hour] += count
                        elif vehicle_class == 'PL':
                            pl_numerator[hour] += count * speed_center
                            pl_denominator[hour] += count
            
            # Calculate mean speeds for each hour
            vl_mean_by_hour = np.zeros(24)
            pl_mean_by_hour = np.zeros(24)
            for hour in range(24):
                if vl_denominator[hour] > 0:
                    vl_mean_by_hour[hour] = vl_numerator[hour] / vl_denominator[hour]
                if pl_denominator[hour] > 0:
                    pl_mean_by_hour[hour] = pl_numerator[hour] / pl_denominator[hour]
            
            # DEBUG: Print calculated values
            print("\n=== PAGE 4 CALCULATED SPEEDS ===")
            for hour in range(24):
                if vl_denominator[hour] > 0 or pl_denominator[hour] > 0:
                    vl_str = f"{vl_mean_by_hour[hour]:.1f}" if vl_denominator[hour] > 0 else "--"
                    pl_str = f"{pl_mean_by_hour[hour]:.1f}" if pl_denominator[hour] > 0 else "--"
                    print(f"Hour {hour:02d}: VL={vl_str} | PL={pl_str}")
            
            # Plot with real data
            ax1.plot(hours, vl_mean_by_hour, 
                    label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5)
            ax1.plot(hours, pl_mean_by_hour, 
                    label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5)
            # Calculate dynamic y-limits from data
            all_values = np.concatenate([vl_mean_by_hour[vl_denominator > 0], pl_mean_by_hour[pl_denominator > 0]])
            if len(all_values) > 0:
                min_val = np.min(all_values)
                max_val = np.max(all_values)
                y_lower = 0  # Always set lower limit to 0
                y_upper = round(max_val + 5)
            else:
                y_lower = 0
                y_upper = 10
        else:
            # Fallback if no data available
            ax1.plot(hours, [0]*24, label='VL', color='#0066cc', linewidth=1.0, marker='o', markersize=5, alpha=0.3)
            ax1.plot(hours, [0]*24, label='PL', color='#ff9800', linewidth=1.0, marker='s', markersize=5, alpha=0.3)
            y_lower = 0
            y_upper = 10
        
        ax1.set_ylabel('Vitesse moyenne (km/h)', fontsize=10, labelpad=5)
        ax1.set_xlabel('Heure du jour', fontsize=10)
        ax1.set_title('Vitesse moyenne par heure (moyenne sur tous les jours)', fontsize=10)
        ax1.set_xticks(range(0, 24, 2))
        ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax1.set_xlim(-0.5, 23.5)
        ax1.margins(y=0.1)
        ax1.legend(fontsize=9, loc='upper right')
        ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax1.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        ax1.set_ylim(y_lower, y_upper)  # Set dynamic limits based on data
        
        # === SUBPLOT 2: Median Speed by Hour of Day for VL and PL ===
        if raw_data and sensor_map and speed_bin_centers:
            # Initialize accumulators for median calculation
            vl_median_by_hour = np.zeros(24)
            pl_median_by_hour = np.zeros(24)
            
            # For each hour, calculate the weighted median from the distribution
            for hour in range(24):
                # Get counts for this hour from both VL and PL
                vl_counts = []  # (speed_center, count) pairs
                pl_counts = []  # (speed_center, count) pairs
                
                # Rebuild distribution for this hour from all measurements
                temp_vl_num = np.zeros(12)
                temp_vl_den = 0
                temp_pl_num = np.zeros(12)
                temp_pl_den = 0
                
                base_time = self.analysis_start_dt
                for sensor_id in range(num_sensors):
                    start_row = sensor_id * rows_per_block
                    end_row = min(start_row + rows_per_block, len(raw_data))
                    
                    if start_row >= len(raw_data):
                        break
                    
                    block = raw_data[start_row:end_row]
                    sensor_info = sensor_map.get(sensor_id, {})
                    vehicle_class = sensor_info.get('class', 'ALL')
                    
                    for row_idx, row_vals in enumerate(block):
                        timestamp = base_time + timedelta(minutes=freq * (start_row + row_idx))
                        if timestamp.hour == hour:
                            for i in range(min(12, len(row_vals), len(speed_bin_centers))):
                                count = int(row_vals[i]) if i < len(row_vals) else 0
                                speed_center = speed_bin_centers[i] if i < len(speed_bin_centers) else 0
                                
                                if vehicle_class == 'VL':
                                    vl_counts.extend([(speed_center, 1)] * count)
                                    temp_vl_num[i] += count
                                    temp_vl_den += count
                                elif vehicle_class == 'PL':
                                    pl_counts.extend([(speed_center, 1)] * count)
                                    temp_pl_num[i] += count
                                    temp_pl_den += count
                
                # Calculate weighted median for VL
                if len(vl_counts) > 0:
                    speeds = [s for s, _ in vl_counts]
                    vl_median_by_hour[hour] = np.median(speeds)
                
                # Calculate weighted median for PL
                if len(pl_counts) > 0:
                    speeds = [s for s, _ in pl_counts]
                    pl_median_by_hour[hour] = np.median(speeds)
            
            # Plot median data
            ax2.plot(hours, vl_median_by_hour, 
                    label='VL', color='#0066cc', linewidth=1.0, marker='^', markersize=5)
            ax2.plot(hours, pl_median_by_hour, 
                    label='PL', color='#ff9800', linewidth=1.0, marker='D', markersize=5)
            # Calculate dynamic y-limits from data
            all_values = np.concatenate([vl_median_by_hour[vl_median_by_hour > 0], pl_median_by_hour[pl_median_by_hour > 0]])
            if len(all_values) > 0:
                min_val = np.min(all_values)
                max_val = np.max(all_values)
                y_lower_2 = max(0, round(min_val - 5))
                y_upper_2 = round(max_val + 5)
            else:
                y_lower_2 = 0
                y_upper_2 = 10
        else:
            # Fallback if no data available
            ax2.plot(hours, [0]*24, label='VL', color='#0066cc', linewidth=1.0, marker='^', markersize=5, alpha=0.3)
            ax2.plot(hours, [0]*24, label='PL', color='#ff9800', linewidth=1.0, marker='D', markersize=5, alpha=0.3)
            y_lower_2 = 0
            y_upper_2 = 10
        
        ax2.set_ylabel('Vitesse médiane (km/h)', fontsize=10, labelpad=5)
        ax2.set_xlabel('Heure du jour', fontsize=10)
        ax2.set_title('Vitesse médiane par heure (médiane sur tous les jours)', fontsize=10)
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=8)
        ax2.set_xlim(-0.5, 23.5)
        ax2.margins(y=0.1)
        ax2.legend(fontsize=9, loc='upper right')
        ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
        ax2.grid(True, axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
        ax2.set_ylim(y_lower_2, y_upper_2)  # Set dynamic limits based on data
        
        # === SUBPLOT 3: Placeholder ===
        ax3.text(0.5, 0.5, 'Subplot 3\n(À définir)', 
                ha='center', va='center', fontsize=12, transform=ax3.transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax3.axis('off')
        
        # Convert figure to image and embed in Excel
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Add image to Excel worksheet
        img = XLImage(img_buffer)
        img.width = 545   # ~7.27 inches at 96 DPI
        img.height = 643  # ~10.69 inches at 96 DPI
        ws.add_image(img, 'A1')


class FIMLoaderWindow(QMainWindow):
    """Main window for FIM File Loader"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FIM File Loader - Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the metadata panel as the central widget
        self.metadata_panel = MetadataPanel()
        self.setCentralWidget(self.metadata_panel)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = FIMLoaderWindow()
    window.show()
    sys.exit(app.exec_())
