"""
Main application window
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QPushButton, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QStatusBar, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from .dialogs import (
    TrafficInputDialog, FileImportDialog, ExportDialog, SettingsDialog
)
from .widgets import TrafficDataTable, StatusPanel
from ..core.file_manager import FileManager
from ..core.data_processor import DataProcessor
from ..core.reports import ReportGenerator
from ..models import TrafficMetadata, RoadInformation
from ..utils.constants import (
    APP_NAME, APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    DEFAULT_FIM_DIR, DEFAULT_IFX_DIR, DEFAULT_DBL_DIR
)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Initialize components
        self.file_manager = FileManager(DEFAULT_FIM_DIR, DEFAULT_IFX_DIR, DEFAULT_DBL_DIR)
        self.data_processor = DataProcessor()
        self.report_generator = ReportGenerator()
        
        # Current data
        self.current_file = None
        self.current_data = None
        self.road_info = RoadInformation()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # File tab
        self.file_tab = self.create_file_tab()
        self.tabs.addTab(self.file_tab, "Files")
        
        # Data tab
        self.data_tab = self.create_data_tab()
        self.tabs.addTab(self.data_tab, "Data")
        
        # Analysis tab
        self.analysis_tab = self.create_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "Analysis")
        
        # Reports tab
        self.reports_tab = self.create_reports_tab()
        self.tabs.addTab(self.reports_tab, "Reports")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_panel = StatusPanel()
        main_layout.addWidget(self.status_panel.status_label)
        
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        import_action = file_menu.addAction("&Import File")
        import_action.triggered.connect(self.import_file)
        
        open_action = file_menu.addAction("&Open File")
        open_action.triggered.connect(self.open_file)
        
        export_action = file_menu.addAction("&Export Results")
        export_action.triggered.connect(self.export_results)
        
        file_menu.addSeparator()
        
        settings_action = file_menu.addAction("&Settings")
        settings_action.triggered.connect(self.open_settings)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        
        process_action = analysis_menu.addAction("&Process Data")
        process_action.triggered.connect(self.process_data)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_file)
        toolbar.addWidget(import_btn)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        process_btn = QPushButton("Process")
        process_btn.clicked.connect(self.process_data)
        toolbar.addWidget(process_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_results)
        toolbar.addWidget(export_btn)
    
    def create_file_tab(self) -> QWidget:
        """Create file management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # File list
        layout.addWidget(QLabel("Available Files:"))
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Size", "Modified"])
        self.file_table.itemDoubleClicked.connect(self.on_file_double_clicked)
        
        layout.addWidget(self.file_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_file_list)
        btn_layout.addWidget(refresh_btn)
        
        import_btn = QPushButton("Import New File")
        import_btn.clicked.connect(self.import_file)
        btn_layout.addWidget(import_btn)
        
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_data_tab(self) -> QWidget:
        """Create data tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Traffic Data:"))
        
        self.data_table = TrafficDataTable()
        layout.addWidget(self.data_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_analysis_tab(self) -> QWidget:
        """Create analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Analysis Results:"))
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(2)
        self.analysis_table.setHorizontalHeaderLabels(["Metric", "Value"])
        
        layout.addWidget(self.analysis_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_reports_tab(self) -> QWidget:
        """Create reports tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Reports:"))
        
        # Report options
        options_layout = QHBoxLayout()
        
        summary_btn = QPushButton("Generate Summary")
        summary_btn.clicked.connect(self.generate_summary_report)
        options_layout.addWidget(summary_btn)
        
        hourly_btn = QPushButton("Hourly Analysis")
        hourly_btn.clicked.connect(self.generate_hourly_report)
        options_layout.addWidget(hourly_btn)
        
        layout.addLayout(options_layout)
        
        # Reports display
        self.reports_table = QTableWidget()
        layout.addWidget(self.reports_table)
        
        widget.setLayout(layout)
        return widget
    
    def import_file(self):
        """Handle file import"""
        dialog = FileImportDialog(self, "FIM")
        if dialog.exec_():
            file_path = dialog.get_selected_file()
            if file_path:
                success, dest_path = self.file_manager.import_file(
                    file_path,
                    self.file_manager.fim_dir
                )
                
                if success:
                    self.status_panel.set_status(f"File imported: {dest_path}")
                    self.refresh_file_list()
                else:
                    QMessageBox.warning(self, "Error", "Failed to import file")
    
    def open_file(self):
        """Handle file open"""
        # Show traffic input dialog first
        input_dialog = TrafficInputDialog(self)
        if input_dialog.exec_():
            self.road_info = RoadInformation(**input_dialog.get_data())
            
            # Then show file selection
            file_dialog = QFileDialog(self)
            file_path, _ = file_dialog.getOpenFileName(
                self,
                "Open Traffic File",
                self.file_manager.ifx_dir,
                "IFX Files (*.IFX);;Excel Files (*.xlsx)"
            )
            
            if file_path:
                self.current_file = file_path
                data = self.file_manager.open_file(file_path, "IFX")
                
                if data is not None:
                    self.current_data = data
                    # Report basic diagnostics about the loaded DataFrame
                    try:
                        rows, cols = self.current_data.shape
                        cols_list = ', '.join(list(self.current_data.columns))
                        self.status_panel.set_status(f"File loaded: {file_path} ({rows} rows x {cols} cols)")
                        print(f"[DEBUG] Loaded file '{file_path}' with shape {rows}x{cols}. Columns: {cols_list}")
                    except Exception:
                        self.status_panel.set_status(f"File loaded: {file_path}")
                    self.update_data_tab()
                else:
                    QMessageBox.warning(self, "Error", "Failed to open file")
    
    def process_data(self):
        """Process current data"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "No data loaded")
            return

        # Validate that expected columns exist (helpful diagnostics)
        expected_cols = ["vehicle_count", "speed", "hour"]
        present = [c for c in expected_cols if c in self.current_data.columns]
        missing = [c for c in expected_cols if c not in self.current_data.columns]
        if len(present) == 0:
            QMessageBox.warning(self, "Warning", f"No usable data columns found. Expected columns: {expected_cols}. Found: {list(self.current_data.columns)}")
            return
        if missing:
            # Warn but allow processing if some metrics can be computed
            self.status_panel.set_status(f"Warning: missing columns {missing}. Processing will proceed where possible.")
        
        # Create metadata
        metadata = TrafficMetadata(
            filename=self.current_file or "data",
            filepath=self.current_file or "",
            format="IFX",
            sequence=1440,
            mode="1 - TV Conf."
        )
        
        # Process data
        success, message = self.data_processor.process_raw_data(
            self.current_data,
            metadata
        )
        
        if success:
            self.status_panel.set_status(message)
            print(f"[DEBUG] Processing successful. Processed data shape: {self.data_processor.processed_data.shape}")
            print(f"[DEBUG] Processed data columns: {list(self.data_processor.processed_data.columns)}")
            self.update_analysis_tab()
        else:
            print(f"[DEBUG] Processing failed: {message}")
            QMessageBox.warning(self, "Error", message)
    
    def export_results(self):
        """Export results"""
        # If no processed data, try processing the current data first
        if self.data_processor.processed_data is None:
            if self.current_data is None:
                QMessageBox.warning(self, "Warning", "No data loaded. Please open a file first.")
                return
            
            # Auto-process if user hasn't explicitly clicked Process Data
            success, message = self.data_processor.process_raw_data(
                self.current_data,
                TrafficMetadata(
                    filename=self.current_file or "data",
                    filepath=self.current_file or "",
                    format="IFX",
                    sequence=1440,
                    mode="1 - TV Conf."
                )
            )
            
            if not success:
                QMessageBox.warning(self, "Error", f"Failed to process data: {message}")
                return
        
        dialog = ExportDialog(self)
        if dialog.exec_():
            options = dialog.get_export_options()
            
            # Use custom export function to handle custom export directory
            success, filepath = self._export_to_path(
                self.data_processor.processed_data,
                options["filename"],
                options["format"],
                options["export_dir"]
            )
            
            if success:
                self.status_panel.set_status(f"Results exported: {filepath}")
                QMessageBox.information(self, "Success", f"Results exported successfully to:\n{filepath}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export results")
    
    def open_settings(self):
        """Open settings dialog"""
        current = {
            "fim_dir": self.file_manager.fim_dir,
            "ifx_dir": self.file_manager.ifx_dir,
            "dbl_dir": self.file_manager.dbl_dir
        }
        
        dialog = SettingsDialog(self, current)
        if dialog.exec_():
            settings = dialog.get_settings()
            
            self.file_manager.fim_dir = settings["fim_dir"]
            self.file_manager.ifx_dir = settings["ifx_dir"]
            self.file_manager.dbl_dir = settings["dbl_dir"]
            
            self.status_panel.set_status("Settings updated")
    
    def refresh_file_list(self):
        """Refresh file list display"""
        fim_files = self.file_manager.list_fim_files()
        
        self.file_table.setRowCount(len(fim_files))
        
        for row, filename in enumerate(fim_files):
            info = self.file_manager.get_file_info(filename, "FIM")
            
            self.file_table.setItem(row, 0, QTableWidgetItem(filename))
            self.file_table.setItem(row, 1, QTableWidgetItem(str(info.get("size", 0))))
            self.file_table.setItem(row, 2, QTableWidgetItem(str(info.get("modified", ""))))
    
    def update_data_tab(self):
        """Update data tab display"""
        if self.current_data is None:
            return
        
        # Convert DataFrame to list of lists
        data_list = []
        for _, row in self.current_data.iterrows():
            data_list.append(list(row))
        
        self.data_table.load_data(data_list)
    
    def update_analysis_tab(self):
        """Update analysis tab"""
        stats = self.data_processor.get_statistical_summary()
        
        self.analysis_table.setRowCount(len(stats))
        
        row = 0
        for metric, values in stats.items():
            self.analysis_table.setItem(row, 0, QTableWidgetItem(metric))
            self.analysis_table.setItem(row, 1, QTableWidgetItem(str(values.get("mean", 0))))
            row += 1
    
    def generate_summary_report(self):
        """Generate summary report"""
        if self.data_processor.processed_data is None:
            QMessageBox.warning(self, "Warning", "No processed data available")
            return
        
        report = self.report_generator.generate_summary_report(
            self.data_processor.processed_data,
            self.road_info
        )
        
        self.display_report(report)
    
    def generate_hourly_report(self):
        """Generate hourly report"""
        if self.data_processor.processed_data is None:
            QMessageBox.warning(self, "Warning", "No processed data available")
            return
        
        report_data = self.report_generator.generate_hourly_report(
            self.data_processor.processed_data
        )
        
        # Display in table
        if not report_data.empty:
            self.reports_table.setColumnCount(len(report_data.columns))
            self.reports_table.setHorizontalHeaderLabels(report_data.columns.tolist())
            self.reports_table.setRowCount(len(report_data))
            
            for row, (_, record) in enumerate(report_data.iterrows()):
                for col, value in enumerate(record):
                    self.reports_table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def display_report(self, report: dict):
        """Display report data"""
        self.reports_table.setRowCount(len(report))
        self.reports_table.setColumnCount(2)
        self.reports_table.setHorizontalHeaderLabels(["Metric", "Value"])
        
        row = 0
        for key, value in report.items():
            self.reports_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.reports_table.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1
    
    def _export_to_path(self, data, filename: str, export_format: str, export_dir: str):
        """Export data to a custom directory path.
        
        Args:
            data: DataFrame to export
            filename: Output filename (without extension)
            export_format: Format (CSV, XLSX, IFX)
            export_dir: Directory to export to
        
        Returns:
            Tuple of (success: bool, filepath: Optional[str])
        """
        import os
        try:
            # Ensure directory exists
            from ..utils.helpers import ensure_directory_exists
            ensure_directory_exists(export_dir)
            
            # Build full path with extension
            if export_format.upper() == "CSV":
                ext = ".csv"
            elif export_format.upper() == "XLSX":
                ext = ".xlsx"
            elif export_format.upper() == "IFX":
                ext = ".IFX"
            else:
                ext = ""
            
            # Add extension if not already present
            if not filename.endswith(ext):
                filepath = os.path.join(export_dir, f"{filename}{ext}")
            else:
                filepath = os.path.join(export_dir, filename)
            
            # Export based on format
            if export_format.upper() == "CSV":
                data.to_csv(filepath, index=False)
            elif export_format.upper() in ["XLSX", "IFX"]:
                data.to_excel(filepath, index=False)
            
            return True, filepath
        
        except Exception as e:
            print(f"Error exporting file: {str(e)}")
            return False, None

    def on_file_double_clicked(self, item):
        """Handle file double-click"""
        # Open the file
        self.open_file()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(
            self,
            "About DCR 2000",
            f"{APP_TITLE}\n\nVersion 1.0.0\n\nTraffic Data Analysis Application\n\nPython Port of VBA Application"
        )
