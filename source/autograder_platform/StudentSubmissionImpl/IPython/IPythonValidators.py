import importlib
from typing import List, Dict

import requests

from autograder_platform.StudentSubmission.AbstractValidator import AbstractValidator
from autograder_platform.StudentSubmission.common import ValidationHook
from autograder_platform.StudentSubmissionImpl.IPython.common import MissingNotebookFile, TooManyNotebooksError, \
    MissingDependencyError, NoTestableCellsError

from autograder_platform.StudentSubmissionImpl.IPython.common import InvalidPackageError


class TestableCellDependencyValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self):
        super().__init__()
        self.cells = {}

    def setup(self, studentSubmission):
        self.cells = studentSubmission.getCells()

    def run(self):
        availableCells = self.cells.keys()

        for cell in self.cells.values():
            metadata = cell.metadata
            for dep in metadata.deps:
                if dep.id not in availableCells:
                    self.addError(MissingDependencyError(metadata.id, dep.id, availableCells))

class TestableCellValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self):
        super().__init__()
        self.cells = {}

    def setup(self, studentSubmission):
        self.cells = studentSubmission.getCells()

    def run(self):
        numberRunnable = 0
        for cell in self.cells.values():
            metadata = cell.metadata

            numberRunnable += int(metadata.runnable)

        if numberRunnable == 0:
            self.addError(NoTestableCellsError())


class IPythonFileValidator(AbstractValidator):

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.MANUAL

    def __init__(self):
        super().__init__()
        self.files: List[str] = []

    def setup(self, studentSubmission):
        self.files = studentSubmission.getDiscoveredFiles()

    def run(self):
        if len(self.files) == 0:
            self.addError(MissingNotebookFile())
            return
        if len(self.files) > 1:
            self.addError(TooManyNotebooksError(self.files))

class PackageValidator(AbstractValidator):

    PYPI_BASE = "https://pypi.org/pypi/"

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.PRE_LOAD

    def __init__(self):
        super().__init__()
        self.packages: Dict[str, str] = {}

    def setup(self, studentSubmission):
        self.packages = studentSubmission.getExtraPackages()

    def run(self):
        for package, version in self.packages.items():
            if importlib.util.find_spec(package) is not None:
                continue

            url = self.PYPI_BASE + package + "/"

            if version:
                url += version + "/"

            url += "json"

            if requests.get(url=url).status_code == 200:
                continue

            self.addError(InvalidPackageError(package, version))
