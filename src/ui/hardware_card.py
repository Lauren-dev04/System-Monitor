# Import Qt widgets for building the hardware card
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class HardwareCard(QWidget):
    """Reusable card widget to display hardware usage and temperature."""

    def __init__(self, title):
        super().__init__()

        # Set a minimum width so the cards look wider
        self.setMinimumWidth(200)

        # Create a vertical layout for the card
        self.layout = QVBoxLayout()
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.layout)

        # 1. Title Label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a9eff;")

        # 2. Progress Bar (Usage %)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True) # Show percentage inside the bar
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # 3. Temperature Label
        self.temp_label = QLabel("Temp: --°C")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setStyleSheet("font-size: 14px; color: #e0e0e0;")

        # Add widgets to the layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.temp_label)

        # Apply styles
        self.apply_styles()

    def update_data(self, usage, temp):
        """Update the progress bar and temperature label with new data."""

        # Update progress bar value (ensure it's an integer)
        self.progress_bar.setValue(int(usage))

        # Update temperature text
        if temp is not None:
            self.temp_label.setText(f"Temp: {temp:.1f}°C")
        else:
            self.temp_label.setText("Temp: N/A")

    def apply_styles(self):
        """Apply dark theme styles to the card and progress bar."""

        # Style for the card container
        self.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 1px solid #3a3a3a;
            }
        """)

        # Style for the progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e1e1e;
                border: none;
                border-radius: 5px;
                text-align: center;
                color: #e0e0e0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 5px;
            }
        """)
