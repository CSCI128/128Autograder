from enum import Enum
from typing import Iterable, TypedDict, Tuple, Dict, Optional

from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock


class FileTypeMap(Enum):
    TEST_FILES = 1
    PYTHON_FILES = 2
    REQUIREMENTS = 3

class PythonTaskResult(TypedDict):
    return_val: object
    parameters: Optional[Tuple[object, ...]]
    mocks: Dict[str, SingleFunctionMock]

class NoPyFilesError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Expected at least one `.py` file. Received 0.\n"
            "Are you writing your code in a file that ends with `.py`?"
        )

class MissingMainFileError(Exception):
    def __init__(self, expectedMains: Iterable[str], files: Iterable[str]) -> None:
        super().__init__(
            f"Expected file named {' or '.join(file for file in expectedMains)}. Received: {','.join(file for file in files)}"
        )

class TooManyFilesError(Exception):
    def __init__(self, files: Iterable[str]) -> None:
        super().__init__(
            f"Expected one `.py` file. Received: {', '.join(file for file in files)}\n"
            "Please delete extra `.py` files"
        )

class InvalidPackageError(Exception):
    def __init__(self, packageName: str, version: str):
        super().__init__(
            f"Unable to locate package, '{packageName}' at version "
            f"{version if version else 'any version'}"
        )

class InvalidRequirementsFileError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
