import importlib
import os
from typing import Dict, Generic, List, Optional as OptionalType, TypeVar, Any
from dataclasses import dataclass

from schema import And, Optional, Or, Regex, Schema, SchemaError

from autograder_platform.config.common import BaseSchema, MissingParsingLibrary, InvalidConfigException


@dataclass(frozen=True)
class BuildConfiguration:
    """
    Build Configuration
    ===================
    
    This class defines the build options when building new or existing autograders
    """
    use_starter_code: bool
    """Whether the starter code should be pulled into the student autograder"""
    use_data_files: bool
    """Whether datafiles should be pulled into the autograder"""
    allow_private: bool
    """Whether the private tests and datafiles should be kept private"""
    build_student: bool
    """If we should build the student autograder"""
    build_gradescope: bool
    """If we should build the gradescope autograder"""
    build_prairie_learn: bool
    """If we should build the PrairieLearn autograder"""
    data_files_source: str
    """The folder that contains the datafiles for use with the autograder"""
    starter_code_source: str
    """The path for the starter code that should be provided to the student"""
    student_work_folder: str
    """The folder that should be created for the student"""
    private_tests_regex: str
    """The pattern that should be used to identify private tests"""
    public_tests_regex: str
    """The pattern that should be used to identify public tests"""


@dataclass(frozen=True)
class PythonConfiguration:
    """
    Python Configuration
    ====================

    This class defines extra parameters for when the autograder is running in Python
    """
    extra_packages: List[Dict[str, str]]
    """
    The extra packages that should be added to the autograder on build.
    Must be stored in 'package_name': 'version'. Similar to requirements.txt 
    """
    buffer_size: int
    """
    The size of the output buffer when the autograder runs
    """


@dataclass(frozen=True)
class CConfiguration:
    """
    C/C++/C-Like Configuration
    ==========================

    This defines the extra parameters for when the autograder is running for c like languages
    """

    use_makefile: bool
    """
    If a makefile should be used for building
    """
    clean_target: str
    """
    The target that should be used to clean. Invoked as `make {clean_target}`
    """
    submission_name: str
    """
    The file name that should be executed
    """


@dataclass(frozen=True)
class BasicConfiguration:
    """
    Basic Configuration
    ===================

    This class defines the basic autograder configuration
    """
    impl_to_use: str
    """The StudentSubmission Implementation to use"""
    student_submission_directory: str
    """The folder that the student submission is in"""
    autograder_version: str
    """The autograder version tag. Autograder will be kept at this version"""
    test_directory: str
    """The directory that the tests are in"""
    enforce_submission_limit: bool
    """Whether or not the submission limit should be enforced"""
    submission_limit: int
    """The max number of submissions that a student has"""
    take_highest: bool
    """If we should take the highest of all the valid scores"""
    allow_extra_credit: bool
    """If scores greater than ``perfect_score`` should be respected"""
    perfect_score: int
    """The max score with out extra credit that a student can get"""
    max_score: int
    """
    The max score that students can get with extra credit. 
    Points greater than this will not be honored.
    """
    python: OptionalType[PythonConfiguration] = None
    """Extra python spefic configuration. See :ref:`PythonConfiguration` for options"""
    c: OptionalType[CConfiguration] = None
    """Extra C/C-like spefic configuration. See :ref:`CConfiguration` for options"""


@dataclass(frozen=True)
class AutograderConfiguration:
    """
    Autograder Configuration
    ========================

    The root object for the autograder configuration.
    Comprised of sub objects. 
    See :ref:`BasicConfiguration` and :ref:`BuildConfiguration` for more information.
    """
    assignment_name: str
    """The assignment name. IE: `ConstructionSite`"""
    semester: str
    """The semester that this assignment is being offered. IE: F99 -> Fall 1999"""
    autograder_root: str
    """The autograder's root directory where the config.toml file is located"""
    config: BasicConfiguration
    """The basic settings for the autograder. See :ref:`BasicConfiguration` for options."""
    build: BuildConfiguration
    """The build configuration for the autograder. See :ref:`BuildConfiguration` for options."""


