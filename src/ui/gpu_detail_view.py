# Import Qt widgets for building the detailed GPU view
from collections import deque
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

# Import custom neon icon widget
from .neon_icon import NeonIconWidget


def temp_color(temp):
    """Return a color hex based on temperature thresholds."""
    if temp is None:
        return "#666666"
    if temp < 50:
        return "#4a9eff"
    elif temp < 70:
        return "#ffaa00"
    else:
        return "#ff4444"


class RealtimeGraph(QWidget):
    """Custom real-time line chart for GPU metrics."""

    def __init__(self, max_points=60, parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.history = deque(maxlen=max_points)
        self.setMinimumHeight(150)

    def update_value(self, value):
        """Push a new value into the rolling history."""
        self.history.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#1e1e1e"))

        # Grid lines with % labels
        font = QFont("Ubuntu", 8)
        painter.setFont(font)
        for pct in (0, 20, 40, 60, 80, 100):
            y = h - (pct / 100) * h
            painter.setPen(QPen(QColor("#2a2a2a"), 1))
            painter.drawLine(0, int(y), w, int(y))
            painter.setPen(QColor("#666666"))
            painter.drawText(4, max(int(y) - 2, 10), f"{pct}%")

        if len(self.history) < 2:
            painter.end()
            return

        # Draw line
        step_x = w / max(self.max_points - 1, 1)
        painter.setPen(QPen(QColor("#4a9eff"), 2))

        points = list(self.history)
        n = len(points)
        x_offset = (self.max_points - n) * step_x

        for i in range(n - 1):
            x1 = x_offset + i * step_x
            y1 = h - (points[i] / 100) * h
            x2 = x_offset + (i + 1) * step_x
            y2 = h - (points[i + 1] / 100) * h
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.end()


class GpuDetailView(QWidget):
    """Detailed GPU view: real-time usage graph, VRAM graph, temperature, and specs."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ================= HEADER =================
        header = QHBoxLayout()
        self.header_icon = NeonIconWidget("gpu")
        header.addWidget(self.header_icon)

        header_text_layout = QVBoxLayout()
        title = QLabel("GPU Information")
        title.setStyleSheet("font-size: 13px; color: #888;")
        self.header_model_label = QLabel("Unknown GPU")
        self.header_model_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        self.header_usage_label = QLabel("Usage: --%")
        self.header_usage_label.setStyleSheet("font-size: 12px; color: #888;")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(self.header_model_label)
        header_text_layout.addWidget(self.header_usage_label)
        header.addLayout(header_text_layout)

        header.addStretch()

        self.header_temp_label = QLabel("--°C")
        self.header_temp_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(self.header_temp_label)
        header.addSpacing(20)

        self.back_button = QPushButton("← Back to Main")
        self.back_button.setFixedSize(150, 40)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setStyleSheet("""
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
        header.addWidget(self.back_button)
        layout.addLayout(header)

        # ================= USAGE GRAPH =================
        usage_frame = self._make_section_frame("Real-time GPU Usage")
        self.usage_graph = RealtimeGraph()
        usage_frame.layout().addWidget(self.usage_graph)
        layout.addWidget(usage_frame)

        # ================= VRAM GRAPH + INFO (side by side) =================
        row2 = QHBoxLayout()

        vram_frame = self._make_section_frame("VRAM Usage")
        self.vram_graph = RealtimeGraph()
        vram_frame.layout().addWidget(self.vram_graph)
        row2.addWidget(vram_frame, stretch=1)

        info_frame = self._make_section_frame("GPU Specifications")
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.setStyleSheet(self._table_style())
        info_frame.layout().addWidget(self.info_table)
        row2.addWidget(info_frame, stretch=1)

        layout.addLayout(row2)

        # ================= FOOTER =================
        footer = QHBoxLayout()
        self.status_label = QLabel("GPU Status: Monitoring")
        self.status_label.setStyleSheet("font-size: 11px; color: #666;")
        footer.addWidget(self.status_label)
        footer.addStretch()
        layout.addLayout(footer)

    def _make_section_frame(self, title_text):
        """Helper to create a styled section frame."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 1px solid #3a3a3a;
            }
        """)
        v = QVBoxLayout(frame)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #4a9eff;")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        return frame

    def _table_style(self):
        """Return stylesheet for tables."""
        return """
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: none;
                gridline-color: #3a3a3a;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #4a9eff;
                border: none;
                padding: 4px;
                font-weight: bold;
            }
        """

    def update_gpu_detail(self, data):
        """Slot for MonitorThread.gpu_detail_data."""
        # Update header
        self.header_model_label.setText(data.get('model', 'Unknown GPU'))
        self.header_usage_label.setText(f"Usage: {data.get('usage', 0)}%")

        temp = data.get('temp')
        if temp is not None:
            self.header_temp_label.setText(f"{temp:.1f}°C")
            self.header_temp_label.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {temp_color(temp)};")
        else:
            self.header_temp_label.setText("N/A")

        # Update graphs
        self.usage_graph.update_value(data.get('usage', 0))

        # Calculate VRAM percentage
        vram_used = data.get('vram_used_mb', 0)
        vram_total = data.get('vram_total_mb', 1)
        vram_percent = (vram_used / vram_total * 100) if vram_total > 0 else 0
        self.vram_graph.update_value(vram_percent)

        # Update info table
        self.info_table.setRowCount(5)

        items = [
            ("Model", data.get('model', 'Unknown')),
            ("Temperature", f"{temp:.1f}°C" if temp else "N/A"),
            ("VRAM Used", f"{vram_used:.1f} MB"),
            ("VRAM Total", f"{vram_total:.1f} MB"),
            ("Frequency", f"{data.get('frequency_mhz', 0)} MHz" if data.get('frequency_mhz') else "N/A")
        ]

        for row, (prop, value) in enumerate(items):
            self.info_table.setItem(row, 0, QTableWidgetItem(prop))
            self.info_table.setItem(row, 1, QTableWidgetItem(value))
