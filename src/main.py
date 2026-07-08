# Main entry point for System Monitor
import sys
import os

# Fix paths for PyInstaller bundled app
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = sys._MEIPASS
else:
    # Running as script
    base_path = os.path.dirname(os.path.abspath(__file__))

# Add src to path so imports work
if base_path not in sys.path:
    sys.path.insert(0, base_path)

# Import and run the application
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Launch the System Monitor application."""
    app = QApplication(sys.argv)
    app.setApplicationName("System Monitor")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
