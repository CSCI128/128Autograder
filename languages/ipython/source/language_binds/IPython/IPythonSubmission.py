import ast
import dataclasses
import os
import re
import subprocess
import sys
from types import CodeType
from typing import TypeVar, List, Dict, Iterable, Optional

import nbconvert
from nbformat import read, NotebookNode

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from language_binds.IPython.CellMetadataParser import CellMetadata, parseCellMetadata
from language_binds.IPython.IPythonTransformers import MagicCommandTransformer, \
    MatplotLibFigTransformer
from language_binds.IPython.IPythonValidators import IPythonFileValidator, \
    TestableCellValidator, TestableCellDependencyValidator

from language_binds.Python.PythonValidators import PackageValidator

Builder = TypeVar("Builder", bound="IPythonSubmission")


def filterSearchResults(path: str) -> bool:
    if path[0] == ".":
        return False
    if "__pycache__" in path:
        return False
    if " " in path:
        return False

    return True


@dataclasses.dataclass()
class Cell:
    metadata: CellMetadata
    code: str

class IPythonSubmission(AbstractStudentSubmission[CodeType]):
    IPYTHON_FILE_REGEX: re.Pattern = re.compile(r"^(\w|-)+\.ipynb")

    def __init__(self):
        super().__init__()
        self._cells: Dict[str, Cell] = {}
        self._discoveredFiles: List[str] = []
        self._htmlTransformationEnabled: bool = False
        self._notebookHtml: Optional[str] = None
        self._extraPackages: Dict[str, str] = {}

        self._builtCells: Dict[str, CodeType] = {}

        self._activeCell: Optional[str] = None

        self.addValidator(PackageValidator())
        self.addValidator(IPythonFileValidator())
        self.addValidator(TestableCellValidator())
        self.addValidator(TestableCellDependencyValidator())
        self.addTransformer(MagicCommandTransformer())
        self.addTransformer(MatplotLibFigTransformer())

    def _discoverSubmittedFiles(self, directoryToSearch: str):
        pathsToVisit: Iterable[str] = filter(filterSearchResults, os.listdir(directoryToSearch))

        if not pathsToVisit:
            return

        for path in pathsToVisit:
            if os.path.isdir(os.path.join(directoryToSearch, path)):
                self._discoverSubmittedFiles(os.path.join(directoryToSearch, path))
                continue

            if self.IPYTHON_FILE_REGEX.match(path):
                self._discoveredFiles.append(os.path.join(directoryToSearch, path))

    def _exportHTML(self, notebook: NotebookNode):
        if self._htmlTransformationEnabled:
            exporter = nbconvert.HTMLExporter()
            (self._notebookHtml, _) = exporter.from_notebook_node(notebook)

    def _parseCells(self, notebook: NotebookNode):
        for cell in notebook.cells:
            if cell["cell_type"] != "code":
                continue

            source = self.runTransformers(cell["source"])

            metadata = parseCellMetadata(ast.parse(source))

            if metadata is None:
                continue

            cellWithMetadata = Cell(metadata, source)

            self._cells[metadata.id] = cellWithMetadata

    def addPackages(self: Builder, packages: List[Dict[str, str]]) -> Builder:
        for package in packages:
            self._extraPackages.update({package['name']: package['version']})

        return self

    def _installRequirements(self) -> None:
        for package, version in self._extraPackages.items():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install",
                                       f"{package}=={version}" if version else package],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as _:  # pragma: no cover
                try:  # pragma: no cover
                    subprocess.check_call([sys.executable, "-m", "pip", "install",  # pragma: no cover
                                           f"{package}=={version}" if version else package, "--break-system-packages"], # pragma: no cover

                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # pragma: no cover
                except subprocess.CalledProcessError as error:  # pragma: no cover
                    raise Exception(f"Failed to install '{package}'!")  # pragma: no cover

    def doLoad(self):
        self._discoverSubmittedFiles(self.getSubmissionRoot())
        self.runManualValidationHook(IPythonFileValidator)

        fileToLoad = self._discoveredFiles[0]

        with open(fileToLoad, 'r', encoding="UTF-8") as r:
            loadedNotebook: NotebookNode = read(r, as_version=4)

        self._exportHTML(loadedNotebook)

        self._parseCells(loadedNotebook)

    def _buildCells(self):
        for cell in self._cells.values():
            if not cell.metadata.runnable:
                continue

            sortedDeps = sorted(cell.metadata.deps, key=lambda x: x.order)

            # testable code is always last in the ordering
            sortedDeps.append((-1, cell.metadata.id))

            combinedSrc = "\n".join([self._cells[id].code for _, id in sortedDeps])

            builtCell: CodeType = compile(combinedSrc, f"student_submission_{cell.metadata.id}", "exec")

            self._builtCells[cell.metadata.id] = builtCell

    def doBuild(self):
        self._installRequirements()
        self._buildCells()

    def TEST_ONLY_removeRequirements(self):
        for package in self._extraPackages.keys():
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall",
                                   "-y", package],
                                  stdout=subprocess.DEVNULL)

    def setActiveCell(self, activeCell: str):
        if activeCell not in self._builtCells.keys():
            raise RuntimeError(f"Invalid active cell '{activeCell}'! Expected one of {', '.join(self._builtCells.keys())}")

        self._activeCell = activeCell

    def getExecutableSubmission(self) -> CodeType:
        if self._activeCell is None and len(self._builtCells) != 1:
            raise RuntimeError("No active cell has been defined!")

        if len(self._builtCells) == 1:
            return self._builtCells[list(self._builtCells.keys())[0]]

        return self._builtCells[self._activeCell]

    def enableHtmlTransformation(self: Builder, enabled: bool = True) -> Builder:
        self._htmlTransformationEnabled = enabled
        return self

    def getCells(self) -> Dict[str, Cell]:
        return self._cells

    def getExtraPackages(self) -> Dict[str, str]:
        return self._extraPackages

    def getDiscoveredFiles(self) -> List[str]:
        return self._discoveredFiles

    def getNotebookHtml(self) -> str:
        if not self._htmlTransformationEnabled or self._notebookHtml is None:
            raise RuntimeError("Notebook HTML requested, but not available!")
        return self._notebookHtml
