import dataclasses
from typing import List, Dict, Optional, TypeVar
from importlib import import_module

from language_binds.Python.AbstractPythonImportFactory import AbstractModuleFinder
from language_binds.Python.Config import PythonConfiguration
from language_binds.Python.PythonModuleMockImportFactory import MockedModuleFinder
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock
from autograder_platform.config.Config import AutograderConfiguration


class PythonResults():
    class Mocks():
        def __init__(self, mocks: Optional[Dict[str, SingleFunctionMock]]):
            self.mocks = mocks

        def __getitem__(self, mockName: str) -> SingleFunctionMock:
            if self.mocks is None:
                raise AssertionError("No mocks were returned by student submission!")
            if mockName not in self.mocks:
                raise AssertionError(f"Mock '{mockName}' was not returned by the students submission")

            return self.mocks[mockName]

    def __init__(self, mocks=None):
        self.mocks = mocks

    @property
    def mocks(self) -> Mocks:
        return self._mocks

    @mocks.setter
    def mocks(self, value: Optional[Dict[str, SingleFunctionMock]]):
        self._mocks = PythonResults.Mocks(value)


@dataclasses.dataclass
class PythonEnvironment():
    buffer_size: int = 2**20
    """Buffer size set from the config file. This shouldn't be set directly"""
    import_loader: List[AbstractModuleFinder] = dataclasses.field(default_factory=list)
    """The import loader. This shouldn't be set directly"""
    mocks: Dict[str, Optional[SingleFunctionMock]] = dataclasses.field(default_factory=dict)
    """What mocks have been defined for this run of the student's submission"""


def configMapper(env: PythonEnvironment, config: AutograderConfiguration[PythonConfiguration]):
    if config.language_config is None:
        raise AttributeError("INVALID STATE: Implementation environment mapping FAILED! Python config is NONE when should be defined!")

    env.buffer_size = config.language_config.buffer_size


Builder = TypeVar("Builder", bound="PythonEnvironmentBuilder")


class PythonEnvironmentBuilder():
    def __init__(self) -> None:
        self.environment: PythonEnvironment = PythonEnvironment()
        self.moduleMocks: Dict[str, Dict[str, SingleFunctionMock]] = {}

    def addModuleMock(self: Builder, moduleName: str, mockedMethods: Dict[str, SingleFunctionMock]) -> Builder:
        """
        Description
        ---
        This function sets up a mock for a complete module. 
        All mocks must be the same 'level' meaning we cant mock a.b.fun and a.fun. We have to choose. 

        We also  cant mock both a.b and a in the same submission currently without mocking the entirety of a.

        :param moduleName: The name of the module that will be mocked.
        :param mockedMethods: the map of the methods to mock in the module
        """
        if moduleName in self.moduleMocks:
            for mockName, mockObject in mockedMethods.items():
                self.moduleMocks[moduleName][mockName] = mockObject

            return self

        self.moduleMocks[moduleName] = mockedMethods

        return self

    def addImportHandler(self: Builder, importHandler: AbstractModuleFinder) -> Builder:
        """
        Description
        ---
        This adds an import handler to the environment

        :param importHandler: the meta path finder
        """
        self.environment.import_loader.append(importHandler)

        return self

    def addMock(self: Builder, mockName: str, mockObject: SingleFunctionMock) -> Builder:
        """
        This needs to be updated once we decide how to do mocks
        """
        self.environment.mocks[mockName] = mockObject

        return self

    def _processAndValidateModuleMocks(self):
        for moduleName in self.moduleMocks.keys():
            try:
                module = import_module(moduleName)
            except ImportError:
                raise AttributeError(f"Failed to import {moduleName}!")

            for methodName, mock in self.moduleMocks[moduleName].items():

                if not isinstance(mock, SingleFunctionMock):
                    raise AttributeError(f"Invalid mock for {methodName}")

                self.environment.mocks[methodName] = None

            self.environment.import_loader.append(MockedModuleFinder(moduleName, module, self.moduleMocks[moduleName]))

    def build(self) -> PythonEnvironment:
        self._processAndValidateModuleMocks()

        return self.environment
