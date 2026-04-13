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
        """Initialize layout and widgets"""
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # 1. File Selection Row
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Aucun fichier chargé")
        self.file_label.setStyleSheet("color: #0066cc;")
        self.file_label.setFont(QFont("Segoe UI", 11))
        
        load_btn = QPushButton("Charger fichier FIM")
        load_btn.clicked.connect(self.load_file)
        
        self.extract_btn = QPushButton("Extraire données")
        self.extract_btn.clicked.connect(self.extract_data)
        
        self.report_btn = QPushButton("Générer des rapports")
        self.report_btn.clicked.connect(self.generate_reports)
        
        file_layout.addWidget(QLabel("Fichier:"))
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(load_btn)
        file_layout.addWidget(self.extract_btn)
        file_layout.addWidget(self.report_btn)
        layout.addLayout(file_layout)

        # 2. Metadata Grid
        metadata_group = QGroupBox("Métadonnées")
        grid = QGridLayout()
        
        field_names = [
            ('Date/Heure de début', 'start_datetime'),
            ('Date/Heure de fin', 'end_datetime'),
            ('TMJ VL Sens 1', 'tmj_vl_sens1'),
            ('TMJ VL Sens 2', 'tmj_vl_sens2'),
            ('TMJ PL Sens 1', 'tmj_pl_sens1'),
            ('TMJ PL Sens 2', 'tmj_pl_sens2'),
        ]
        
        for i, (label_text, key) in enumerate(field_names):
            lbl = QLabel(label_text + ":")
            val_lbl = QLabel("--")
            val_lbl.setStyleSheet("color: #0066cc;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
            self.metadata_fields[key] = val_lbl

        # Logo
        logo_label = QLabel()
        pix = QPixmap(resource_path("logo.png"))
        if not pix.isNull():
            logo_label.setPixmap(pix.scaledToHeight(64, Qt.SmoothTransformation))
        grid.addWidget(logo_label, len(field_names), 1, alignment=Qt.AlignRight)

        metadata_group.setLayout(grid)
        layout.addWidget(metadata_group)
        self.setLayout(layout)

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
