import io
import logging
import unittest

from autograder_platform.config.Logging import GeneralLogging


class TestGeneralLoggingFormatter(unittest.TestCase):
    LOGGER_NAME = "test_logging_formatter"

    def renderLogOutput(self, level: int, message: str) -> str:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(GeneralLogging())

        logger = logging.getLogger(f"{self.LOGGER_NAME}_{level}_{id(stream)}")
        logger.handlers = [handler]
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        logger.log(level, message)

        return stream.getvalue()

    def assertRenderedOutput(self, output: str, expected_level_name: str, message: str):
        self.assertIn(expected_level_name, output)
        self.assertIn(message, output)
        self.assertIn(self.LOGGER_NAME, output)
        self.assertRegex(output, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")

    def testDebugColorAppliedThroughLogger(self):
        output = self.renderLogOutput(logging.DEBUG, "debug message")
        self.assertRenderedOutput(output, "\033[0;37mDEBUG\033[0m", "debug message")

    def testInfoColorAppliedThroughLogger(self):
        output = self.renderLogOutput(logging.INFO, "info message")
        self.assertRenderedOutput(output, "\033[0;37mINFO\033[0m", "info message")

    def testWarningColorAppliedThroughLogger(self):
        output = self.renderLogOutput(logging.WARNING, "warning message")
        self.assertRenderedOutput(output, "\033[0;33mWARNING\033[0m", "warning message")

    def testErrorColorAppliedThroughLogger(self):
        output = self.renderLogOutput(logging.ERROR, "error message")
        self.assertRenderedOutput(output, "\033[0;31mERROR\033[0m", "error message")

    def testCriticalColorAppliedThroughLogger(self):
        output = self.renderLogOutput(logging.CRITICAL, "critical message")
        self.assertRenderedOutput(output, "\033[1;31mCRITICAL\033[0m", "critical message")

    def testUnknownLogLevelFallsBackToDebugColor(self):
        output = self.renderLogOutput(999, "custom level message")

        self.assertRenderedOutput(output, "\033[0;37mDEBUG\033[0m", "custom level message")
