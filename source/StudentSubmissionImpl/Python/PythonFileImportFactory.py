import os

from importlib.machinery import ModuleSpec
from types import ModuleType, CodeType
from typing import Dict, Optional, List
from importlib.abc import Loader
from importlib.util import spec_from_file_location

from StudentSubmissionImpl.Python.AbstractPythonImportFactory import AbstractModuleFinder

class ModuleFinder(AbstractModuleFinder):
    def __init__(self) -> None:
        self.knownModules: Dict[str, str] = {}
        self.modulesToReload: List[str] = []

    def addModule(self, fullname, path):
        for mod in fullname.split('.'):
            self.knownModules[mod] = path
            self.modulesToReload.append(mod)

    def find_spec(self, fullname, path, target=None):
        if fullname not in self.knownModules:
            return None
        
        return spec_from_file_location(fullname, self.knownModules[fullname], loader=ModuleLoader(self.knownModules[fullname]))
    
    def getModulesToReload(self) -> List[str]:
        return self.modulesToReload


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
    
class PythonFileImportFactory:
    moduleFinder: ModuleFinder = ModuleFinder()

    @classmethod
    def registerFile(cls, pathToFile: str, importName: str):
        if cls.moduleFinder == None:
            raise AttributeError("Invalid State: Module finder is none")
        if "addModule" in vars(cls.moduleFinder):
            raise AttributeError("Invalid ModuleFinder for registration")

        cls.moduleFinder.addModule(importName, pathToFile)
    
    @classmethod
    def buildImport(cls):
        return cls.moduleFinder