class AutograderConfigurationSchema(BaseSchema[AutograderConfiguration]):
    """
    Autograder Configuration Schema
    ===============================

    This class defines the format agnostic schema required for the autograder.
    This class is able to validate and build a config. 
    Configs are expected to be provided as a dictionary; hence that agnostic nature of the schema.

    This class builds to: ref:`AutograderConfiguration` for easy typing.
    """
    IMPL_SOURCE = "StudentSubmissionImpl"

    @staticmethod
    def validateImplSource(implName: str) -> bool:
        try:
            importlib.import_module(f"autograder_platform.{AutograderConfigurationSchema.IMPL_SOURCE}.{implName}")
        except ImportError:
            return False
        return True

    def __init__(self):
        self.currentSchema: Schema = Schema(
            {
                "assignment_name": And(str, Regex(r"^(\w+-?)+$")),
                "semester": And(str, Regex(r"^(F|S|SUM)\d{2}$")),
                Optional("autograder_root", default="."): And(os.path.exists, os.path.isdir, lambda path: "config.toml" in os.listdir(path)),
                "config": {
                    "impl_to_use": And(str, AutograderConfigurationSchema.validateImplSource),
                    Optional("student_submission_directory", default="."): And(str, os.path.exists, os.path.isdir),
                    "autograder_version": And(str, Regex(r"\d+\.\d+\.\d+")),
                    "test_directory": And(str, os.path.exists),
                    "enforce_submission_limit": bool,
                    Optional("submission_limit", default=1000): And(int, lambda x: x >= 1),
                    Optional("take_highest", default=True): bool,
                    Optional("allow_extra_credit", default=False): bool,
                    "perfect_score": And(int, lambda x: x >= 1),
                    "max_score": And(int, lambda x: x >= 1),
                    Optional("python", default=None): Or({
                        Optional("extra_packages", default=lambda: []): [{
                            "name": str,
                            "version": str,
                        }],
                        Optional("buffer_size", default=2 ** 20): And(int, lambda x: x >= 2 ** 20)
                    }, None),
                    Optional("c", default=None): Or({
                        "use_makefile": bool,
                        "clean_target": str,
                        "submission_name": And(str, lambda x: len(x) >= 1)
                    }, None),
                },
                "build": {
                    "use_starter_code": bool,
                    "use_data_files": bool,
                    Optional("allow_private", default=True): bool,
                    Optional("data_files_source", default=None): str,
                    Optional("starter_code_source", default=None): str,
                    "build_student": bool,
                    "build_gradescope": bool,
                    Optional("build_prairie_learn", default=False): bool,
                    Optional("student_work_folder", default="student_work"): str,
                    Optional("private_tests_regex", default=r"^test_private_?\w*\.py$"): str,
                    Optional("public_tests_regex", default=r"^test_?\w*\.py$"): str,
                }
            },
            ignore_extra_keys=False, name="ConfigSchema"
        )

    def validate(self, data: Dict) -> Dict:
        """
        Description
        ---
        This method validates the provided data against the schema.

        If it is valid, then it will be returned. Otherwise, an ``InvalidConfigException`` will be raised.

        :param data: The data to validate
        :return: The data if it is able to be validated
        """
        validated = {}
        try:
            validated = self.currentSchema.validate(data)
        except SchemaError as schemaError:
            raise InvalidConfigException(str(schemaError))

        impl_to_use = validated["config"]["impl_to_use"].lower()

        if impl_to_use not in validated["config"] or validated["config"][impl_to_use] is None:
            raise InvalidConfigException(f"Missing Implementation Config for config.{impl_to_use}")

        if validated["build"]["use_starter_code"] and validated["build"]["starter_code_source"] is None:
            raise InvalidConfigException("Missing starter code file location")

        if validated["build"]["use_data_files"] and validated["build"]["data_files_source"] is None:
            raise InvalidConfigException("Missing directory for data files!")

        return validated

    def build(self, data: Dict) -> AutograderConfiguration:
        """
        Description
        ---
        This method builds the provided data into the known config format.

        In this case, it builds into the ``AutograderConfiguration`` format.
        Data should be validated before calling this method as it uses dictionary expandsion to populate the config objects.

        Doing this allows us to have a strongly typed config format to be used later in the autograder.
        """
        if data["config"]["python"] is not None:
            data["config"]["python"] = PythonConfiguration(**data["config"]["python"])

        if data["config"]["c"] is not None:
            data["config"]["c"] = CConfiguration(**data["config"]["c"])

        data["config"] = BasicConfiguration(**data["config"])
        data["build"] = BuildConfiguration(**data["build"])

        return AutograderConfiguration(**data)


