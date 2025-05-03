import ast
import dataclasses
import re
from types import CodeType
from typing import TypeVar, List

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission

Builder = TypeVar("Builder", bound="IPythonSubmission")

def filterSearchResults(path: str) -> bool:
    if path[0] == ".":
        return False
    if "__pycache__" in path:
        return False
    if " " in path:
        return False

    return True


class IPythonSubmission(AbstractStudentSubmission[CodeType]):
    IPYTHON_FILE_REGEX: re.Pattern = re.compile(r"^(\w|-)+\.ipynb")

    def doLoad(self):
        pass

    def doBuild(self):
        pass

    def getExecutableSubmission(self) -> CodeType:
        pass
