import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
)
from PySide6.QtWidgets import QWidget


class WavePattern(QWidget):
    """Event driven wave pattern to display listener state.

    >>> WavePattern

    """

    def __init__(self):
        """Initialize the WavePattern widget.

        See Also:
            - Sets up the window properties, animation parameters, and timer.
            - The widget starts in an idle state with zero amplitude.
            - A QTimer is configured but not started until animation begins.
        """
        super().__init__()
        self.resize(600, 500)
        self.setWindowTitle("Event Driven Wave Pattern")
        self.phase = 0
        self.speed = 0.06
        self.target_amplitude = 220
        self.current_amplitude = 0
        self.state = "idle"  # idle | running | settling

        # Timer only used when needed
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

    def start(self) -> None:
        """Start the wave animation.

        See Also:
            - | Transitions the widget state to "running" and starts the animation
              | timer if it is not already active.
            - The amplitude smoothly ramps up toward the target amplitude during animation.
        """
        self.state = "running"
        if not self.timer.isActive():
            self.timer.start(16)

    def stop(self) -> None:
        """Stop the wave animation.

        See Also:
            - Transitions the widget state to "settling" and starts the animation timer if needed.
            - During settling, the amplitude smoothly decays toward zero.
            - The timer automatically stops once the amplitude becomes negligible.
        """
        self.state = "settling"
        if not self.timer.isActive():
            self.timer.start(16)

    def animate(self) -> None:
        """Advance the animation by one frame. After updating animation parameters, schedules a repaint.

        See Also:
            This method is triggered by the QTimer timeout signal.
            Behavior depends on the current state:

            - "running": Increases phase and smoothly interpolates the current amplitude toward the target amplitude.
            - | "settling": Increases phase and exponentially decays the amplitude toward zero.
              | Stops the timer once the amplitude becomes minimal.
            - "idle": No animation updates occur.
        """
        if self.state == "running":
            self.phase += self.speed
            # smooth ramp up
            self.current_amplitude += (self.target_amplitude - self.current_amplitude) * 0.08

        elif self.state == "settling":
            self.phase += self.speed
            # smooth ramp down
            self.current_amplitude *= 0.92

            # Instead of forcing to 0, just stop when nearly still
            if self.current_amplitude < 1:
                self.state = "idle"
                self.timer.stop()

        self.update()

    # noinspection PyUnresolvedReferences
    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the animated wave pattern.

        See Also:
            - Paints multiple layered sine waves with a Gaussian envelope centered vertically in the widget.
            - Each layer uses a horizontal linear gradient and additive blending to create a glowing visual effect.

        Args:
            event: The paint event containing region information.

        Drawing process:
            - Clears the background to black.
            - Enables antialiasing for smoother curves.
            - Uses additive composition mode for glow effect.
            - Draws multiple layered wave paths with decreasing amplitudes.
            - Applies gradient fills to each wave layer.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.black)
        painter.setCompositionMode(QPainter.CompositionMode_Plus)

        width = self.width()
        height = self.height()
        center = height / 2

        colors = [
            ("#3B82F6", "#1D4ED8"),  # Blue
            ("#EC4899", "#BE185D"),  # Pink
            ("#7F9CF5", "#6366F1"),  # Soft purple instead of white
            ("#FACC15", "#EAB308"),  # Yellow
            ("#10B981", "#059669"),  # Green
        ]

        for i, (c1, c2) in enumerate(colors):
            path = QPainterPath()
            layer_amp = self.current_amplitude * (1 - i * 0.2) * 0.7  # scale down to prevent overbright

            for x in range(width):
                t = (x - width / 2) / (width / 2)
                envelope = math.exp(-5 * t * t)  # tighter envelope

                y_offset = layer_amp * envelope * math.sin(3 * t + self.phase + i * 0.4)
                y = center + y_offset
                if x == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            for x in reversed(range(width)):
                t = (x - width / 2) / (width / 2)
                envelope = math.exp(-5 * t * t)
                y_offset = layer_amp * envelope * math.sin(3 * t + self.phase + i * 0.4)
                y = center - y_offset
                path.lineTo(x, y)

            path.closeSubpath()
            # Gradient
            gradient = QLinearGradient(0, 0, width, 0)
            gradient.setColorAt(0, QColor(c1))
            gradient.setColorAt(1, QColor(c2))
            painter.fillPath(path, QBrush(gradient))
