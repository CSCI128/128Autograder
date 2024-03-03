import os

from importlib.machinery import ModuleSpec
from types import ModuleType, CodeType
from typing import Dict, Optional
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location



class ModuleFinder(MetaPathFinder):
    def __init__(self) -> None:
        self.knownModules: Dict[str, str] = {}

    def addModule(self, fullname, path):
        self.knownModules[fullname] = path

    def find_spec(self, fullname, path, target=None):
        if fullname not in self.knownModules:
            return None
        
        return spec_from_file_location(fullname, self.knownModules[fullname], loader=ModuleLoader(self.knownModules[fullname]))


class ModuleLoader(Loader):
    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec: ModuleSpec) -> Optional[ModuleType]:
        return None
    
    def exec_module(self, module: ModuleType) -> None:
        if not os.path.exists(self.filename):
            raise ImportError(f"Should be able to open {self.filename}, but was unable to locate file!")
        with open(self.filename) as r:
            data = r.read()
        
        compiledImport: CodeType = compile(data, self.filename, "exec")
        exec(compiledImport, vars(module))
    
