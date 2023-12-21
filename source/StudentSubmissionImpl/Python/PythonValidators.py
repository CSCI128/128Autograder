from typing import Dict, Set, List
from StudentSubmission import AbstractValidator
from StudentSubmission.common import ValidationHook
from .common import FileTypeMap, InvalidPackageError, MissingMainFileError, NoPyFilesError, TooManyFilesError
from .PythonSubmission import StudentSubmission

class PythonFileValidator(AbstractValidator):

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self, allowedMainNames: List[str]):
        super().__init__()
        self.ALLOWED_MAIN_NAMES = allowedMainNames
        self.pythonFiles: Dict[FileTypeMap, Set[str]] = {}
        self.looseMainMatchingAllowed: bool = False

    def setup(self, studentSubmission: StudentSubmission):
        submissionFiles = studentSubmission.getDiscoveredFileMap()
        self.looseMainMatchingAllowed = studentSubmission.looseMainMatchingAllowed()

        if studentSubmission.testFilesAllowed():
            self.pythonFiles[FileTypeMap.TEST_FILES] = submissionFiles[FileTypeMap.TEST_FILES]

        if FileTypeMap.PYTHON_FILES not in submissionFiles:
            submissionFiles[FileTypeMap.PYTHON_FILES] = set() 

        self.pythonFiles[FileTypeMap.PYTHON_FILES] = submissionFiles[FileTypeMap.PYTHON_FILES]

    def run(self):
        if not self.pythonFiles[FileTypeMap.PYTHON_FILES]:
            self.addError(NoPyFilesError())
            return

        if self.looseMainMatchingAllowed and len(self.pythonFiles[FileTypeMap.PYTHON_FILES]) > 1:
            self.addError(TooManyFilesError(self.pythonFiles[FileTypeMap.PYTHON_FILES]))
            return

        if not any(file in self.pythonFiles[FileTypeMap.PYTHON_FILES] for file in self.ALLOWED_MAIN_NAMES):
            self.addError(MissingMainFileError(self.ALLOWED_MAIN_NAMES, self.pythonFiles[FileTypeMap.PYTHON_FILES]))
            return

class RequirementsValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self):
        super().__init__()
        self.requirements: Set[str] = set()
        self.submissionBase: str = ""

    def setup(self, studentSubmission: StudentSubmission):
        self.submissionBase = studentSubmission.getSubmissionRoot()
        files = studentSubmission.getDiscoveredFileMap()
        if FileTypeMap.REQUIREMENTS not in files:
            files[FileTypeMap.REQUIREMENTS] = set()

        self.requirements = files[FileTypeMap.REQUIREMENTS]

    def run(self):
        pass




class PackageValidator(AbstractValidator):

    PYPI_BASE = "https://pypi.org/pypi/"

    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.PRE_BUILD

    def __init__(self):
        super().__init__()
        self.packages: Dict[str, str] = {}

    def setup(self, studentSubmission: StudentSubmission):
        self.packages = studentSubmission.getExtraPackages()

    def run(self):
        # this is pretty slow, but basically, it issues a request to PyPi to see if a package is avaiable for install
        # might want to have a custom exception for packages that aren't installed
        import requests

        for package, version in self.packages.items():
            url = self.PYPI_BASE + package + "/"

            if version:
                url += version + "/"

            url += "json"

            if requests.get(url=url).status_code == 200:
                continue

            self.addError(InvalidPackageError(package, version))


        

