from enum import Enum


class LoggerType(Enum):
    """Enum to store all possible message logging types."""

    NONE = ("NONE",)
    INFO = ("INFO",)
    WARNING = ("WARNING",)
    ERROR = "ERROR"


class Logger:
    @staticmethod
    def message(logger_type: LoggerType, source: str, message: str) -> None:
        """
        Prints a logger message.

        Args:
            logger_type (LoggerType):
                Enum reference of the logging type.
            source (str):
                File path from which the logging message was called.
            message (str):
                Logging message.
        """
        print(f"[{logger_type.value}] ({source}) - {message}")
