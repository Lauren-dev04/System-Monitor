# Import Qt classes for widgets, painting, and effects
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush


class NeonIconWidget(QWidget):
    """Widget that draws neon-style hardware icons with a glow effect."""

    def __init__(self, icon_type, color="#4a9eff", parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.color = color

        # Set a fixed size for the icon
        self.setFixedSize(140, 140)

        # Animation
        self.angle = 0.0
        self.rpm = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(33)

        # Create the neon glow effect
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(15)
        self.glow_effect.setColor(QColor(self.color))
        self.glow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.glow_effect)

    def set_color(self, color):
        """Update the icon color and glow dynamically."""
        self.color = color
        self.glow_effect.setColor(QColor(color))
        self.update()  # Trigger repaint

    def set_rpm(self, rpm):
        """Set the RPM to control the fan speed."""
        self.rpm = rpm if rpm else 0

    def update_angle(self):
        """Update the rotation angle based on RPM."""
        # Only rotate if it's a fan and has RPM
        if self.icon_type == "fan" and self.rpm > 0:
            degrees_per_frame = (self.rpm / 60) * 1.5  # Rotation speed
            self.angle = (self.angle + degrees_per_frame) % 360

        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw the specific icon based on icon_type."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Setup pen for neon look (no fill, bright outline)
        pen = QPen(QColor(self.color))
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        size = min(w, h) * 0.6  # Base size for the icon

        if self.icon_type == "cpu":
            # Draw CPU: Outer square, inner square, and corner pins
            painter.drawRect(QRectF(cx - size/2, cy - size/2, size, size))
            painter.drawRect(QRectF(cx - size/4, cy - size/4, size/2, size/2))
            # Corner pins
            painter.drawLine(QPointF(cx - size/2 - 5, cy - size/2 - 5), QPointF(cx - size/2 + 5, cy - size/2 + 5))
            painter.drawLine(QPointF(cx + size/2 + 5, cy - size/2 - 5), QPointF(cx + size/2 - 5, cy - size/2 + 5))
            painter.drawLine(QPointF(cx - size/2 - 5, cy + size/2 + 5), QPointF(cx - size/2 + 5, cy + size/2 - 5))
            painter.drawLine(QPointF(cx + size/2 + 5, cy + size/2 + 5), QPointF(cx + size/2 - 5, cy + size/2 - 5))

        elif self.icon_type == "gpu":
            # Draw GPU: Rectangle with a fan circle inside
            painter.drawRect(QRectF(cx - size/2, cy - size/3, size, size * 0.66))
            painter.drawEllipse(QPointF(cx, cy), size/4, size/4)
            # Fan blades (simple lines)
            painter.drawLine(QPointF(cx, cy - size/4), QPointF(cx, cy + size/4))
            painter.drawLine(QPointF(cx - size/4, cy), QPointF(cx + size/4, cy))

        elif self.icon_type == "ram":
            # Draw RAM: Long rectangle with chips
            painter.drawRect(QRectF(cx - size/2, cy - size/4, size, size/2))
            # Chips inside
            painter.drawRect(QRectF(cx - size/3, cy - size/8, size/6, size/4))
            painter.drawRect(QRectF(cx, cy - size/8, size/6, size/4))
            painter.drawRect(QRectF(cx + size/6, cy - size/8, size/6, size/4))

        elif self.icon_type == "disk":
            # Draw Disk: Rounded rectangle with a circle (platter)
            painter.drawRoundedRect(QRectF(cx - size/2, cy - size/2, size, size), 10, 10)
            painter.drawEllipse(QPointF(cx, cy), size/5, size/5)
            painter.drawEllipse(QPointF(cx, cy), size/6, size/6)

        elif self.icon_type == "fan":
            # Save state and rotate the entire fan assembly
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self.angle)
            painter.translate(-cx, -cy)  # Return to origin to draw

            # Draw blades and center hub
            painter.drawEllipse(QPointF(cx, cy), size/5, size/5)
            for i in range(3):
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(i * 120)

                # Blade shape
                path = QPainterPath()
                path.moveTo(0, -size/6)
                path.quadTo(size/4, -size/2.5, 0, -size/2.5)
                path.quadTo(-size/4, -size/2.5, 0, -size/6)
                painter.drawPath(path)
                painter.restore()

            # Restore original state
            painter.restore()

        elif self.icon_type == "fire":
            # Draw Fire: Stylized flame
            path = QPainterPath()
            path.moveTo(QPointF(cx, cy - size/2))
            path.quadTo(QPointF(cx + size/2, cy), QPointF(cx, cy + size/2))
            path.quadTo(QPointF(cx - size/2, cy), QPointF(cx, cy - size/2))
            painter.drawPath(path)

        elif self.icon_type == "drop":
            # Draw Drop: Water drop shape
            path = QPainterPath()
            path.moveTo(QPointF(cx, cy - size/2))
            path.quadTo(QPointF(cx + size/2, cy + size/4), QPointF(cx, cy + size/2))
            path.quadTo(QPointF(cx - size/2, cy + size/4), QPointF(cx, cy - size/2))
            painter.drawPath(path)

        elif self.icon_type == "processes":
            # Draw Processes: List icon (3 horizontal lines)
            line_spacing = size / 4
            start_y = cy - line_spacing
            for i in range(3):
                painter.drawLine(QPointF(cx - size/3, start_y + i * line_spacing),
                                 QPointF(cx + size/3, start_y + i * line_spacing))
