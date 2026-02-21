import sys

if sys.platform != "win32":
    # noinspection PyProtectedMember
    from multiprocessing.connection import Connection
else:
    # noinspection PyProtectedMember
    from multiprocessing.connection import PipeConnection as Connection

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from jarvis.modules.logger import logger
from jarvis.modules.microphone import widget


def start(connection: Connection) -> None:
    """Run the UI event loop process for the WavePattern visualizer.

    See Also:
        - | Creates a QApplication instance, initializes the WavePattern window,
          | and listens for control commands from a multiprocessing connection.
        - This function is intended to run in a dedicated process.

    Args:
        connection: A multiprocessing connection used to receive control commands from another process.

    Supported commands:
        - "start": Begin wave animation.
        - "stop": Begin wave settling animation.

    Behavior:
        - Starts a Qt application event loop.
        - Displays the WavePattern window.
        - Uses a QTimer to periodically poll the pipe connection.
        - Processes all pending commands without blocking the UI thread.
        - Stops polling and logs an error if the controller disconnects.

    Raises:
        SystemExit:
        Raised when the Qt application event loop exits.
    """
    app = QApplication(sys.argv)
    window = widget.WavePattern()
    window.show()

    def check_pipe() -> None:
        """Poll the multiprocessing connection for incoming control commands.

        Checks whether data is available on the pipe using non-blocking
        polling. If commands are present, reads and processes all pending
        messages in sequence.

        Recognized commands:
            - "start": Triggers the WavePattern to begin animating.
            - "stop": Triggers the WavePattern to begin settling.

        If the connection is closed unexpectedly, logs an error and stops
        the polling timer to prevent repeated exceptions.

        Raises:
            EOFError:
            Caught internally if the controller process disconnects.
        """
        try:
            while connection.poll():  # Only read if data exists
                cmd = connection.recv()
                if cmd == "start":
                    window.start()
                elif cmd == "stop":
                    window.stop()
        except EOFError:
            logger.error("Controller disconnected")
            timer.stop()

    timer = QTimer()
    timer.timeout.connect(check_pipe)
    timer.start(50)

    sys.exit(app.exec())
