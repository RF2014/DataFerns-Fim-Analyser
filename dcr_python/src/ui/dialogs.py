"""
Dialog windows for the application
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QMessageBox, QFormLayout, QGroupBox, QCheckBox
)
from PyQt5.QtCore import pyqtSignal, Qt

from ..utils.constants import (
    ROAD_TYPES, LANE_OPTIONS, DIRECTION_TYPES,
    MODE_TV_CONF, MODE_PL_CONF, MODE_TV_DISC
)


class TrafficInputDialog(QDialog):
    """Dialog for entering traffic analysis parameters"""
    
    data_submitted = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Traffic Data Input")
        self.setGeometry(100, 100, 500, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Road Information Group
        road_group = QGroupBox("Road Information")
        road_layout = QFormLayout()
        
        self.client_input = QLineEdit()
        self.service_input = QLineEdit()
        self.location_input = QLineEdit()
        
        road_layout.addRow("Client/Organization:", self.client_input)
        road_layout.addRow("Service:", self.service_input)
        road_layout.addRow("Location:", self.location_input)
        
        road_group.setLayout(road_layout)
        layout.addWidget(road_group)
        
        # Traffic Parameters Group
        param_group = QGroupBox("Traffic Parameters")
        param_layout = QFormLayout()
        
        self.road_type_combo = QComboBox()
        self.road_type_combo.addItems(ROAD_TYPES)
        
        self.lanes_combo = QComboBox()
        self.lanes_combo.addItems(LANE_OPTIONS)
        
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(DIRECTION_TYPES)
        
        self.speed_limit_spin = QDoubleSpinBox()
        self.speed_limit_spin.setMinimum(0)
        self.speed_limit_spin.setMaximum(200)
        self.speed_limit_spin.setValue(90)
        self.speed_limit_spin.setSuffix(" km/h")
        
        param_layout.addRow("Road Type:", self.road_type_combo)
        param_layout.addRow("Number of Lanes:", self.lanes_combo)
        param_layout.addRow("Direction:", self.direction_combo)
        param_layout.addRow("Speed Limit:", self.speed_limit_spin)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # Analysis Mode Group
        mode_group = QGroupBox("Analysis Mode")
        mode_layout = QFormLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            MODE_TV_CONF,
            MODE_PL_CONF,
            MODE_TV_DISC
        ])
        
        mode_layout.addRow("Mode:", self.mode_combo)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_data(self) -> dict:
        """Get entered data"""
        return {
            "client": self.client_input.text(),
            "service": self.service_input.text(),
            "location": self.location_input.text(),
            "road_type": self.road_type_combo.currentText(),
            "lanes": self.lanes_combo.currentText(),
            "direction": self.direction_combo.currentText(),
            "speed_limit": self.speed_limit_spin.value(),
            "mode": self.mode_combo.currentText()
        }


class FileImportDialog(QDialog):
    """Dialog for file import operations"""
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, file_type: str = "FIM"):
        super().__init__(parent)
        self.file_type = file_type
        self.setWindowTitle(f"Import {file_type} File")
        self.setGeometry(100, 100, 400, 200)
        self.selected_file = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_label = QLabel("Select file to import:")
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file browser"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_filter = f"{self.file_type} Files (*.{self.file_type})"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {self.file_type} File",
            "",
            file_filter
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_input.setText(file_path)
    
    def get_selected_file(self) -> str:
        """Get selected file path"""
        return self.selected_file or ""


class ExportDialog(QDialog):
    """Dialog for file export operations"""
    
    export_ready = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Results")
        self.setGeometry(100, 100, 400, 250)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Export directory
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Export Directory:")
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(True)
        # Default to Desktop or user home
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.export_dir = desktop if os.path.isdir(desktop) else os.path.expanduser("~")
        self.dir_input.setText(self.export_dir)
        browse_dir_btn = QPushButton("Browse...")
        browse_dir_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_dir_btn)
        layout.addLayout(dir_layout)
        
        # Filename and format
        form_layout = QFormLayout()
        
        self.filename_input = QLineEdit()
        self.filename_input.setText("traffic_report")
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "XLSX", "IFX"])  # CSV first as default
        
        self.include_charts = QCheckBox("Include Charts")
        self.include_charts.setChecked(False)  # Disabled for now
        self.include_charts.setEnabled(False)
        
        form_layout.addRow("Filename:", self.filename_input)
        form_layout.addRow("Format:", self.format_combo)
        form_layout.addRow(self.include_charts)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_directory(self):
        """Open directory browser"""
        from PyQt5.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dir_path:
            self.export_dir = dir_path
            self.dir_input.setText(dir_path)
    
    def get_export_options(self) -> dict:
        """Get export options"""
        return {
            "filename": self.filename_input.text(),
            "format": self.format_combo.currentText(),
            "include_charts": self.include_charts.isChecked(),
            "export_dir": self.export_dir
        }


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_settings: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 500, 400)
        self.current_settings = current_settings or {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Directories
        dir_group = QGroupBox("Directory Settings")
        dir_layout = QFormLayout()
        
        self.fim_dir_input = QLineEdit()
        self.fim_dir_input.setText(self.current_settings.get("fim_dir", ""))
        
        self.ifx_dir_input = QLineEdit()
        self.ifx_dir_input.setText(self.current_settings.get("ifx_dir", ""))
        
        self.dbl_dir_input = QLineEdit()
        self.dbl_dir_input.setText(self.current_settings.get("dbl_dir", ""))
        
        dir_layout.addRow("FIM Directory:", self.fim_dir_input)
        dir_layout.addRow("IFX Directory:", self.ifx_dir_input)
        dir_layout.addRow("DBL Directory:", self.dbl_dir_input)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_settings(self) -> dict:
        """Get updated settings"""
        return {
            "fim_dir": self.fim_dir_input.text(),
            "ifx_dir": self.ifx_dir_input.text(),
            "dbl_dir": self.dbl_dir_input.text()
        }
class ReportSettingsDialog(QDialog):
    """Dialog for entering metadata for the official report"""
    
    def __init__(self, parent=None, metadata: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres du Rapport")
        self.setGeometry(100, 100, 450, 450)
        self.metadata = metadata or {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # General Info
        self.site_name = QLineEdit(self.metadata.get('description', ''))
        self.vmax = QSpinBox()
        self.vmax.setRange(10, 130)
        self.vmax.setValue(50)
        
        form.addRow("Localisation / Rue:", self.site_name)
        form.addRow("Vitesse Max (km/h):", self.vmax)
        
        # Sect / Ind / Count
        # Try to guess from metadata or filename if possible, else defaults
        self.sect = QLineEdit("0170")
        self.ind = QLineEdit("11")
        self.count = QLineEdit("0000")
        
        sect_layout = QHBoxLayout()
        sect_layout.addWidget(QLabel("Sect:"))
        sect_layout.addWidget(self.sect)
        sect_layout.addWidget(QLabel("Ind:"))
        sect_layout.addWidget(self.ind)
        sect_layout.addWidget(QLabel("Count:"))
        sect_layout.addWidget(self.count)
        
        form.addRow("Référence Section:", sect_layout)
        
        # GPS and Sens
        gps_val = self.metadata.get('gps_coordinates', '')
        if gps_val is None:
            gps_val = ''
        self.gps_input = QLineEdit(gps_val)
        
        # Sens (Direction) must always start empty for manual entry
        self.sens_input = QLineEdit('')
        
        form.addRow("Cordonnées GPS:", self.gps_input)
        form.addRow("Sens:", self.sens_input)
        
        # Periods
        self.period1 = QLineEdit("07:00-09:00")
        self.period2 = QLineEdit("12:00-14:00")
        self.period3 = QLineEdit("17:00-19:00")
        
        form.addRow("Période 1 (HH:MM-HH:MM):", self.period1)
        form.addRow("Période 2 (HH:MM-HH:MM):", self.period2)
        form.addRow("Période 3 (HH:MM-HH:MM):", self.period3)
        
        layout.addLayout(form)
        
        # Help text
        help_lbl = QLabel("Note: La période d'enquête est calculée automatiquement à partir des dates du fichier.")
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(help_lbl)
        
        # Buttons
        btns = QHBoxLayout()
        ok_btn = QPushButton("Générer")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        
        self.setLayout(layout)
        
    def get_settings(self) -> dict:
        return {
            "site_name": self.site_name.text(),
            "vmax": self.vmax.value(),
            "sect_info": f"Sect: {self.sect.text()} / Ind: {self.ind.text()} / Count: {self.count.text()}",
            "periods": [self.period1.text(), self.period2.text(), self.period3.text()],
            "gps_coordinates": self.gps_input.text(),
            "sens": self.sens_input.text()
        }


class RawExportFormatDialog(QDialog):
    """Dialog for choosing raw data export format"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Format d'Export des Données Brutes")
        self.setMinimumWidth(450)
        self.init_ui()
        
    def init_ui(self):
        from PyQt5.QtWidgets import QRadioButton
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        lbl = QLabel("Sélectionnez le format d'exportation pour les données brutes :")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529;")
        layout.addWidget(lbl)
        
        self.standard_radio = QRadioButton("Format Standard Excel (Multi-feuilles : Métadonnées, Comptages, Vitesse)")
        self.standard_radio.setChecked(True)
        
        self.weekly_radio = QRadioButton("Format Matrice Hebdomadaire (Données Brutes V3 : Semaine / 24h)")
        
        layout.addWidget(self.standard_radio)
        layout.addWidget(self.weekly_radio)
        
        btns = QHBoxLayout()
        ok_btn = QPushButton("Exporter")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        
        self.setLayout(layout)
        
    def is_weekly_matrix_selected(self) -> bool:
        return self.weekly_radio.isChecked()

