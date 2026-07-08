# Import Qt widgets for building the detailed disk view
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# Import custom neon icon widget
from .neon_icon import NeonIconWidget


class DiskDetailView(QWidget):
    """Detailed Disk view: list of all disks with usage, I/O stats, and mount points."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ================= HEADER =================
        header = QHBoxLayout()
        self.header_icon = NeonIconWidget("disk")
        header.addWidget(self.header_icon)

        header_text_layout = QVBoxLayout()
        title = QLabel("Disk Information")
        title.setStyleSheet("font-size: 13px; color: #888;")
        self.header_count_label = QLabel("0 Disks Found")
        self.header_count_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(self.header_count_label)
        header.addLayout(header_text_layout)

        header.addStretch()

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

        # ================= DISK TABLE =================
        table_frame = self._make_section_frame("All Disks")
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(7)
        self.disk_table.setHorizontalHeaderLabels([
            "Disk Name", "Model", "Mount Points", "Total", "Used", "Free", "Usage %"
        ])
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.setStyleSheet(self._table_style())
        table_frame.layout().addWidget(self.disk_table)
        layout.addWidget(table_frame, stretch=1)

        # ================= I/O TABLE =================
        io_frame = self._make_section_frame("Disk I/O Statistics")
        self.io_table = QTableWidget()
        self.io_table.setColumnCount(3)
        self.io_table.setHorizontalHeaderLabels(["Disk Name", "Read (MB)", "Write (MB)"])
        self.io_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.io_table.verticalHeader().setVisible(False)
        self.io_table.setStyleSheet(self._table_style())
        io_frame.layout().addWidget(self.io_table)
        layout.addWidget(io_frame)

        # ================= FOOTER =================
        footer = QHBoxLayout()
        self.status_label = QLabel("Disk Status: Monitoring")
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

    def update_disk_detail(self, disks):
        """Slot for MonitorThread.disk_detail_data."""
        # Update header
        self.header_count_label.setText(f"{len(disks)} Disks Found")

        # Update disk table
        self.disk_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            self.disk_table.setItem(row, 0, QTableWidgetItem(disk.get('disk_name', 'Unknown')))
            self.disk_table.setItem(row, 1, QTableWidgetItem(disk.get('model', 'Unknown')))
            self.disk_table.setItem(row, 2, QTableWidgetItem(disk.get('mountpoints', 'N/A')))
            self.disk_table.setItem(row, 3, QTableWidgetItem(f"{disk.get('total_gb', 0)} GB"))
            self.disk_table.setItem(row, 4, QTableWidgetItem(f"{disk.get('used_gb', 0)} GB"))
            self.disk_table.setItem(row, 5, QTableWidgetItem(f"{disk.get('free_gb', 0)} GB"))

            percent_item = QTableWidgetItem(f"{disk.get('percent', 0)}%")
            percent = disk.get('percent', 0)
            if percent < 50:
                percent_item.setForeground(QColor("#4a9eff"))
            elif percent < 80:
                percent_item.setForeground(QColor("#ffaa00"))
            else:
                percent_item.setForeground(QColor("#ff4444"))
            self.disk_table.setItem(row, 6, percent_item)

        # Update I/O table
        self.io_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            self.io_table.setItem(row, 0, QTableWidgetItem(disk.get('disk_name', 'Unknown')))
            self.io_table.setItem(row, 1, QTableWidgetItem(f"{disk.get('read_mb', 0)} MB"))
            self.io_table.setItem(row, 2, QTableWidgetItem(f"{disk.get('write_mb', 0)} MB"))
