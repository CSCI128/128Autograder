import logging
import sys
from typing import Optional, Literal, TextIO

class GeneralFormatter(logging.Formatter):
    FORMAT = "\033[0;37m[%(asctime)s] [%(name)-12s]\033[0m [%(levelname)s] - %(message)s"
    MAPPING = {
        logging.DEBUG: "\033[0;37mDEBUG\033[0m",
        logging.INFO: "\033[0;37mINFO\033[0m",
        logging.WARNING: "\033[0;33mWARNING\033[0m",
        logging.ERROR: "\033[0;31mERROR\033[0m",
        logging.CRITICAL: "\033[1;31mCRITICAL\033[0m",
    }
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(self.FORMAT, datefmt=self.TIME_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = self.MAPPING.get(record.levelno, self.MAPPING[logging.DEBUG])
        return super().format(record)

class AutograderLoggerProvider:
    _logger: Optional[logging.Logger] = None

    @classmethod
    def configure(cls, name: str, log_level: Literal[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL], file: TextIO = sys.stdout) -> None:
        if cls._logger is not None:
            return

        handler = logging.StreamHandler(file)
        handler.setFormatter(GeneralFormatter())
        cls._logger = logging.getLogger(name)
        cls._logger.setLevel(log_level)
        cls._logger.handlers = [handler]
        cls._logger.propagate = False

    @classmethod
    def get(cls) -> logging.Logger:
        if cls._logger is not None:
            return cls._logger

        raise ValueError("Logger has not been initialized")

    @classmethod
    def reset(cls):
        cls._logger = None


