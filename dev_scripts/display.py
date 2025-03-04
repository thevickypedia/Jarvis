from typing import Any


class Format:
    """Initiates Format object to define variables that print the message in a certain format.

    >>> Format

    """

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ITALIC = "\x1B[3m"


class Colors:
    """Initiates Colors object to define variables that print the message in a certain color.

    >>> Colors

    """

    VIOLET = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    LIGHT_GREEN = "\033[32m"
    LIGHT_YELLOW = "\033[2;33m"
    LIGHT_RED = "\033[31m"


class Echo:
    """Initiates Echo objects to set text to certain format and color based on the level of the message.

    >>> Echo

    """

    def __init__(self):
        self._colors = Colors
        self._format = Format

    def debug(self, msg: Any) -> None:
        """Method for debug statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.LIGHT_GREEN}{msg}{self._colors.END}")

    def info(self, msg: Any) -> None:
        """Method for info statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.GREEN}{msg}{self._colors.END}")

    def warning(self, msg: Any) -> None:
        """Method for warning statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.YELLOW}{msg}{self._colors.END}")

    def error(self, msg: Any) -> None:
        """Method for error statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.RED}{msg}{self._colors.END}")

    def critical(self, msg: Any) -> None:
        """Method for critical statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.RED}{self._format.BOLD}{msg}{self._colors.END}")

    def fatal(self, msg: Any) -> None:
        """Method for fatal statement.

        Args:
            msg: Message to be printed.
        """
        print(f"{self._colors.RED}{self._format.BOLD}{msg}{self._colors.END}")


echo = Echo()
