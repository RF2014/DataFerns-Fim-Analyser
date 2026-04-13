"""
FIM File Loader - Refactored Main Window
(Original 5,000-line monolith deconstructed)
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from dcr_python.src.ui.metadata_panel import MetadataPanel
from dcr_python.src.models.state import AppState

class FIMLoaderWindow(QMainWindow):
    """Main window for FIM File Loader (Modular Version)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FIM File Loader - Analysis Tool")
        self.setGeometry(100, 100, 1000, 600)
        
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