# Using generics as PyRight and mypy are able to infer what `T` should be from the Schema
#  as it inherits from BaseSchema
T = TypeVar("T")
Builder = TypeVar("Builder", bound="AutograderConfigurationBuilder[Any]")


class AutograderConfigurationBuilder(Generic[T]):
    """
    AutograderConfigurationBuilder
    ==============================

    This class currently doesn't do much.
    It allows a schema (that inherits from :ref:`BaseSchema`) to passed in to use to validate and build.
    However, it assumes the ``AutograderConfigurationSchema`` will be used.

    This allows loading from currently only toml files, but is very easy to expand to different file formats if needed.

    ``.build`` should always be the last thing called.

    In the future, configuration will be allowed with this builder, but I would need to see the use case.
    """
    DEFAULT_CONFIG_FILE = "./config.toml"

    def __init__(self, configSchema: BaseSchema[T] = AutograderConfigurationSchema()):
        self.schema: BaseSchema[T] = configSchema
        self.data: Dict = {}

    def fromTOML(self: Builder, file=DEFAULT_CONFIG_FILE, merge=True) -> Builder:
        """
        Attempt to load the autograder config from the TOML config file.
        This file is assumed to be located in the same directory as the actual test cases
        """
        try:
            from tomli import load
        except ModuleNotFoundError:
            raise MissingParsingLibrary("tomlkit", "AutograderConfigurationBuilder.fromTOML")

        with open(file, 'rb') as rb:
            self.data = load(rb)

        return self

    # Really easy to add support for other file formats.
    # YAML or JSON would work as well

    @staticmethod
    def _createKeyIfDoesntExist(source: Dict[str, Any], key: str):
        if key in source:
            return

        source[key] = {}

    def setStudentSubmissionDirectory(self: Builder, studentSubmissionDirectory: OptionalType[str]) -> Builder:
        if studentSubmissionDirectory is None:
            return self

        self._createKeyIfDoesntExist(self.data, "config")

        self.data["config"]["student_submission_directory"] = studentSubmissionDirectory

        return self

    def setTestDirectory(self: Builder, testDirectory: str) -> Builder:
        self._createKeyIfDoesntExist(self.data, "config")

        self.data["config"]["test_directory"] = testDirectory

        return self

    def setAutograderRoot(self: Builder, autograderDirectory: str) -> Builder:
        self.data["autograder_root"] = autograderDirectory

        return self

    def build(self) -> T:
        self.data = self.schema.validate(self.data)
        return self.schema.build(self.data)


class AutograderConfigurationProvider:
    """
    AutograderConfigurationProvider
    ===============================

    This class allows access to the same config across the entire program.
    This is using a similar pattern to singletons, however, it's a bit better as it's a separate provider.
    """
    config: OptionalType[AutograderConfiguration] = None

    @classmethod
    def get(cls) -> AutograderConfiguration:
        if cls.config is None:
            raise AttributeError("Configuration has not been set!")

        return cls.config

    @classmethod
    def set(cls, config: AutograderConfiguration):
        if cls.config is not None:
            raise AttributeError("Configuration has already been set!")

        cls.config = config

    @classmethod
    def reset(cls):
        cls.config = None
