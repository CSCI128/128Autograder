from typing import List

from autograder_platform.StudentSubmission.AbstractValidator import AbstractValidator
from autograder_platform.StudentSubmission.common import ValidationHook
from language_binds.IPython.common import MissingNotebookFile, TooManyNotebooksError, \
    MissingDependencyError, NoTestableCellsError

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
                if dep not in availableCells:
                    self.addError(MissingDependencyError(metadata.id, dep, availableCells))

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
