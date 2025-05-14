from typing import List

from autograder_platform.StudentSubmission.AbstractValidator import AbstractValidator
from autograder_platform.StudentSubmission.common import ValidationHook
from autograder_platform.StudentSubmissionImpl.ipython.common import MissingNotebookFile, TooManyNotebooksError


class TestableCellDependencyValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def setup(self, studentSubmission):
        pass

    def run(self):
        pass

class TestableCellValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def setup(self, studentSubmission):
        pass

    def run(self):
        pass


class IPythonFileValidator(AbstractValidator):

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.MANUAL

    def __init__(self):
        super().__init__()
        self.files: List[str] = []

    def setup(self, studentSubmission):
        submissionFiles = studentSubmission.getDiscoveredFiles()

    def run(self):
        if len(self.files) == 0:
            self.addError(MissingNotebookFile())
            return
        if len(self.files) > 1:
            self.addError(TooManyNotebooksError(self.files))
