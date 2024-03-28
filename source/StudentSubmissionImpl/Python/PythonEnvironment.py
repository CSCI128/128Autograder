import dataclasses
from typing import List, Dict, Optional, TypeVar
from importlib import import_module

from StudentSubmissionImpl.Python.AbstractPythonImportFactory import AbstractModuleFinder
from StudentSubmissionImpl.Python.PythonModuleMockImportFactory import ModuleFinder
from TestingFramework.SingleFunctionMock import SingleFunctionMock

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

    def __init__(self, mocks = None):
        self.mocks = mocks

    @property
    def mocks(self) -> Mocks:
        return self._mocks

    @mocks.setter
    def mocks(self, value: Optional[Dict[str, SingleFunctionMock]]):
        self._mocks = PythonResults.Mocks(value)

@dataclasses.dataclass
class PythonEnvironment():
    import_loader: List[AbstractModuleFinder] = dataclasses.field(default_factory=list)
    """The import loader. This shouldn't be set directly"""
    mocks: Dict[str, Optional[SingleFunctionMock]] = dataclasses.field(default_factory=dict)
    """What mocks have been defined for this run of the student's submission"""

Builder = TypeVar("Builder", bound="PythonEnvironmentBuilder")

class PythonEnvironmentBuilder():
    def __init__(self) -> None:
        self.environment: PythonEnvironment = PythonEnvironment()
        self.moduleMocks: Dict[str, Dict[str, object]] = {}
        
    def addModuleMock(self: Builder, moduleName: str, mockedMethods: Dict[str, object]) -> Builder:
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
                splitName = methodName.split('.')

                if not isinstance(mock, SingleFunctionMock):
                    raise AttributeError(f"Invalid mock for {methodName}")

                if mock.spy:
                    mock.setSpyFunction(getattr(module, splitName[-1]))

                self.environment.mocks[methodName] = None
                setattr(module, splitName[-1], mock)

            self.environment.import_loader.append(ModuleFinder(moduleName, module))

    def build(self) -> PythonEnvironment:
        self._processAndValidateModuleMocks()

        return self.environment

