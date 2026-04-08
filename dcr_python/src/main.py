"""
DCR 2000 - Traffic Data Analysis Application
Main application entry point
"""

import sys
from PyQt5.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .utils.constants import APP_NAME, APP_VERSION


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
