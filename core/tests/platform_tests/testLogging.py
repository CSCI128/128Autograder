import io
import logging
import re
import unittest

from autograder_platform.config.Logging import AutograderLoggerProvider


class TestGeneralFormatter(unittest.TestCase):
    LOGGER_NAME = "test_logging_provider"

    def setUp(self) -> None:
        AutograderLoggerProvider.reset()
        self.stream = io.StringIO()
        AutograderLoggerProvider.configure(self.LOGGER_NAME, logging.DEBUG, self.stream)
        self.logger = AutograderLoggerProvider.get()

    def renderLogOutput(self, level: int, message: str) -> str:
        self.logger.log(level, message)
        return self.stream.getvalue()

    def assertRenderedOutput(self, output: str, expected_level_name: str, message: str):
        self.assertIn(expected_level_name, output)
        self.assertIn(message, output)
        self.assertIn(self.LOGGER_NAME, output)
        message_pattern = (
            r"^\033\[0;37m"  # color for general status
            r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]"  # date
            r" \[[^\]]+\]"  # name
            r"\033\[0m "  # reset color
            rf"\[{re.escape(expected_level_name)}\]"
            rf" - {re.escape(message)}\n$"
        )
        self.assertRegex(output, message_pattern)

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
