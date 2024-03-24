import importlib.util
from typing import Callable, Dict, List
import requests
import os
from StudentSubmission.AbstractValidator import AbstractValidator
from StudentSubmission.common import ValidationHook
from StudentSubmissionImpl.Python.common import FileTypeMap, InvalidPackageError, InvalidRequirementsFileError, MissingMainFileError, NoPyFilesError, TooManyFilesError

class PythonFileValidator(AbstractValidator):

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self, allowedMainNames: List[str]):
        super().__init__()
        self.allowedMainNames = allowedMainNames
        self.pythonFiles: Dict[FileTypeMap, List[str]] = {}
        self.looseMainMatchingAllowed: bool = False

    def setup(self, studentSubmission):
        submissionFiles = studentSubmission.getDiscoveredFileMap()
        self.looseMainMatchingAllowed = studentSubmission.getLooseMainMatchingEnabled()

        if studentSubmission.getTestFilesEnabled() and FileTypeMap.TEST_FILES in submissionFiles.keys():
            self.pythonFiles[FileTypeMap.TEST_FILES] = submissionFiles[FileTypeMap.TEST_FILES]

        if FileTypeMap.PYTHON_FILES not in submissionFiles:
            submissionFiles[FileTypeMap.PYTHON_FILES] = []

        self.pythonFiles[FileTypeMap.PYTHON_FILES] = [os.path.basename(file) for file in submissionFiles[FileTypeMap.PYTHON_FILES]]

    def run(self):
        if not self.pythonFiles[FileTypeMap.PYTHON_FILES]:
            self.addError(NoPyFilesError())
            return

        if self.looseMainMatchingAllowed and len(self.pythonFiles[FileTypeMap.PYTHON_FILES]) > 1:
            self.addError(TooManyFilesError(self.pythonFiles[FileTypeMap.PYTHON_FILES]))
            return

        if self.looseMainMatchingAllowed:
            return

        mainNameFilter: Callable[[str], bool] = lambda x: x in self.allowedMainNames

        filteredFiles = list(filter(mainNameFilter, self.pythonFiles[FileTypeMap.PYTHON_FILES]))

        if not filteredFiles:
            self.addError(MissingMainFileError(self.allowedMainNames, self.pythonFiles[FileTypeMap.PYTHON_FILES]))
            return
        
        if len(filteredFiles) != 1:
            self.addError(TooManyFilesError(filteredFiles))

class RequirementsValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self):
        super().__init__()
        self.requirements: List[str] = []
        self.submissionBase: str = ""

    def setup(self, studentSubmission):
        self.submissionBase = studentSubmission.getSubmissionRoot()
        files = studentSubmission.getDiscoveredFileMap()
        if FileTypeMap.REQUIREMENTS not in files:
            files[FileTypeMap.REQUIREMENTS] = []

        self.requirements = files[FileTypeMap.REQUIREMENTS]

    def run(self):
        if not self.requirements:
            return

        if len(self.requirements) != 1:
            self.addError(InvalidRequirementsFileError(
                    "Too many requirements.txt files.\n"
                    f"Expected 1, received {len(self.requirements)}"
                )
            )
        for file in self.requirements:
            if file == os.path.join(self.submissionBase, "requirements.txt"):
                continue

            self.addError(InvalidRequirementsFileError(
                    "Invalid location for requirements file.\n"
                    f"Should be {os.path.join(self.submissionBase, 'requirements.txt')}\n"
                    f"But was {file}"
                )
            )

class PackageValidator(AbstractValidator):

    PYPI_BASE = "https://pypi.org/pypi/"

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.PRE_BUILD

    def __init__(self):
        super().__init__()
        self.packages: Dict[str, str] = {}

    def setup(self, studentSubmission):
        self.packages = studentSubmission.getExtraPackages()

    def run(self):

        for package, version in self.packages.items():
            if importlib.util.find_spec(package) != None:
                continue

            url = self.PYPI_BASE + package + "/"

            if version:
                url += version + "/"

            url += "json"

            if requests.get(url=url).status_code == 200:
                continue

            self.addError(InvalidPackageError(package, version))


        

