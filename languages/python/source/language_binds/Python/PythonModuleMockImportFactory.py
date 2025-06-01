from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Optional, List, Dict

from autograder_binds.Python.AbstractPythonImportFactory import AbstractModuleFinder
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock


class MockedModuleFinder(AbstractModuleFinder, Loader):
    def __init__(self, name: str, module: ModuleType, mocks: Dict[str, SingleFunctionMock]) -> None:
        super().__init__()
        self.name: str = name
        self.module: ModuleType = module
        self.mocks: Dict[str, SingleFunctionMock] = mocks
        self.modulesToReload: List[str] = [self.name]

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        return self.module

    def exec_module(self, module):
        for methodName, mock in self.mocks.items():
            splitName = methodName.split('.')

            if mock.spy:
                mock.setSpyFunction(getattr(module, splitName[-1]))

            setattr(module, splitName[-1], mock)

    def find_spec(self, fullname, path, target=None) -> Optional[ModuleSpec]:
        if self.name != fullname:
            return None

        return ModuleSpec(self.name, self)

    def getModulesToReload(self) -> List[str]:
        return self.modulesToReload

