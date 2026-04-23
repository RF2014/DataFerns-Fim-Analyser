"""
FIM File Loader - Refactored Main Window
(Original 5,000-line monolith deconstructed)
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.ui.metadata_panel import MetadataPanel
from src.models.state import AppState

class FIMLoaderWindow(QMainWindow):
    """Main window for FIM File Loader (Modular Version)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataFerns FIM Analyser")
        self.setGeometry(100, 100, 1000, 600)
        
        # Set Window Icon
        from PyQt5.QtGui import QIcon
        from src.utils.helpers import resource_path
        icon_path = resource_path("ui", "logo.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        # Initialize Shared State
        self.state = AppState()
        
        # Central Metadata Panel
        self.metadata_panel = MetadataPanel(self.state)
        self.setCentralWidget(self.metadata_panel)

def main():
    """Standalone entry point for FIM Loader"""
    app = QApplication(sys.argv)
    window = FIMLoaderWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
