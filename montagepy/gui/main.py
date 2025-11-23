import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from montagepy.gui.windows.main_window import MainWindow

def main():
    """GUI Application Entry Point."""
    app = QApplication(sys.argv)
    app.setApplicationName("MontagePy")
    app.setOrganizationName("MontagePy")
    
    # Apply qt-material theme
    try:
        from qt_material import apply_stylesheet
        # Using a light theme to match the previous design intent, or user can configure
        apply_stylesheet(app, theme='light_blue.xml')
    except ImportError:
        print("Warning: qt-material not installed. Install it with 'pip install qt-material'")
        # Fallback to custom style if needed, or just warn
        pass
            
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
