# Import necessary PySide6 classes for building the UI
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QLabel, QGridLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QBrush, QColor, QPixmap, QPainter, QPen

# Import our custom UI components
from .hardware_card import HardwareCard
from .cpu_detail_view import CpuDetailView

# Import hardware monitoring functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hardware.monitor_thread import MonitorThread


class MainWindow(QMainWindow):
    """Main application window for the System Monitor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.resize(1200, 700)
        self.process_update_counter = 0

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main vertical layout (content only, sidebar removed)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Content area (now takes full space)
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # Create pages
        self.create_content_pages()
        self.switch_page('main')

        # Apply theme with pattern
        self.apply_dark_theme()

        # Background thread for hardware monitoring (non-blocking)
        self.monitor_thread = MonitorThread()

        # Connect signals to slots
        self.monitor_thread.cpu_data.connect(self.on_cpu_data)
        self.monitor_thread.gpu_data.connect(self.on_gpu_data)
        self.monitor_thread.ram_data.connect(self.on_ram_data)
        self.monitor_thread.disks_data.connect(self.on_disks_data)
        self.monitor_thread.fans_data.connect(self.on_fans_data)
        self.monitor_thread.processes_data.connect(self.on_processes_data)

        # Connect new signals for the detailed CPU view
        self.monitor_thread.cpu_detail_data.connect(self.cpu_detail_view.update_cpu_detail)
        self.monitor_thread.processes_detail_data.connect(self.cpu_detail_view.update_processes)

        # Start the background thread
        self.monitor_thread.start()

    def create_content_pages(self):
        """Create content pages."""
        self.page_indices = {}
        sections = ['main', 'cpu', 'gpu', 'ram', 'disk']

        for index, section in enumerate(sections):
            if section == 'main':
                # Create main view container with pattern background
                main_container = QWidget()
                # Apply pattern background to this container
                pattern_pixmap = self.create_circuit_pattern()
                palette = QPalette()
                palette.setBrush(QPalette.Window, QBrush(pattern_pixmap))
                main_container.setPalette(palette)
                main_container.setAutoFillBackground(True)

                main_layout = QVBoxLayout(main_container)
                main_layout.setContentsMargins(30, 30, 30, 30)
                main_layout.setSpacing(15)

                # Create grid layout for 2 rows x 4 columns
                grid_layout = QGridLayout()
                grid_layout.setSpacing(15)

                # ROW 0: Standard cards (Clickable)
                card_cpu = HardwareCard("CPU", mode="usage_only", icon_type="cpu", click_target="cpu")
                card_cpu.card_clicked.connect(self.switch_page)

                card_gpu = HardwareCard("GPU", mode="usage_only", icon_type="gpu", click_target="gpu")
                card_gpu.card_clicked.connect(self.switch_page)

                card_ram = HardwareCard("RAM", mode="standard", icon_type="ram", click_target="ram")
                card_ram.card_clicked.connect(self.switch_page)

                card_disk1 = HardwareCard("DISK 1", mode="standard", icon_type="disk", click_target="disk")
                card_disk1.card_clicked.connect(self.switch_page)

                grid_layout.addWidget(card_cpu, 0, 0)
                grid_layout.addWidget(card_gpu, 0, 1)
                grid_layout.addWidget(card_ram, 0, 2)
                grid_layout.addWidget(card_disk1, 0, 3)

                # ROW 1: Specialized cards
                card_cpu_temp = HardwareCard("CPU Temperature", mode="temp_only", icon_type="fan")
                card_gpu_temp = HardwareCard("GPU Temperature", mode="temp_only", icon_type="fan")
                card_processes = HardwareCard("Top 5 Processes", mode="processes", icon_type="processes")

                card_disk2 = HardwareCard("DISK 2", mode="standard", icon_type="disk", click_target="disk")
                card_disk2.card_clicked.connect(self.switch_page)

                grid_layout.addWidget(card_cpu_temp, 1, 0)
                grid_layout.addWidget(card_gpu_temp, 1, 1)
                grid_layout.addWidget(card_processes, 1, 2)
                grid_layout.addWidget(card_disk2, 1, 3)

                main_layout.addLayout(grid_layout)
                self.content_stack.addWidget(main_container)

                # Store references
                self.cards = {
                    'cpu': card_cpu,
                    'gpu': card_gpu,
                    'ram': card_ram,
                    'disk1': card_disk1,
                    'cpu_temp': card_cpu_temp,
                    'gpu_temp': card_gpu_temp,
                    'processes': card_processes,
                    'disk2': card_disk2
                }

            elif section == 'cpu':
                # Detailed CPU view (replaces the old "Coming Soon" placeholder)
                page_container = QWidget()
                page_container.setAutoFillBackground(True)
                pattern_pixmap = self.create_circuit_pattern()
                palette = QPalette()
                palette.setBrush(QPalette.Window, QBrush(pattern_pixmap))
                page_container.setPalette(palette)

                page_layout = QVBoxLayout(page_container)
                page_layout.setContentsMargins(0, 0, 0, 0)

                self.cpu_detail_view = CpuDetailView()
                self.cpu_detail_view.back_button.clicked.connect(lambda: self.switch_page('main'))
                page_layout.addWidget(self.cpu_detail_view)

                self.content_stack.addWidget(page_container)

            else:
                # Create page container
                page_container = QWidget()
                page_container.setAutoFillBackground(True)
                pattern_pixmap = self.create_circuit_pattern()
                palette = QPalette()
                palette.setBrush(QPalette.Window, QBrush(pattern_pixmap))
                page_container.setPalette(palette)

                page_layout = QVBoxLayout(page_container)

                # --- Back Button ---
                back_button = QPushButton("← Back to Main")
                back_button.setFixedSize(150, 40)
                back_button.setCursor(Qt.PointingHandCursor)
                back_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2a2a2a;
                        color: #4a9eff;
                        border: 1px solid #4a9eff;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #4a9eff;
                        color: #1a1a1a;
                    }
                """)
                back_button.clicked.connect(lambda: self.switch_page('main'))

                page_layout.addWidget(back_button, alignment=Qt.AlignCenter)
                page_layout.addSpacing(20)

                label = QLabel(f"{section.upper()} View - Coming Soon")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #888; font-size: 18px;")
                page_layout.addWidget(label)

                self.content_stack.addWidget(page_container)

            self.page_indices[section] = index

    def on_cpu_data(self, cpu_info):
        """Handle CPU data received from the background thread."""
        self.cards['cpu'].update_data(cpu_info['usage'], cpu_info['temp'], model=cpu_info['model'])
        self.cards['cpu_temp'].update_data(0, cpu_info['temp'])
        self.cards['cpu_temp'].update_temp_icon_color(cpu_info['temp'])

    def on_gpu_data(self, gpu_info):
        """Handle GPU data received from the background thread."""
        self.cards['gpu'].update_data(gpu_info['usage'], gpu_info['temp'], model=gpu_info['model'])
        self.cards['gpu_temp'].update_data(0, gpu_info['temp'])
        self.cards['gpu_temp'].update_temp_icon_color(gpu_info['temp'])

    def on_ram_data(self, ram_info):
        """Handle RAM data received from the background thread."""
        self.cards['ram'].update_data(ram_info['percent'], None, model=ram_info['model'])

    def on_disks_data(self, disks_info):
        """Handle disks data received from the background thread."""
        if len(disks_info) >= 1:
            self.cards['disk1'].update_data(disks_info[0]['percent'], None, model=disks_info[0]['model'])
        if len(disks_info) >= 2:
            self.cards['disk2'].update_data(disks_info[1]['percent'], None, model=disks_info[1]['model'])

    def on_fans_data(self, fans_info):
        """Handle fan data received from the background thread."""
        self.cards['cpu_temp'].update_fan_rpm(fans_info['cpu_fan_rpm'])
        self.cards['gpu_temp'].update_fan_rpm(fans_info['gpu_fan_rpm'])

    def on_processes_data(self, processes_info):
        """Handle processes data received from the background thread."""
        self.cards['processes'].update_processes(processes_info)

    def switch_page(self, page_name):
        """Switch visible page."""
        if page_name in self.page_indices:
            self.content_stack.setCurrentIndex(self.page_indices[page_name])

    def create_circuit_pattern(self):
        """Create a subtle circuit/tech pattern as background."""
        pattern_size = 100
        pixmap = QPixmap(pattern_size, pattern_size)
        pixmap.fill(QColor("#1a1a1a"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#252525"), 1)
        painter.setPen(pen)

        painter.drawLine(0, 25, 100, 25)
        painter.drawLine(0, 75, 100, 75)
        painter.drawLine(25, 0, 25, 100)
        painter.drawLine(75, 0, 75, 100)

        painter.setBrush(QColor("#2a2a2a"))
        painter.drawRect(23, 23, 4, 4)
        painter.drawRect(73, 23, 4, 4)
        painter.drawRect(23, 73, 4, 4)
        painter.drawRect(73, 73, 4, 4)

        painter.drawLine(10, 10, 20, 20)
        painter.drawLine(80, 80, 90, 90)
        painter.end()

        return pixmap

    def apply_dark_theme(self):
        """Apply dark theme with circuit pattern background."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                color: #e0e0e0;
                font-family: 'Ubuntu', 'Segoe UI', sans-serif;
            }
        """)

    def closeEvent(self, event):
        """Stop the monitoring thread when the window is closed."""
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        event.accept()
