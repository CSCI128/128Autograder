from typing import Dict, Generic, List, Optional as OptionalType, TypeVar
from dataclasses import dataclass
import requests

from schema import And, Optional, Regex, Schema, SchemaError

from .common import BaseSchema, MissingParsingLibrary, InvalidConfigException


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

@dataclass(frozen=True)
class BasicConfiguration:
    """
    Basic Configuration
    ===================

    This class defines the basic autograder configuration
    """
    autograder_version: str
    """The autograder version tag. Autograder will be kept at this version"""
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

    This class builds to :ref:`AutograderConfiguration` for easy typing.
    """
    TAGS_ENDPOINT = "https://api.github.com/repos/CSCI128/128Autograder/tags"

    @staticmethod
    def getAvailableTags() -> List[str]:
        """
        Description
        ---
        This method gets the currently available version tags from GitHub.
        This ensures that any version of the autorgader is using a spefic version of the autograder.
        :return: a list of all the valid tags from GitHub
        """
        headers = {"X-GitHub-Api-Version": "2022-11-28"}

        tags = requests.get(url=AutograderConfigurationSchema.TAGS_ENDPOINT, headers=headers).json()

        return [el["name"] for el in tags]

    def __init__(self):
        self.TAGS = self.getAvailableTags()

        self.currentSchema: Schema = Schema(
            {
                "assignment_name": And(str, Regex(r"^(\w+-?)+$")),
                "semester": And(str, Regex(r"^(F|S|SUM)\d{2}$")),
                "config": {
                    "autograder_version": And(str, lambda x: x in self.TAGS),
                    "enforce_submission_limit": bool,
                    Optional("submission_limit", default=1000): And(int, lambda x: x >= 1),
                    Optional("take_highest", default=True): bool,
                    Optional("allow_extra_credit", default=False): bool,
                    "perfect_score": And(int, lambda x: x >= 1),
                    "max_score": And(int, lambda x: x >= 1),
                    Optional("python", default=None): {
                        Optional("extra_packages", default=lambda: []): [{
                            "name": str,
                            "version": str,
                        }],
                    },
                },
                "build": {
                    "use_starter_code": bool,
                    "use_data_files": bool,
                    Optional("allow_private", default=True): bool,

                }
            },
            ignore_extra_keys=False, name="ConfigSchema"
        )

    def validate(self, data: Dict) -> Dict:
        """
        Description
        ---
        This method validates the provided data agaist the schema.

        If it is valid, then it will be returned. Otherwise, an ``InvalidConfigException`` will be raised.

        :param data: The data to validate
        :return: The data if it is able to be validated
        """
        try:
            return self.currentSchema.validate(data)
        except SchemaError as schemaError:
            raise InvalidConfigException(str(schemaError))


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


        data["config"] = BasicConfiguration(**data["config"])
        data["build"] = BuildConfiguration(**data["build"])

        return AutograderConfiguration(**data)

# Using generics as PyRight and mypy are able to infer what `T` should be from the Schema
#  as it inherits from BaseSchema
T = TypeVar("T")
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


    def fromTOML(self, file=DEFAULT_CONFIG_FILE):
        try:
            from tomli import load
        except ModuleNotFoundError:
            raise MissingParsingLibrary("tomlkit", "AutograderConfigurationBuilder.fromTOML")

        with open(file, 'rb') as rb:
            self.data = load(rb)
            print(self.data)

        return self

    # Really easy to add support for other file formats. 
    # YAML or JSON would work as well

    # For now, not allowing any configuration in code. Thankfully thats really easy to add in the future
    
    def build(self) -> T:
        self.data = self.schema.validate(self.data)
        return self.schema.build(self.data)

    

