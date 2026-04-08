"""
Custom widgets for the application
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QStatusBar, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class FileSelector(QWidget):
    """Custom file selector widget"""
    
    def __init__(self, label_text: str = "Select File:", parent=None):
        super().__init__(parent)
        self.label = QLabel(label_text)
        self.input_field = QLineEdit()
        self.input_field.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.select_file)
        
        self.selected_file = None
    
    def select_file(self):
        """Open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;Excel Files (*.xlsx *.xls);;FIM Files (*.FIM);;DBL Files (*.DBL);;IFX Files (*.IFX)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.input_field.setText(file_path)


class DataComboBox(QComboBox):
    """Enhanced combo box with data storage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_map = {}
    
    def add_item_with_data(self, text: str, data):
        """Add item with associated data"""
        self.addItem(text)
        self.data_map[text] = data
    
    def get_current_data(self):
        """Get data associated with current selection"""
        return self.data_map.get(self.currentText(), None)


class TrafficDataTable(QTableWidget):
    """Custom table widget for traffic data display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Hour", "Vehicle Count", "Flow (veh/h)", "Speed (km/h)", "Classification", "Status"
        ])
    
    def load_data(self, data_list: list):
        """Load data into table"""
        self.setRowCount(len(data_list))
        
        for row, item in enumerate(data_list):
            for col, value in enumerate(item):
                table_item = QTableWidgetItem(str(value))
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, col, table_item)
        
        self.resizeColumnsToContents()


class StatusPanel(QWidget):
    """Status and progress panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
    
    def set_status(self, message: str):
        """Update status message"""
        self.status_label.setText(message)
    
    def show_progress(self):
        """Show progress bar"""
        self.progress_bar.setVisible(True)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
    
    def set_progress(self, value: int):
        """Set progress bar value"""
        self.progress_bar.setValue(value)


class DirectorySelector(QWidget):
    """Custom directory selector widget"""
    
    def __init__(self, label_text: str = "Select Directory:", parent=None):
        super().__init__(parent)
        self.label = QLabel(label_text)
        self.input_field = QLineEdit()
        self.input_field.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.select_directory)
        
        self.selected_directory = None
    
    def select_directory(self):
        """Open directory dialog"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if dir_path:
            self.selected_directory = dir_path
            self.input_field.setText(dir_path)
