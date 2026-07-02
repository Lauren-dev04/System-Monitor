# Import Qt widgets and styles for building the sidebar
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QStyle
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon


class Sidebar(QWidget):
    """Sidebar navigation component with icon buttons."""

    # Signal emitted when a button is clicked (sends the button name)
    button_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        # Set fixed width for the sidebar
        self.setFixedWidth(80)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Create vertical layout to stack buttons
        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setAlignment(Qt.AlignTop)

        # Apply the layout to the widget
        self.setLayout(self.layout)

        # Create the navigation buttons
        self.create_buttons()

        # Apply custom styles
        self.apply_styles()

    def create_buttons(self):
        """Create navigation buttons with Qt standard icons."""

        # Define buttons: (name, icon_type, tooltip)
        self.buttons_config = [
            ("main", QStyle.SP_ComputerIcon, "Main Overview"),
            ("cpu", QStyle.SP_BrowserReload, "CPU Details"),
            ("gpu", QStyle.SP_DesktopIcon, "GPU Details"),
            ("disk", QStyle.SP_DriveHDIcon, "Disk Usage"),
        ]

        # Create a button for each configuration
        self.buttons = {}
        for name, icon_type, tooltip in self.buttons_config:
            button = QPushButton()
            button.setFixedSize(60, 60)
            button.setToolTip(tooltip)
            button.setProperty("name", name)
            button.setCheckable(True)
            button.setText("")  # No text, icon only

            # Get the standard icon from the system style
            style = self.style()
            standard_icon = style.standardIcon(icon_type)
            button.setIcon(standard_icon)
            button.setIconSize(QSize(32, 32))

            # Connect button click to signal
            button.clicked.connect(lambda checked, n=name: self.on_button_clicked(n))

            # Store button reference
            self.buttons[name] = button

            # Add to layout
            self.layout.addWidget(button)
            self.layout.addSpacing(5)

    def on_button_clicked(self, button_name):
        """Handle button click and emit signal."""

        # Uncheck all other buttons
        for name, btn in self.buttons.items():
            if name != button_name:
                btn.setChecked(False)

        # Emit signal with the clicked button name
        self.button_clicked.emit(button_name)

    def apply_styles(self):
        """Apply minimalist dark theme styles to sidebar buttons."""

        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
            QPushButton:checked {
                background-color: #3a3a3a;
                border-left: 3px solid #4a9eff;
            }
        """

        # Apply style to all buttons
        for button in self.buttons.values():
            button.setStyleSheet(button_style)
