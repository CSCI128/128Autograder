from .common import ValidationHook
from .AbstractValidator import AbstractValidator
from os import PathLike
import os
from typing import Union

class SubmissionPathValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.PRE_LOAD

    def __init__(self):
        super().__init__()
        self.pathToValidate: Union[PathLike, str] = ""

    def setup(self, studentSubmission):
        self.pathToValidate = studentSubmission.getSubmissionRoot()
        
    def run(self):
        if not os.path.exists(self.pathToValidate):
            self.addError(
                FileNotFoundError(f"{self.pathToValidate} does not exist or is not accessible!")
            )
            return

        if not os.path.isdir(self.pathToValidate):
            self.addError(
                NotADirectoryError(f"{self.pathToValidate} is not a directory!")
            )

        if not os.access(self.pathToValidate, os.R_OK):
            self.addError(
                PermissionError(f"Unable to read from {self.pathToValidate}!")
            )

        if len(os.listdir(self.pathToValidate)) < 1:
            self.addError(
                FileNotFoundError(
                    f"No files found in {self.pathToValidate}.\n"
                    f"Ensure that your submission is in {self.pathToValidate}."
                )
            )

