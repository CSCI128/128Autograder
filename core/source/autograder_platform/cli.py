import abc
import argparse
import importlib
import unittest.loader
from argparse import ArgumentParser
from typing import List, Optional
from unittest import TestSuite

import autograder_platform
from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfigurationProvider, \
    AutograderConfiguration
from autograder_platform.config.Logging import AutograderLoggerProvider

KNOWN_REGISTRATIONS_NAMES = ["language_binds.IPython", "language_binds.Python"]

class AutograderCLITool(abc.ABC):
    PACKAGE_ERROR: str = "Required Package Error"
    SUBMISSION_ERROR: str = "Student Submission Error"
    ENVIRONMENT_ERROR: str = "Environment Error"

    def __init__(self, tool_name: str):
        self.config: Optional[AutograderConfiguration] = None
        self.arguments: Optional[argparse.Namespace] = None
        self.tests: Optional[TestSuite] = None

        self.parser: ArgumentParser = argparse.ArgumentParser(description=f"Autograder Platform - {tool_name}")

        # required CLI arguments
        self.parser.add_argument("--config-file", default="./config.toml",
                            help="Set the location of the config file")
        self.parser.add_argument("--additional-languages", action="extend", nargs="+", default=[],
                                 help="The import names for each additional language not provided in the base plugin set. The import should register via `Registration.Registrar` in `__init__.py`.")

        self.parser.add_argument("--version", action="store_true", default=False, help="Print out version and exit")

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

        self.discover_installed_language_binds(self.arguments.additional_languages)

        # load toml then override any options in toml with things that are passed to the runtime
        builder = AutograderConfigurationBuilder() \
            .fromTOML(file=self.arguments.config_file)

        self.set_config_arguments(builder)

        self.config = builder.build()

        AutograderLoggerProvider.configure(self.config.system_logger_name, self.config.system_log_level)
        AutograderConfigurationProvider.set(self.config)

    def discover_installed_language_binds(self, additional_languages: List[str]):  # pragma: no cover
        to_discover = KNOWN_REGISTRATIONS_NAMES
        to_discover.extend(additional_languages)

        for module in to_discover:
            try:
                mod = importlib.import_module(module)
            except ImportError:
                pass

    def discover_tests(self):  # pragma: no cover
        self.tests = unittest.loader.defaultTestLoader.discover(self.config.config.test_directory)
        AutograderLoggerProvider.get().debug(f"discovered {self.tests.countTestCases()} test cases")

