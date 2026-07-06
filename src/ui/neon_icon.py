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

        # Animation variables
        self.angle = 0.0
        self.rpm = 0
        self.hover_factor = 0.0  # 0.0 = normal, 1.0 = full hover
        self.target_hover = 0.0

        # Timer for animations (runs at ~30 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animations)
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
        self.update()

    def set_rpm(self, rpm):
        """Set the RPM to control the fan speed."""
        self.rpm = rpm if rpm else 0

    def set_hover(self, is_hovering):
        """Set the target hover state for animation."""
        self.target_hover = 1.0 if is_hovering else 0.0

    def update_animations(self):
        """Update all animations (rotation and hover interpolation)."""
        # 1. Handle Fan Rotation (if it's a fan and has RPM)
        if self.icon_type == "fan" and self.rpm > 0:
            degrees_per_frame = (self.rpm / 60) * 1.5
            self.angle = (self.angle + degrees_per_frame) % 360

        # 2. Handle Hover Interpolation (smooth transition)
        # Move hover_factor towards target_hover by 0.1 per frame
        if self.hover_factor < self.target_hover:
            self.hover_factor = min(1.0, self.hover_factor + 0.1)
        elif self.hover_factor > self.target_hover:
            self.hover_factor = max(0.0, self.hover_factor - 0.1)

        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw the specific icon based on icon_type."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Setup pen for neon look
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
        base_size = min(w, h) * 0.6

        # --- CPU ICON ---
        if self.icon_type == "cpu":
            # Expansion effect: outer square gets bigger, inner gets smaller
            expand = self.hover_factor * 10

            # Outer square
            painter.drawRect(QRectF(cx - base_size/2 - expand, cy - base_size/2 - expand,
                                    base_size + expand*2, base_size + expand*2))
            # Inner square
            painter.drawRect(QRectF(cx - base_size/4 + expand/2, cy - base_size/4 + expand/2,
                                    base_size/2 - expand, base_size/2 - expand))

            # Corner pins (move outwards with expansion)
            pin_offset = 5 + expand
            painter.drawLine(QPointF(cx - base_size/2 - pin_offset, cy - base_size/2 - pin_offset),
                             QPointF(cx - base_size/2 + 5, cy - base_size/2 + 5))
            painter.drawLine(QPointF(cx + base_size/2 + pin_offset, cy - base_size/2 - pin_offset),
                             QPointF(cx + base_size/2 - 5, cy - base_size/2 + 5))
            painter.drawLine(QPointF(cx - base_size/2 - pin_offset, cy + base_size/2 + pin_offset),
                             QPointF(cx - base_size/2 + 5, cy + base_size/2 - 5))
            painter.drawLine(QPointF(cx + base_size/2 + pin_offset, cy + base_size/2 + pin_offset),
                             QPointF(cx + base_size/2 - 5, cy + base_size/2 - 5))

        # --- GPU ICON ---
        elif self.icon_type == "gpu":
            # Draw main body
            painter.drawRect(QRectF(cx - base_size/2, cy - base_size/3, base_size, base_size * 0.66))
            painter.drawEllipse(QPointF(cx, cy), base_size/4, base_size/4)

            # Fan blades (cross) - Rotate them on hover
            painter.save()
            painter.translate(cx, cy)
            # Rotate based on hover_factor (0 to 45 degrees)
            painter.rotate(self.hover_factor * 45)
            painter.drawLine(QPointF(0, -base_size/4), QPointF(0, base_size/4))
            painter.drawLine(QPointF(-base_size/4, 0), QPointF(base_size/4, 0))
            painter.restore()

        # --- RAM ICON ---
        elif self.icon_type == "ram":
            # Main stick
            painter.drawRect(QRectF(cx - base_size/2, cy - base_size/4, base_size, base_size/2))

            # Chips inside - Separate them on hover
            chip_gap = self.hover_factor * 5
            painter.drawRect(QRectF(cx - base_size/3 - chip_gap, cy - base_size/8, base_size/6, base_size/4))
            painter.drawRect(QRectF(cx - base_size/12, cy - base_size/8, base_size/6, base_size/4)) # Center chip stays
            painter.drawRect(QRectF(cx + base_size/6 + chip_gap, cy - base_size/8, base_size/6, base_size/4))

        # --- DISK ICON ---
        elif self.icon_type == "disk":
            # Outer case
            painter.drawRoundedRect(QRectF(cx - base_size/2, cy - base_size/2, base_size, base_size), 10, 10)

            # Inner platter (rotates on hover)
            painter.save()
            painter.translate(cx, cy)
            # Continuous rotation if hovering, else static
            rotation_angle = (self.angle if self.target_hover > 0 else 0)
            if self.target_hover > 0:
                self.angle = (self.angle + 2) % 360 # Slow spin

            painter.rotate(rotation_angle)

            # Draw platter with a small dot to show rotation
            painter.drawEllipse(QPointF(0, 0), base_size/5, base_size/5)
            painter.drawEllipse(QPointF(0, 0), base_size/6, base_size/6)
            # Small indicator dot
            painter.setBrush(QColor(self.color))
            painter.drawEllipse(QPointF(base_size/5 - 2, 0), 2, 2)
            painter.setBrush(Qt.NoBrush) # Reset brush

            painter.restore()

        # --- FAN ICON (Temperature cards) ---
        elif self.icon_type == "fan":
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self.angle)
            painter.translate(-cx, -cy)

            painter.drawEllipse(QPointF(cx, cy), base_size/5, base_size/5)
            for i in range(3):
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(i * 120)
                path = QPainterPath()
                path.moveTo(0, -base_size/6)
                path.quadTo(base_size/4, -base_size/2.5, 0, -base_size/2.5)
                path.quadTo(-base_size/4, -base_size/2.5, 0, -base_size/6)
                painter.drawPath(path)
                painter.restore()
            painter.restore()

        # --- FIRE ICON ---
        elif self.icon_type == "fire":
            path = QPainterPath()
            path.moveTo(QPointF(cx, cy - base_size/2))
            path.quadTo(QPointF(cx + base_size/2, cy), QPointF(cx, cy + base_size/2))
            path.quadTo(QPointF(cx - base_size/2, cy), QPointF(cx, cy - base_size/2))
            painter.drawPath(path)

        # --- DROP ICON ---
        elif self.icon_type == "drop":
            path = QPainterPath()
            path.moveTo(QPointF(cx, cy - base_size/2))
            path.quadTo(QPointF(cx + base_size/2, cy + base_size/4), QPointF(cx, cy + base_size/2))
            path.quadTo(QPointF(cx - base_size/2, cy + base_size/4), QPointF(cx, cy - base_size/2))
            painter.drawPath(path)

        # --- PROCESSES ICON ---
        elif self.icon_type == "processes":
            line_spacing = base_size / 4
            start_y = cy - line_spacing
            for i in range(3):
                painter.drawLine(QPointF(cx - base_size/3, start_y + i * line_spacing),
                                 QPointF(cx + base_size/3, start_y + i * line_spacing))
