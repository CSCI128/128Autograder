import abc
from typing import List

from .common import ValidationHook

class AbstractValidator(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def getValidationHook() -> ValidationHook:
        pass

    def __init__(self):
        self.errors: List[Exception] = []

    @abc.abstractmethod
    # this should be typed, but its a weird cross depenacny issue
    def setup(self, studentSubmission):
        pass

    @abc.abstractmethod
    def run(self):
        pass

    def addError(self, error: Exception):
        self.errors.append(error)

    def collectErrors(self) -> List[Exception]:
        return self.errors
