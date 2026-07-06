# Import Qt widgets for building the detailed CPU view
from collections import deque
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

from .neon_icon import NeonIconWidget

# Color palette cycled per core, both in the graph lines and the legend labels
CORE_COLORS = [
    "#4a9eff", "#ff6b6b", "#51cf66", "#ffd43b",
    "#cc5de8", "#22b8cf", "#ff922b", "#845ef7",
    "#20c997", "#f06595", "#94d82d", "#fcc419",
]


def temp_color(temp):
    """Return a color hex based on temperature thresholds, matching the main cards."""
    if temp is None:
        return "#666666"
    if temp < 50:
        return "#4a9eff"
    elif temp < 70:
        return "#ffaa00"
    else:
        return "#ff4444"


class RealtimeUsageGraph(QWidget):
    """Custom real-time multi-line chart for per-core CPU usage (no external deps)."""

    def __init__(self, max_points=60, parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.history = []  # one deque per core
        self.setMinimumHeight(180)

    def update_usage(self, per_core_usage):
        """Push a new usage sample for each core into the rolling history."""
        if len(self.history) != len(per_core_usage):
            self.history = [deque(maxlen=self.max_points) for _ in per_core_usage]
        for i, usage in enumerate(per_core_usage):
            self.history[i].append(usage)
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

        if not self.history:
            painter.end()
            return

        step_x = w / max(self.max_points - 1, 1)

        for core_idx, core_history in enumerate(self.history):
            if len(core_history) < 2:
                continue
            color = QColor(CORE_COLORS[core_idx % len(CORE_COLORS)])
            painter.setPen(QPen(color, 1.5))

            points = list(core_history)
            n = len(points)
            x_offset = (self.max_points - n) * step_x

            for i in range(n - 1):
                x1 = x_offset + i * step_x
                y1 = h - (points[i] / 100) * h
                x2 = x_offset + (i + 1) * step_x
                y2 = h - (points[i + 1] / 100) * h
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.end()


class CpuDetailView(QWidget):
    """Detailed CPU view: real-time per-core graph, temperature table, VCore (auto),
    frequency, real cache sizes, and a detailed process table (CPU%, memory, threads, status).
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ================= HEADER =================
        header = QHBoxLayout()

        self.header_icon = NeonIconWidget("cpu")
        header.addWidget(self.header_icon)

        header_text_layout = QVBoxLayout()
        title = QLabel("Global Average CPU Temperature")
        title.setStyleSheet("font-size: 13px; color: #888;")
        self.header_temp_label = QLabel("--°C")
        self.header_temp_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #e0e0e0;")
        self.header_usage_label = QLabel("Usage: --%")
        self.header_usage_label.setStyleSheet("font-size: 12px; color: #888;")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(self.header_temp_label)
        header_text_layout.addWidget(self.header_usage_label)
        header.addLayout(header_text_layout)

        header.addStretch()

        # VCore: shown only if auto-detected on this hardware, hidden otherwise
        self.vcore_label = QLabel("")
        self.vcore_label.setStyleSheet("font-size: 13px; color: #4a9eff; font-weight: bold;")
        self.vcore_label.hide()
        header.addWidget(self.vcore_label)

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

        # ================= REAL-TIME GRAPH =================
        graph_frame = self._make_section_frame("Real-time CPU Usage (per core)")
        graph_row = QHBoxLayout()

        self.graph = RealtimeUsageGraph()
        graph_row.addWidget(self.graph, stretch=4)

        self.core_legend_layout = QVBoxLayout()
        self.core_legend_labels = []
        legend_widget = QWidget()
        legend_widget.setLayout(self.core_legend_layout)
        legend_widget.setFixedWidth(140)
        graph_row.addWidget(legend_widget, stretch=1)

        graph_frame.layout().addLayout(graph_row)
        layout.addWidget(graph_frame)

        # ================= TEMP TABLE + FREQ/CACHE (side by side) =================
        row2 = QHBoxLayout()

        temp_frame = self._make_section_frame("Core Temperature")
        self.temp_table = QTableWidget()
        self.temp_table.setColumnCount(2)
        self.temp_table.setHorizontalHeaderLabels(["Core", "Temp (°C)"])
        self.temp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.temp_table.verticalHeader().setVisible(False)
        self.temp_table.setStyleSheet(self._table_style())
        temp_frame.layout().addWidget(self.temp_table)
        row2.addWidget(temp_frame, stretch=1)

        freq_cache_frame = self._make_section_frame("Frequency & Cache")
        self.freq_label = QLabel("Current Frequency: -- GHz")
        self.freq_label.setAlignment(Qt.AlignCenter)
        self.freq_label.setStyleSheet("font-size: 14px; color: #e0e0e0; padding: 4px;")
        freq_cache_frame.layout().addWidget(self.freq_label)

        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(2)
        self.cache_table.setHorizontalHeaderLabels(["Cache", "Size"])
        self.cache_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cache_table.verticalHeader().setVisible(False)
        self.cache_table.setStyleSheet(self._table_style())
        freq_cache_frame.layout().addWidget(self.cache_table)
        row2.addWidget(freq_cache_frame, stretch=1)

        layout.addLayout(row2)

        # ================= PROCESSES TABLE =================
        proc_frame = self._make_section_frame("Top Processes (Detailed)")
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(
            ["Process Name", "CPU Usage (%)", "Memory (MB)", "Thread Count", "Status"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setStyleSheet(self._table_style())
        proc_frame.layout().addWidget(self.process_table)
        layout.addWidget(proc_frame, stretch=1)

        # ================= FOOTER =================
        footer = QHBoxLayout()
        self.uptime_label = QLabel("Uptime: --")
        self.uptime_label.setStyleSheet("font-size: 11px; color: #666;")
        self.sensors_label = QLabel("Sensors: OK")
        self.sensors_label.setStyleSheet("font-size: 11px; color: #666;")
        footer.addWidget(self.uptime_label)
        footer.addStretch()
        footer.addWidget(self.sensors_label)
        layout.addLayout(footer)

    # ---------- helpers ----------
    def _make_section_frame(self, title_text):
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

    # ---------- data update slots (connect these to MonitorThread signals) ----------
    def update_cpu_detail(self, data):
        """Slot for MonitorThread.cpu_detail_data."""
        avg_temp = data.get('avg_temp')
        if avg_temp is not None:
            self.header_temp_label.setText(f"{avg_temp:.1f}°C")
        else:
            self.header_temp_label.setText("N/A")

        self.header_usage_label.setText(f"Usage: {data.get('overall_usage', 0):.1f}%")

        # VCore: auto — show if detected, hide (not fabricate) if not
        vcore = data.get('vcore')
        if vcore is not None:
            self.vcore_label.setText(f"VCore: {vcore:.3f} V")
            self.vcore_label.show()
        else:
            self.vcore_label.hide()

        per_core = data.get('per_core_usage', [])
        self.graph.update_usage(per_core)
        self._update_legend(per_core)
        self._update_temp_table(data.get('per_core_temp', {}))

        freqs = data.get('per_core_freq', [])
        if freqs:
            avg_freq_ghz = (sum(freqs) / len(freqs)) / 1000
            self.freq_label.setText(f"Current Frequency: {avg_freq_ghz:.2f} GHz (avg)")
        else:
            self.freq_label.setText("Current Frequency: N/A")

        self._update_cache_table(data.get('cache_sizes', {}))

        uptime_sec = data.get('uptime_seconds', 0)
        h = uptime_sec // 3600
        m = (uptime_sec % 3600) // 60
        self.uptime_label.setText(f"Uptime: {h}h {m}m")

    def update_processes(self, processes):
        """Slot for MonitorThread.processes_detail_data."""
        self.process_table.setRowCount(len(processes))
        for row, proc in enumerate(processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(proc['name']))
            self.process_table.setItem(row, 1, QTableWidgetItem(f"{proc['cpu_percent']:.1f}"))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{proc['memory_mb']:.1f}"))
            self.process_table.setItem(row, 3, QTableWidgetItem(str(proc['threads'])))
            self.process_table.setItem(row, 4, QTableWidgetItem(proc['status']))

    # ---------- internal update helpers ----------
    def _update_legend(self, per_core):
        if len(self.core_legend_labels) != len(per_core):
            for lbl in self.core_legend_labels:
                lbl.setParent(None)
            self.core_legend_labels = []
            for i in range(len(per_core)):
                lbl = QLabel()
                color = CORE_COLORS[i % len(CORE_COLORS)]
                lbl.setStyleSheet(f"font-size: 11px; color: {color};")
                self.core_legend_layout.addWidget(lbl)
                self.core_legend_labels.append(lbl)
            self.core_legend_layout.addStretch()

        for i, usage in enumerate(per_core):
            self.core_legend_labels[i].setText(f"Core {i}: {usage:.1f}%")

    def _update_temp_table(self, per_core_temp):
        cores = sorted(per_core_temp.keys())
        self.temp_table.setRowCount(len(cores))
        for row, core_num in enumerate(cores):
            temp = per_core_temp[core_num]
            self.temp_table.setItem(row, 0, QTableWidgetItem(f"Core {core_num}"))
            temp_item = QTableWidgetItem(f"{temp:.1f}°C")
            temp_item.setForeground(QColor(temp_color(temp)))
            self.temp_table.setItem(row, 1, temp_item)

    def _update_cache_table(self, cache_sizes):
        keys = sorted(cache_sizes.keys())
        self.cache_table.setRowCount(len(keys))
        for row, key in enumerate(keys):
            self.cache_table.setItem(row, 0, QTableWidgetItem(key.upper()))
            self.cache_table.setItem(row, 1, QTableWidgetItem(cache_sizes[key]))
