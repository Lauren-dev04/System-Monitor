# Import necessary PySide6 classes for building the UI
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt

# Import our custom UI components
from .sidebar import Sidebar


class MainWindow(QMainWindow):
    """Main application window for the System Monitor."""

    def __init__(self):
        # Initialize the parent class (QMainWindow) to inherit its properties
        super().__init__()

        # Set window title and initial dimensions (width, height)
        self.setWindowTitle("System Monitor")
        self.resize(900, 600)

        # Create a central widget to hold the main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a horizontal layout to place sidebar and content side by side
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins
        self.main_layout.setSpacing(0) # Remove spacing between widgets

        # Create and add the Sidebar to the left
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)

        # Create a QStackedWidget to hold the different content pages
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # Connect the sidebar signal to the page switching method
        self.sidebar.button_clicked.connect(self.switch_page)

        # Create the content pages and show the default one
        self.create_content_pages()
        self.switch_page('main')

        # Call the method to apply the dark theme
        self.apply_dark_theme()

    def create_content_pages(self):
        """Create placeholder pages for each section."""
        # Dictionary to keep track of page indices
        self.page_indices = {}

        sections = ['main', 'cpu', 'gpu', 'disk']

        for index, section in enumerate(sections):
            # Create a temporary label for each section
            label = QLabel(f"Vista de {section.upper()} (Próximamente)")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 18px;")

            # Add the label to the stacked widget
            self.content_stack.addWidget(label)
            self.page_indices[section] = index

    def switch_page(self, page_name):
        """Switch the visible page in the stacked widget."""
        if page_name in self.page_indices:
            # Change the current index of the stacked widget
            self.content_stack.setCurrentIndex(self.page_indices[page_name])

    def apply_dark_theme(self):
        """Apply a minimalist dark theme using Qt Style Sheets (QSS)."""

        # Define CSS-like styles for the window and widgets
        dark_theme_qss = """
            QMainWindow, QWidget {
                background-color: #1e1e1e;  /* Dark gray background */
                color: #e0e0e0;             /* Light gray text */
                font-family: 'Ubuntu', 'Segoe UI', sans-serif;
            }
        """

        # Apply the stylesheet to the entire window
        self.setStyleSheet(dark_theme_qss)
