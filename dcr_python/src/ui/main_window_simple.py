"""
Main application window - simplified for FIM processing
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QPushButton, QLabel, QTableWidget, 
    QTableWidgetItem, QMessageBox, QFileDialog, QProgressBar,
    QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..core.file_manager import FileManager
from ..core.data_processor import DataProcessor
from ..models import TrafficMetadata
from ..utils.constants import (
    APP_NAME, APP_TITLE, DEFAULT_FIM_DIR, DEFAULT_IFX_DIR, DEFAULT_DBL_DIR
)


class MainWindow(QMainWindow):
    """Main application window - FIM processing focused"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, 900, 600)
        
        # Initialize components
        self.file_manager = FileManager(DEFAULT_FIM_DIR, DEFAULT_IFX_DIR, DEFAULT_DBL_DIR)
        self.data_processor = DataProcessor()
        
        # Current state
        self.current_file = None
        self.current_data = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("FIM File Processor")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("1. Import a FIM file  →  2. Process  →  3. Export as CSV")
        main_layout.addWidget(instructions)
        
        # Interval configuration
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Interval (minutes):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(5)
        self.interval_spinbox.setMaximum(1440)
        self.interval_spinbox.setValue(5)  # Default 5 minutes
        self.interval_spinbox.setSingleStep(5)  # Increment by 5
        self.interval_spinbox.setSuffix(" min")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        main_layout.addLayout(interval_layout)
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("1. Import FIM File")
        import_btn.setMinimumHeight(40)
        import_btn.clicked.connect(self.import_file)
        button_layout.addWidget(import_btn)
        
        process_btn = QPushButton("2. Process")
        process_btn.setMinimumHeight(40)
        process_btn.clicked.connect(self.process_data)
        button_layout.addWidget(process_btn)
        
        export_btn = QPushButton("3. Export as CSV")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Data preview table
        preview_label = QLabel("Data Preview (first 10 rows):")
        main_layout.addWidget(preview_label)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels([
            "Vehicle Count", "Flow (veh/h)", "Speed (km/h)", "Hour", "Minute", "Interval Time", "Period"
        ])
        self.data_table.setMaximumHeight(250)
        main_layout.addWidget(self.data_table)
        
        main_layout.addStretch()
        
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        
        import_action = file_menu.addAction("&Import FIM File")
        import_action.triggered.connect(self.import_file)
        
        export_action = file_menu.addAction("&Export as CSV")
        export_action.triggered.connect(self.export_csv)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about)
    
    def import_file(self):
        """Import FIM file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open FIM File",
            self.file_manager.fim_dir or "",
            "FIM Files (*.fim *.FIM);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.current_file = file_path
        data = self.file_manager.open_file(file_path, "FIM")
        
        if data is not None:
            self.current_data = data
            rows, cols = data.shape
            self.status_label.setText(f"Loaded: {file_path.split('/')[-1]} ({rows} rows)")
            self.update_preview()
        else:
            QMessageBox.warning(self, "Error", "Failed to load FIM file")
    
    def process_data(self):
        """Process the loaded data"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "No file loaded. Import a FIM file first.")
            return
        
        self.status_label.setText("Processing...")
        
        # Get interval value from spinbox
        interval = self.interval_spinbox.value()
        
        metadata = TrafficMetadata(
            filename=self.current_file or "data.fim",
            filepath=self.current_file or "",
            format="FIM",
            sequence=1440,
            mode="1 - TV Conf."
        )
        
        success, message = self.data_processor.process_raw_data(self.current_data, metadata, interval)
        
        if success:
            self.status_label.setText(f"Processing complete ({interval}-min intervals). Ready to export.")
            self.update_preview()
        else:
            QMessageBox.warning(self, "Error", f"Processing failed: {message}")
    
    def export_csv(self):
        """Export processed data as CSV"""
        if self.data_processor.processed_data is None:
            QMessageBox.warning(self, "Warning", "No processed data. Please process a file first.")
            return
        
        # File save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ensure .csv extension
        if not file_path.endswith(".csv"):
            file_path += ".csv"
        
        try:
            self.data_processor.processed_data.to_csv(file_path, index=False)
            self.status_label.setText(f"Exported: {file_path.split('/')[-1]}")
            QMessageBox.information(self, "Success", f"File saved:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
    
    def update_preview(self):
        """Update data preview table"""
        data = self.data_processor.processed_data if self.data_processor.processed_data is not None else self.current_data
        
        if data is None or data.empty:
            self.data_table.setRowCount(0)
            return
        
        # Show first 10 rows
        preview = data.head(10)
        self.data_table.setRowCount(len(preview))
        
        for row_idx, (_, row) in enumerate(preview.iterrows()):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value)[:15])  # Truncate long values
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.data_table.setItem(row_idx, col_idx, item)
        
        self.data_table.resizeColumnsToContents()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(
            self,
            "About DCR 2000",
            f"{APP_TITLE}\n\nSimplified FIM File Processor\nVersion 1.0.0"
        )
