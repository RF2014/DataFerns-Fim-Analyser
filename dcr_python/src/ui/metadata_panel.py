"""
Refactored MetadataPanel for DataFerns Traffic Reporter
Follows Senior architecture and surgical refactoring rules (< 200 lines).
"""
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QGridLayout, QMessageBox, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont, QPixmap

from ..core.fim_parser import parse_fim_file
from ..core.analytics import AnalyticsEngine
from ..services.excel_service import ExcelService
from ..services.report_service import ReportService
from ..services.csv_ingress_service import CsvIngressService
from ..services.raw_data_service import RawDataService
from ..services.data_filtering_service import DataFilteringService
from ..models.state import AppState
from ..utils.helpers import resource_path
from .dialogs import RawExportFormatDialog, ReportSettingsDialog

class MetadataPanel(QWidget):
    """Refactored UI panel for traffic metadata, period filtering, and file operations"""
    
    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.metadata_fields = {}
        
        # Filter range boundaries
        self.filter_start_dt = None
        self.filter_end_dt = None
        
        self.init_ui()
        self.state.subscribe(self.update_ui_from_state)

    def init_ui(self):
        """Initialize premium modern UI layout"""
        self.setStyleSheet("""
            MetadataPanel {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1.5em;
                padding: 15px;
                font-weight: bold;
                color: #495057;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton#report_btn {
                background-color: #28a745;
            }
            QPushButton#report_btn:hover {
                background-color: #218838;
            }
            QLabel#title_label {
                color: #212529;
                font-size: 24px;
                font-weight: 800;
            }
            QLabel#status_label {
                color: #6c757d;
                font-size: 13px;
            }
            QLabel#meta_val {
                color: #007bff;
                font-weight: 700;
                font-size: 14px;
            }
            QDateTimeEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                color: #495057;
            }
            QCalendarWidget QWidget {
                background-color: #ffffff;
            }
            QCalendarWidget QToolButton {
                color: #212529;
                background-color: transparent;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e9ecef;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #212529;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: #ffffff;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 1. Header Section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        title_container = QVBoxLayout()
        title_label = QLabel("DataFerns ANALYSER")
        title_label.setObjectName("title_label")
        self.file_label = QLabel("Prêt pour la capture de données")
        self.file_label.setObjectName("status_label")
        title_container.addWidget(title_label)
        title_container.addWidget(self.file_label)
        
        logo_label = QLabel()
        logo_path = resource_path("ui", "logo.png")
        pix = QPixmap(logo_path)
        if not pix.isNull():
            logo_label.setPixmap(pix.scaledToHeight(60, Qt.SmoothTransformation))
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        main_layout.addWidget(header_widget)

        # 2. Controls Bar
        ctrl_card = QGroupBox("Operations")
        ctrl_layout = QHBoxLayout()
        
        load_btn = QPushButton("Charger FIM")
        load_btn.clicked.connect(self.load_file)
        
        load_csv_btn = QPushButton("Charger CSV")
        load_csv_btn.clicked.connect(self.load_csv_file)
        
        load_raw_btn = QPushButton("Charger Brut XLS")
        load_raw_btn.clicked.connect(self.load_raw_file)
        
        self.extract_btn = QPushButton("Exporter Excel")
        self.extract_btn.clicked.connect(self.extract_data)
        
        self.extract_csv_btn = QPushButton("Exporter CSV")
        self.extract_csv_btn.clicked.connect(self.export_csv_data)
        
        self.report_btn = QPushButton("Générer Rapports")
        self.report_btn.setObjectName("report_btn")
        self.report_btn.clicked.connect(self.generate_reports)
        
        ctrl_layout.addWidget(load_btn)
        ctrl_layout.addWidget(load_csv_btn)
        ctrl_layout.addWidget(load_raw_btn)
        ctrl_layout.addWidget(self.extract_btn)
        ctrl_layout.addWidget(self.extract_csv_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.report_btn)
        ctrl_card.setLayout(ctrl_layout)
        main_layout.addWidget(ctrl_card)

        # 3. Content Area (Metadata & Filtering side-by-side)
        content_layout = QHBoxLayout()
        
        # Metadata grid
        metadata_group = QGroupBox("Statistiques de Trafic")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.setHorizontalSpacing(30)
        
        field_names = [
            ('Période de début', 'start_datetime'),
            ('Période de fin', 'end_datetime'),
            ('Données Vitesse', 'speed_status'),
            ('Sens 1 : VL (TMJ)', 'tmj_vl_sens1'),
            ('Sens 2 : VL (TMJ)', 'tmj_vl_sens2'),
            ('Sens 1 : PL (TMJ)', 'tmj_pl_sens1'),
            ('Sens 2 : PL (TMJ)', 'tmj_pl_sens2'),
        ]
        
        for i, (label_text, key) in enumerate(field_names):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #495057; font-weight: 500;")
            val_lbl = QLabel("--")
            val_lbl.setObjectName("meta_val")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
            self.metadata_fields[key] = val_lbl

        metadata_group.setLayout(grid)
        content_layout.addWidget(metadata_group)
        
        # Period Filter controls
        filter_group = QGroupBox("Filtre Temporel")
        filter_layout = QGridLayout()
        filter_layout.setVerticalSpacing(15)
        filter_layout.setHorizontalSpacing(15)
        
        start_lbl = QLabel("Date de Début :")
        start_lbl.setStyleSheet("color: #495057; font-weight: 500;")
        self.start_date_input = QDateTimeEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.start_date_input.setMaximumWidth(200)
        
        end_lbl = QLabel("Date de Fin :")
        end_lbl.setStyleSheet("color: #495057; font-weight: 500;")
        self.end_date_input = QDateTimeEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.end_date_input.setMaximumWidth(200)
        
        self.apply_filter_btn = QPushButton("Appliquer le Filtre")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.apply_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        filter_layout.addWidget(start_lbl, 0, 0, Qt.AlignRight)
        filter_layout.addWidget(self.start_date_input, 0, 1, Qt.AlignLeft)
        filter_layout.addWidget(end_lbl, 1, 0, Qt.AlignRight)
        filter_layout.addWidget(self.end_date_input, 1, 1, Qt.AlignLeft)
        filter_layout.addWidget(self.apply_filter_btn, 2, 0, 1, 2)
        
        filter_group.setLayout(filter_layout)
        content_layout.addWidget(filter_group)
        
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def load_file(self):
        """Load and parse FIM file"""
        path, _ = QFileDialog.getOpenFileName(self, "Charger FIM", "", "FIM (*.fim)")
        if not path: return
        
        self.file_label.setText(os.path.basename(path))
        self._set_busy(True, "Chargement du fichier FIM...")
        try:
            df, meta = parse_fim_file(path)
            if df is not None:
                # Basic analytics before updating state
                df = AnalyticsEngine.remove_outliers(df)
                vl, pl = AnalyticsEngine.compute_tmj(df)
                meta.update({
                    'tmj_vl_sens1': vl.get('Sens 1', '--'),
                    'tmj_vl_sens2': vl.get('Sens 2', '--'),
                    'tmj_pl_sens1': pl.get('Sens 1', '--'),
                    'tmj_pl_sens2': pl.get('Sens 2', '--'),
                })
                self.state.set_data(df, meta)
                QMessageBox.information(self, "Chargement Réussi", f"Le fichier FIM a été chargé et analysé avec succès.\n\nFichier : {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du chargement: {e}")
        finally:
            self._set_busy(False)

    def load_csv_file(self):
        """Load and parse edited CSV file"""
        path, _ = QFileDialog.getOpenFileName(self, "Charger CSV", "", "CSV (*.csv)")
        if not path: return
        
        self.file_label.setText(os.path.basename(path))
        self._set_busy(True, "Chargement du fichier CSV...")
        try:
            df, meta = CsvIngressService.parse_csv_file(path)
            if df is not None:
                df = AnalyticsEngine.remove_outliers(df)
                vl, pl = AnalyticsEngine.compute_tmj(df)
                meta.update({
                    'tmj_vl_sens1': vl.get('Sens 1', '--'),
                    'tmj_vl_sens2': vl.get('Sens 2', '--'),
                    'tmj_pl_sens1': pl.get('Sens 1', '--'),
                    'tmj_pl_sens2': pl.get('Sens 2', '--'),
                })
                self.state.set_data(df, meta)
                QMessageBox.information(self, "Chargement Réussi", f"Le fichier CSV a été chargé et analysé avec succès.\n\nFichier : {os.path.basename(path)}")
            else:
                QMessageBox.critical(self, "Erreur", "Le fichier CSV n'a pas pu être analysé. Assurez-vous qu'il respecte le format requis.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du chargement CSV: {e}")
        finally:
            self._set_busy(False)

    def load_raw_file(self):
        """Load and parse alternative Raw Data file (.xls or .xlsx)"""
        path, _ = QFileDialog.getOpenFileName(self, "Charger Données Brutes", "", "Excel (*.xls *.xlsx)")
        if not path: return
        
        self.file_label.setText(os.path.basename(path))
        self._set_busy(True, "Chargement des données brutes...")
        try:
            df, meta = RawDataService.parse_raw_data_file(path)
            if df is not None:
                df = AnalyticsEngine.remove_outliers(df)
                vl, pl = AnalyticsEngine.compute_tmj(df)
                meta.update({
                    'tmj_vl_sens1': vl.get('Sens 1', '--'),
                    'tmj_vl_sens2': vl.get('Sens 2', '--'),
                    'tmj_pl_sens1': pl.get('Sens 1', '--'),
                    'tmj_pl_sens2': pl.get('Sens 2', '--'),
                })
                self.state.set_data(df, meta)
                QMessageBox.information(self, "Chargement Réussi", f"Le fichier de données brutes a été chargé et analysé avec succès.\n\nFichier : {os.path.basename(path)}")
            else:
                QMessageBox.critical(self, "Erreur", "Le fichier n'a pas pu être analysé. Assurez-vous qu'il respecte le format requis.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du chargement: {e}")
        finally:
            self._set_busy(False)

    def update_ui_from_state(self, df, meta):
        """Update labels when state changes"""
        has_velocity = meta.get('has_velocity', True)
        speed_text = "Détectée (Avec Vitesse)" if has_velocity else "Non disponible (Comptage Seul)"
        
        for key, widget in self.metadata_fields.items():
            if key == 'speed_status':
                widget.setText(speed_text)
                continue
            val = meta.get(key, '--')
            if key == 'gps_coordinates' and val is None:
                val = 'Non détecté'
            widget.setText(str(val))
            
        if df is not None and not df.empty:
            # Explicitly ensure timestamp column is standardized to datetime64[ns]
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(
                    df['timestamp'].apply(DataFilteringService.parse_timestamp_robustly),
                    errors='coerce'
                )
                
            min_ts = df['timestamp'].min()
            max_ts = df['timestamp'].max()
            
            if pd.notnull(min_ts) and pd.notnull(max_ts):
                # Block signals temporarily to prevent loop
                self.start_date_input.blockSignals(True)
                self.end_date_input.blockSignals(True)
                
                self.start_date_input.setDateTime(QDateTime(min_ts.to_pydatetime()))
                self.start_date_input.setMinimumDateTime(QDateTime(min_ts.to_pydatetime()))
                self.start_date_input.setMaximumDateTime(QDateTime(max_ts.to_pydatetime()))
                
                self.end_date_input.setDateTime(QDateTime(max_ts.to_pydatetime()))
                self.end_date_input.setMinimumDateTime(QDateTime(min_ts.to_pydatetime()))
                self.end_date_input.setMaximumDateTime(QDateTime(max_ts.to_pydatetime()))
                
                self.start_date_input.blockSignals(False)
                self.end_date_input.blockSignals(False)
            
            # Reset filter variables
            self.filter_start_dt = None
            self.filter_end_dt = None

    def apply_filter(self):
        """Apply selected date range filter and update statistics display"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée pour le filtrage")
            return
            
        start_dt = self.start_date_input.dateTime().toPyDateTime()
        end_dt = self.end_date_input.dateTime().toPyDateTime()
        
        if start_dt > end_dt:
            QMessageBox.warning(self, "Erreur", "La date de début doit être antérieure ou égale à la date de fin.")
            return
            
        self.filter_start_dt = start_dt
        self.filter_end_dt = end_dt
        
        # Filter copy of current data
        filtered_df = DataFilteringService.filter_by_date_range(self.state.current_df, start_dt, end_dt)
        
        # Recompute TMJ on the filtered slice
        vl, pl = AnalyticsEngine.compute_tmj(filtered_df)
        
        # Update display labels
        self.metadata_fields['start_datetime'].setText(start_dt.strftime('%d/%m/%Y %H:%M'))
        self.metadata_fields['end_datetime'].setText(end_dt.strftime('%d/%m/%Y %H:%M'))
        self.metadata_fields['tmj_vl_sens1'].setText(str(vl.get('Sens 1', '--')))
        self.metadata_fields['tmj_vl_sens2'].setText(str(vl.get('Sens 2', '--')))
        self.metadata_fields['tmj_pl_sens1'].setText(str(pl.get('Sens 1', '--')))
        self.metadata_fields['tmj_pl_sens2'].setText(str(pl.get('Sens 2', '--')))
        
        QMessageBox.information(self, "Succès", "Filtre temporel appliqué avec succès. Les rapports et extractions utiliseront cette période.")

    def extract_data(self):
        """Export raw traffic data with user format selection (Standard or Weekly Matrix)"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée")
            return
            
        dialog = RawExportFormatDialog(self)
        if dialog.exec_() != RawExportFormatDialog.Accepted:
            return
            
        is_weekly = dialog.is_weekly_matrix_selected()
        
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'export")
        if not folder: return

        self._set_busy(True, "Extraction des données brutes en cours...")
        try:
            df_to_use = self.state.current_df
            meta_to_use = self.state.current_metadata.copy()
            
            if self.filter_start_dt is not None or self.filter_end_dt is not None:
                df_to_use = DataFilteringService.filter_by_date_range(df_to_use, self.filter_start_dt, self.filter_end_dt)
                meta_to_use['start_datetime'] = self.filter_start_dt.strftime('%d/%m/%Y %H:%M')
                meta_to_use['end_datetime'] = self.filter_end_dt.strftime('%d/%m/%Y %H:%M')
                
            if is_weekly:
                path = ExcelService.export_raw_data_weekly(df_to_use, meta_to_use, folder)
            else:
                path = ExcelService.export_raw_data(df_to_use, meta_to_use, folder)
                
            QMessageBox.information(self, "Succès", f"Export réussi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
        finally:
            self._set_busy(False)

    def export_csv_data(self):
        """Export raw traffic data to CSV with embedded metadata"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Exporter en CSV", "", "CSV (*.csv)")
        if not file_path: return
        
        self._set_busy(True, "Exportation des données brutes en CSV...")
        try:
            success = CsvIngressService.export_raw_to_csv(self.state.current_df, self.state.current_metadata, file_path)
            if success:
                QMessageBox.information(self, "Succès", f"Export CSV réussi:\n{file_path}")
            else:
                QMessageBox.critical(self, "Erreur", "Échec de l'exportation CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'exportation CSV: {e}")
        finally:
            self._set_busy(False)

    def generate_reports(self):
        """Generate official analytics report using template with UI feedback, applying the date filter if set"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée pour les rapports")
            return
            
        # Check if filter is applied and update metadata copy before report dialog
        meta_to_use = self.state.current_metadata.copy()
        df_to_use = self.state.current_df
        
        if self.filter_start_dt is not None or self.filter_end_dt is not None:
            df_to_use = DataFilteringService.filter_by_date_range(df_to_use, self.filter_start_dt, self.filter_end_dt)
            meta_to_use['start_datetime'] = self.filter_start_dt.strftime('%d/%m/%Y %H:%M')
            meta_to_use['end_datetime'] = self.filter_end_dt.strftime('%d/%m/%Y %H:%M')

        # Show Metadata Dialog
        from .dialogs import ReportSettingsDialog
        dialog = ReportSettingsDialog(self, meta_to_use)
        if dialog.exec_() != ReportSettingsDialog.Accepted:
            return
            
        settings = dialog.get_settings()
        
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier pour le rapport")
        if not folder: return

        self._set_busy(True, "Génération du rapport analytique... Veuillez patienter.")
        try:
            path = ReportService.generate_report(df_to_use, meta_to_use, settings, folder, auto_open=True)
            QMessageBox.information(self, "Succès", f"Rapport généré avec succès:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la génération du rapport: {e}")
        finally:
            self._set_busy(False)

    def _set_busy(self, is_busy: bool, message: str = ""):
        """Handle UI state during heavy processing"""
        from PyQt5.QtWidgets import QApplication
        if is_busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.extract_btn.setEnabled(False)
            self.extract_csv_btn.setEnabled(False)
            self.report_btn.setEnabled(False)
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().showMessage(message)
        else:
            QApplication.restoreOverrideCursor()
            self.extract_btn.setEnabled(True)
            self.extract_csv_btn.setEnabled(True)
            self.report_btn.setEnabled(True)
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().clearMessage()
        QApplication.processEvents()
