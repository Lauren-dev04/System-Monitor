# Import necessary PySide6 classes for building the UI
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt, QTimer

# Import our custom UI components
from .sidebar import Sidebar
from .hardware_card import HardwareCard

# Import hardware monitoring functions (using absolute path from src)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.monitor import get_cpu_info, get_gpu_info, get_ram_info, get_disk_info


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

        # Create a timer to update hardware data every 1 second (1000 milliseconds)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_hardware_data)
        self.update_timer.start(1000)  # Update every 1 second

        # Do an initial update immediately
        self.update_hardware_data()

    def create_content_pages(self):
        """Create placeholder pages for each section."""
        # Dictionary to keep track of page indices
        self.page_indices = {}

        sections = ['main', 'cpu', 'gpu', 'disk']

        for index, section in enumerate(sections):
            if section == 'main':
                # Create a container widget for the main view cards
                main_container = QWidget()
                main_layout = QHBoxLayout(main_container)
                main_layout.setContentsMargins(30, 30, 30, 30)
                main_layout.setSpacing(20)

                # Create the hardware cards
                self.cpu_card = HardwareCard("CPU")
                self.gpu_card = HardwareCard("GPU")
                self.ram_card = HardwareCard("RAM")
                self.disk_card = HardwareCard("DISK")

                # Add cards to the layout (with stretch on both sides to center them)
                main_layout.addStretch() # Left spacer
                main_layout.addWidget(self.cpu_card)
                main_layout.addWidget(self.gpu_card)
                main_layout.addWidget(self.ram_card)
                main_layout.addWidget(self.disk_card)
                main_layout.addStretch() # Right spacer

                # Add the container to the stacked widget
                self.content_stack.addWidget(main_container)
            else:
                # Create a temporary label for other sections
                label = QLabel(f"{section.upper()} View - Coming Soon")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #888; font-size: 18px;")

                # Add the label to the stacked widget
                self.content_stack.addWidget(label)

            self.page_indices[section] = index

    def update_hardware_data(self):
        """Fetch hardware data and update the cards."""

        # Get CPU data and update the card
        cpu_data = get_cpu_info()
        self.cpu_card.update_data(cpu_data['usage'], cpu_data['temp'])

        # Get GPU data and update the card
        gpu_data = get_gpu_info()
        self.gpu_card.update_data(gpu_data['usage'], gpu_data['temp'])

        # Get RAM data and update the card
        ram_data = get_ram_info()
        self.ram_card.update_data(ram_data['percent'], None)  # RAM typically doesn't have temp

        # Get Disk data and update the card
        disk_data = get_disk_info()
        self.disk_card.update_data(disk_data['percent'], None)  # Disk typically doesn't have temp

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
