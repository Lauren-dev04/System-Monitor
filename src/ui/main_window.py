# Import necessary PySide6 classes for building the UI
from PySide6.QtWidgets import QMainWindow, QWidget

class MainWindow(QMainWindow):
    """Main aplication window for the System Monitor."""

    def __init__(self):
        # Initialize the parent class (QMainWindow) to inherit its properties
        super().__init__()

        # Set window title and initial dimensions (width, height)
        self .setWindowTitle("System Monitor")
        self .resize(900, 600)

        #Create a central widget (mandatory in QMainWindow to hold future layouts/tabs)
        self .central_widget = QWidget()
        self .setCentralWidget(self.central_widget)

        # Call the method to apply the dark theme
        self .apply_dark_theme()


    def apply_dark_theme(self):
        """Apply a minimalist dark theme using Qt Style Sheets (QSS)."""

        # Define CSS-like styles for the window and widgets
        dark_theme_qss = """
            QMainWindow, QWidget {
                background-color: #1e1e1e; /* Dark gray backgruond */
                color: #e0e0e0             /* Light gray text */
                font-family: 'Ubuntu', 'Segoe UI', sans-serif;
            }
        """

        # Apply the stylesheet to the entrie window
        self .setStyleSheet(dark_theme_qss)

