import abc
import argparse
import unittest.loader
from argparse import ArgumentParser
from typing import List, Callable, Dict, Optional
from unittest import TestSuite

import autograder_platform
from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfigurationProvider, \
    AutograderConfiguration

class AutograderCLITool(abc.ABC):

    PACKAGE_ERROR: str = "Required Package Error"
    SUBMISSION_ERROR: str = "Student Submission Error"
    ENVIRONMENT_ERROR: str = "Environment Error"
    RED_COLOR: str = u"\u001b[31m"
    YELLOW_COLOR: str = u"\u001b[33m"
    BLUE_COLOR: str = u"\u001b[34m"
    RESET_COLOR: str = u"\u001b[0m"

    @classmethod
    def print_error_message(cls, errorType: str, errorText: str) -> None:
        """
        This function prints out a validation error message as they occur.
        The error type is colored red when it is printed
        the format used is `[<error_type>] <error_text>`
        :param errorType: The error type
        :param errorText: the text for the error
        :return:
        """
        print(f"[{cls.RED_COLOR}{errorType}{cls.RESET_COLOR}]: {errorText}")


    @classmethod
    def print_warning_message(cls, warningType: str, warningText: str) -> None:
        print(f"[{cls.YELLOW_COLOR}{warningType}{cls.RESET_COLOR}]: {warningText}")

    @classmethod
    def print_info_message(cls, text: str) -> None:
        print(f"[{cls.BLUE_COLOR}INFORMATION{cls.RESET_COLOR}]: {text}")

    def __init__(self, tool_name: str):
        self.config: Optional[AutograderConfiguration] = None
        self.arguments: Optional[argparse.Namespace] = None
        self.tests: Optional[TestSuite] = None

        self.parser: ArgumentParser = argparse.ArgumentParser(description=f"Autograder Platform - {tool_name}")

        # required CLI arguments
        self.parser.add_argument("--config-file", default="./config.toml",
                            help="Set the location of the config file")

    @staticmethod
    def get_version() -> str:
        return autograder_platform.__version__

    @abc.abstractmethod
    def configure_options(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def set_config_arguments(self, configBuilder: AutograderConfigurationBuilder[AutograderConfiguration]):
        raise NotImplementedError()

    @abc.abstractmethod
    def run(self) -> bool:
        raise NotImplementedError()

    def load_config(self):  # pragma: no cover
        self.arguments = self.parser.parse_args()

        # load toml then override any options in toml with things that are passed to the runtime
        builder = AutograderConfigurationBuilder() \
            .fromTOML(file=self.arguments.config_file)

        self.set_config_arguments(builder)

        self.config = builder.build()

        AutograderConfigurationProvider.set(self.config)

    def discover_tests(self):  # pragma: no cover
        self.tests = unittest.loader.defaultTestLoader.discover(self.config.config.test_directory)

