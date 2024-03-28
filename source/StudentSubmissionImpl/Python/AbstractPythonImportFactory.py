from importlib.abc import MetaPathFinder
from typing import List


class AbstractModuleFinder(MetaPathFinder):
    def __init__(self) -> None:
        super().__init__()
        self.modulesToReload: List[str] = []

    def getModulesToReload(self) -> List[str]:
        return self.modulesToReload
