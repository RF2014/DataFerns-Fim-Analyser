"""
Refactored MetadataPanel for DataFerns Traffic Reporter
Follows Senior architecture and surgical refactoring rules (< 200 lines).
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from ..core.fim_parser import parse_fim_file
from ..core.analytics import AnalyticsEngine
from ..services.excel_service import ExcelService
from ..services.report_service import ReportService
from ..models.state import AppState
from ..utils.helpers import resource_path

class MetadataPanel(QWidget):
    """Refactored UI panel for traffic metadata and file operations"""
    
    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.metadata_fields = {}
        self.init_ui()
        self.state.subscribe(self.update_ui_from_state)

    def init_ui(self):
        """Initialize premium modern UI layout"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
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
                min-width: 150px;
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
        
        self.extract_btn = QPushButton("Extraire Données")
        self.extract_btn.clicked.connect(self.extract_data)
        
        self.report_btn = QPushButton("Générer Rapports")
        self.report_btn.setObjectName("report_btn")
        self.report_btn.clicked.connect(self.generate_reports)
        
        ctrl_layout.addWidget(load_btn)
        ctrl_layout.addWidget(self.extract_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.report_btn)
        ctrl_card.setLayout(ctrl_layout)
        main_layout.addWidget(ctrl_card)

        # 3. Content Area (Metadata)
        content_layout = QHBoxLayout()
        
        metadata_group = QGroupBox("Statistiques de Trafic")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.setHorizontalSpacing(30)
        
        field_names = [
            ('Période de début', 'start_datetime'),
            ('Période de fin', 'end_datetime'),
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
        
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def load_file(self):
        """Load and parse FIM file"""
        path, _ = QFileDialog.getOpenFileName(self, "Charger FIM", "", "FIM (*.fim)")
        if not path: return
        
        self.file_label.setText(os.path.basename(path))
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
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du chargement: {e}")

    def update_ui_from_state(self, df, meta):
        """Update labels when state changes"""
        for key, widget in self.metadata_fields.items():
            widget.setText(str(meta.get(key, '--')))

    def extract_data(self):
        """Delegate to ExcelService with UI feedback"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'export")
        if not folder: return

        self._set_busy(True, "Extraction des données brutes en cours...")
        try:
            path = ExcelService.export_raw_data(self.state.current_df, self.state.current_metadata, folder)
            QMessageBox.information(self, "Succès", f"Export réussi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
        finally:
            self._set_busy(False)

    def generate_reports(self):
        """Generate official analytics report using template with UI feedback"""
        if not self.state.has_data():
            QMessageBox.warning(self, "Attention", "Aucune donnée chargée pour les rapports")
            return
            
        # Show Metadata Dialog
        from .dialogs import ReportSettingsDialog
        dialog = ReportSettingsDialog(self, self.state.current_metadata)
        if dialog.exec_() != ReportSettingsDialog.Accepted:
            return
            
        settings = dialog.get_settings()
        
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier pour le rapport")
        if not folder: return

        self._set_busy(True, "Génération du rapport analytique... Veuillez patienter.")
        try:
            path = ReportService.generate_report(self.state.current_df, self.state.current_metadata, settings, folder)
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
            self.report_btn.setEnabled(False)
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().showMessage(message)
        else:
            QApplication.restoreOverrideCursor()
            self.extract_btn.setEnabled(True)
            self.report_btn.setEnabled(True)
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().clearMessage()
        QApplication.processEvents()
