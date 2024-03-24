from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Optional


class ModuleFinder(MetaPathFinder, Loader):
    def __init__(self, name, module: ModuleType) -> None:
        self.name = name
        self.module = module

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        return self.module

    def find_spec(self, fullname, path, target=None) -> Optional[ModuleSpec]:
        if self.name != fullname:
            return None

        return ModuleSpec(self.name, self)
