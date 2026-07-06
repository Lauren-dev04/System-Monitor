from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
import math


class FanWidget(QWidget):
    """Animated fan blade widget that rotates based on RPM."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(40, 40)

        # Animation timer
        self.angle = 0
        self.rpm = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(33)  # Update every 33ms (~30 FPS)

    def set_rpm(self, rpm):
        """Set the fan RPM."""
        self.rpm = rpm if rpm else 0

    def update_angle(self):
        """Update the rotation angle based on RPM."""
        # Calculate rotation speed: higher RPM = faster rotation
        if self.rpm > 0:
            degrees_per_frame = (self.rpm / 60) * 1.5
            self.angle = (self.angle + degrees_per_frame) % 360

        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw the fan blades."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Center of the widget
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 2

        # Draw fan blades
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)

        # Draw 3 blades
        for i in range(3):
            painter.rotate(120)

            # Create blade polygon using QPolygonF
            blade = QPolygonF([
                QPoint(0, -radius),
                QPoint(radius * 0.3, -radius * 0.3),
                QPoint(radius * 0.5, 0),
                QPoint(radius * 0.3, radius * 0.3),
                QPoint(0, radius * 0.5)
            ])

            # Draw blade
            painter.setPen(QPen(QColor("#4a9eff"), 2))
            painter.setBrush(QBrush(QColor("#4a9eff")))
            painter.drawPolygon(blade)

        painter.restore()

        # Draw center hub
        painter.setPen(QPen(QColor("#4a9eff"), 2))
        painter.setBrush(QBrush(QColor("#4a9eff")))
        painter.drawEllipse(center_x - 4, center_y - 4, 8, 8)
