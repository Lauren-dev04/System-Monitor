# Import Qt widgets for building the hardware card
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QProgressBar, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from .fan_widget import FanWidget
from .neon_icon import NeonIconWidget


class HardwareCard(QWidget):
    """Reusable card widget to display hardware usage and temperature."""

    def __init__(self, title, model="", mode="standard", icon_type=None):
        super().__init__()

        self.mode = mode
        self.current_bg_color = "#2a2a2a"

        # Set fixed size for all cards (same dimensions)
        self.setFixedSize(250, 345)

        # Create main layout for this widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Create a QFrame as the card container (this will have the background)
        self.card_frame = QFrame()
        self.card_frame.setObjectName("card_frame")
        self.card_frame.setStyleSheet("""
            #card_frame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 1px solid #3a3a3a;
            }
        """)

        # Create layout inside the frame
        self.card_layout = QVBoxLayout()
        self.card_layout.setSpacing(6)
        self.card_layout.setContentsMargins(10, 10, 10, 10)
        self.card_frame.setLayout(self.card_layout)

        # Add frame to main layout
        main_layout.addWidget(self.card_frame)

        # Title/Model Label
        self.title_label = QLabel(model if model else title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(50)

        if mode == "temp_only":
            self.title_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #888;")
        else:
            self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #4a9eff;")

        self.card_layout.addWidget(self.title_label)

        # Create all widgets first (before adding to layout)

        # Progress Bar (standard and usage_only modes)
        if mode in ["standard", "usage_only"]:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setAlignment(Qt.AlignCenter)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #1e1e1e;
                    border: none;
                    border-radius: 5px;
                    text-align: center;
                    color: #e0e0e0;
                    height: 16px;
                }
                QProgressBar::chunk {
                    background-color: #4a9eff;
                    border-radius: 5px;
                }
            """)
        else:
            self.progress_bar = None

        # Neon icon for main display
        if icon_type and mode != "processes":
            self.neon_icon = NeonIconWidget(icon_type)
        else:
            self.neon_icon = None

        # Second icon for temp_only mode (fire/drop based on temperature)
        if mode == "temp_only":
            self.bottom_temp_icon = NeonIconWidget("drop", color="#4a9eff")
        else:
            self.bottom_temp_icon = None

        # Temperature Label
        if mode in ["standard", "temp_only"]:
            self.temp_label = QLabel("--°C")
            self.temp_label.setAlignment(Qt.AlignCenter)
            self.temp_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #e0e0e0;")
        else:
            self.temp_label = None

        # RPM Label (for temp_only mode)
        if mode == "temp_only":
            self.rpm_label = QLabel("0 RPM")
            self.rpm_label.setAlignment(Qt.AlignCenter)
            self.rpm_label.setStyleSheet("font-size: 14px; color: #e0e0e0;")
        else:
            self.rpm_label = None

        # Process List (processes mode only)
        if mode == "processes":
            self.process_list = QListWidget()
            self.process_list.setStyleSheet("""
                QListWidget {
                    background-color: transparent;
                    border: none;
                    color: #e0e0e0;
                    font-size: 13px;
                }
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid #3a3a3a;
                }
                QListWidget::item:last-child {
                    border-bottom: none;
                }
            """)
        else:
            self.process_list = None

        # Now add widgets to layout in correct order

        if mode == "temp_only":
            # Layout: Title -> Space -> Fan Icon -> RPM -> Temp -> Bottom Icon -> Stretch
            self.card_layout.addSpacing(2.5)
            self.card_layout.addWidget(self.neon_icon, alignment=Qt.AlignCenter)
            self.card_layout.addSpacing(20)
            self.card_layout.addWidget(self.rpm_label)
            self.card_layout.addWidget(self.temp_label)
            self.card_layout.addSpacing(2.5)
            self.card_layout.addWidget(self.bottom_temp_icon, alignment=Qt.AlignCenter)
            self.card_layout.addSpacing(10)
        elif mode in ["standard", "usage_only"]:
            # Layout: Title -> Stretch -> Icon -> Stretch -> Usage -> Bar
            if self.neon_icon:
                self.card_layout.addStretch()
                self.card_layout.addWidget(self.neon_icon, alignment=Qt.AlignCenter)
                self.card_layout.addStretch()

            # Usage label
            usage_label = QLabel("Usage")
            usage_label.setStyleSheet("font-size: 10px; color: #888;")
            usage_label.setAlignment(Qt.AlignLeft)
            self.card_layout.addWidget(usage_label)
            self.card_layout.addWidget(self.progress_bar)
        elif mode == "processes":
            # Layout: Title -> Icon -> Process List
            if self.neon_icon:
                self.card_layout.addWidget(self.neon_icon, alignment=Qt.AlignCenter)
            self.card_layout.addWidget(self.process_list)
        else:
            # Standard mode with temp
            if self.neon_icon:
                self.card_layout.addStretch()
                self.card_layout.addWidget(self.neon_icon, alignment=Qt.AlignCenter)
                self.card_layout.addStretch()
            self.card_layout.addWidget(self.temp_label)

    def update_data(self, usage, temp, model=""):
        """Update the card with new data."""

        # Update model name (standard and usage_only modes)
        if model and self.mode in ["standard", "usage_only"]:
            self.title_label.setText(model)

        # Update progress bar
        if self.progress_bar is not None:
            self.progress_bar.setValue(int(usage))

        # Update temperature
        if self.temp_label is not None:
            if temp is not None:
                self.temp_label.setText(f"{temp:.1f}°C")
                self.temp_label.show()  # Show if we have temp

                # ONLY apply background color for temp_only mode
                if self.mode == "temp_only":
                    if temp < 50:
                        bg_color = "#1a3a5c"  # Blue (Cool)
                    elif temp < 70:
                        bg_color = "#5c4a1a"  # Yellow/Orange (Warm)
                    else:
                        bg_color = "#5c1a1a"  # Red (Hot)

                    self._apply_background(bg_color)
            else:
                # Hide the temp label if no temperature data
                self.temp_label.hide()

    def update_processes(self, processes):
        """Update the process list."""
        if self.process_list is not None:
            self.process_list.clear()
            for proc in processes:
                item = QListWidgetItem(f"{proc['name']}: {proc['memory_mb']} MB")
                self.process_list.addItem(item)

    def update_fan_rpm(self, rpm):
        """Update fan animation and RPM text."""
        if hasattr(self, 'neon_icon') and self.neon_icon and self.mode == "temp_only":
            if rpm is not None and rpm > 0:
                self.neon_icon.set_rpm(rpm)
                self.rpm_label.setText(f"{int(rpm)} RPM")
            else:
                self.neon_icon.set_rpm(0)
                self.rpm_label.setText("N/A")

    def update_temp_icon_color(self, temp):
        """Change bottom icon color and type based on temperature."""
        if self.bottom_temp_icon is not None and temp is not None:
            if temp < 50:
                # Cool - show drop icon in blue
                self.bottom_temp_icon.icon_type = "drop"
                self.bottom_temp_icon.set_color("#4a9eff")
            elif temp < 70:
                # Warm - show drop icon in orange
                self.bottom_temp_icon.icon_type = "drop"
                self.bottom_temp_icon.set_color("#ffaa00")
            else:
                # Hot - show fire icon in red
                self.bottom_temp_icon.icon_type = "fire"
                self.bottom_temp_icon.set_color("#ff4444")

    def _apply_background(self, color):
        """Apply background color to the card frame."""
        self.current_bg_color = color
        self.card_frame.setStyleSheet(f"""
            #card_frame {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid #3a3a3a;
            }}
        """)
