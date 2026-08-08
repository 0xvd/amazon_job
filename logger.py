import sys
from datetime import datetime


class Colors:
    RESET = "\033[0m"
    WHITE = "\033[37m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"


class Logger:
    @staticmethod
    def write(message, prefix="LOG", end="\n", color=Colors.WHITE):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log = f"[{timestamp}][{prefix}] {message}"
        sys.stdout.write(f"{color}{log}{Colors.RESET}{end}")
        sys.stdout.flush()

    @classmethod
    def error(cls, message, end="\n"):
        cls.write(message, "ERROR", end, Colors.RED)

    @classmethod
    def info(cls, message, end="\n"):
        cls.write(message, "INFO", end, Colors.BLUE)

    @classmethod
    def warn(cls, message, end="\n"):
        cls.write(message, "WARN", end, Colors.YELLOW)

    @classmethod
    def debug(cls, message, end="\n"):
        cls.write(message, "DEBUG", end, Colors.WHITE)
