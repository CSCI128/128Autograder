import ast
import dataclasses
import os
import re
from types import CodeType
from typing import TypeVar, List, Tuple, Dict, Iterable, Optional, cast

import nbconvert
from nbformat import read, NotebookNode

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.StudentSubmissionImpl.ipython.CellMetadataParser import CellMetadata, parseCellMetadata
from autograder_platform.StudentSubmissionImpl.ipython.IPythonTransformers import MagicCommandTransformer, \
    MatplotLibFigTransformer
from autograder_platform.StudentSubmissionImpl.ipython.iPythonValidators import IPythonFileValidator

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
        self.cells: Dict[str, Cell] = {}
        self.discoveredFiles: List[str] = []
        self.htmlTransformationEnabled: bool = False
        self.notebookHtml: Optional[str] = None

        self.addValidator(IPythonFileValidator())
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
                self.discoveredFiles.append(os.path.join(directoryToSearch, path))


    def doLoad(self):
        self._discoverSubmittedFiles(self.getSubmissionRoot())
        self.runManualValidationHook(IPythonFileValidator)

        fileToLoad = self.discoveredFiles[0]

        with open(fileToLoad, 'r', encoding="UTF-8") as r:
            loadedNotebook: NotebookNode = read(r, as_version=4)

        if self.htmlTransformationEnabled:
            exporter = nbconvert.HTMLExporter(template="default")
            self.notebookHtml = exporter.export_from_notebook(loadedNotebook)

        for cell in loadedNotebook.cells:
            if "cell_type" not in cell or "source" not in cell:
                continue

            if cell["cell_type"] != "code":
                continue

            source = self.runTransformers(cell["source"])

            metadata = parseCellMetadata(ast.parse(source))

            if metadata is None:
                continue

            cellWithMetadata = Cell(metadata, source)

            self.cells[metadata.id] = cellWithMetadata

    def doBuild(self):
        pass

    def getExecutableSubmission(self) -> CodeType:
        pass

    def enableHtmlTransformation(self: Builder, enabled: bool = True) -> Builder:
        self.htmlTransformationEnabled = enabled
        return self

    def getDiscoveredFiles(self) -> List[str]:
        return self.discoveredFiles

    def getNotebookHtml(self) -> str:
        if not self.htmlTransformationEnabled or self.notebookHtml is None:
            raise RuntimeError("Notebook HTML requested, but not available!")
        return self.notebookHtml
