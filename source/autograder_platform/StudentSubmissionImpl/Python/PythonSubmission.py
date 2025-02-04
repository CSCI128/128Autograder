import os
import re
import sys
import subprocess
from types import CodeType
from typing import Dict, Iterable, List, Optional, TypeVar
from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.StudentSubmissionImpl.Python.PythonValidators import PythonFileValidator, PackageValidator, RequirementsValidator
from autograder_platform.StudentSubmissionImpl.Python.common import FileTypeMap

Builder = TypeVar("Builder", bound="PythonSubmission")


def filterSearchResults(path: str) -> bool:
    # ignore hidden files
    if path[0] == '.':
        return False

    # ignore python cache files
    if "__pycache__" in path:
        return False

    if " " in path:
        return False

    return True


class PythonSubmission(AbstractStudentSubmission[CodeType]):
    ALLOWED_STRICT_MAIN_NAMES = ["main.py", "submission.py"]

    # we are not allowing any files with a space in them
    PYTHON_FILE_REGEX: re.Pattern = re.compile(r"^(\w|-)+\.py$")
    # the requirements.txt file MUST be in the root of the student's submission
    REQUIREMENTS_REGEX: re.Pattern = re.compile(r"^requirements\.txt$")
    # test files follow similar rules to python files, but must start with 'test'
    TEST_FILE_REGEX: re.Pattern = re.compile(r"^test(\w|-)*\.py$")
    # this allows versioned and non versioned packages, but disallows local packages
    REQUIREMENTS_LINE_REGEX: re.Pattern = re.compile(r"^(\w|-)+(==)?(\d+\.?){0,3}$")

    def __init__(self):
        super().__init__()

        self.testFilesEnabled: bool = False
        self.requirementsEnabled: bool = False
        self.looseMainMatchingEnabled: bool = False

        self.discoveredFileMap: Dict[FileTypeMap, List[str]] = {}

        self.extraPackages: Dict[str, str] = {}

        self.entryPoint: Optional[CodeType] = None

        self.addValidator(PythonFileValidator(self.ALLOWED_STRICT_MAIN_NAMES))
        self.addValidator(RequirementsValidator())
        self.addValidator(PackageValidator())

    def enableTestFiles(self: Builder, enableTestFiles: bool = True) -> Builder:
        self.testFilesEnabled = enableTestFiles
        return self

    def enableRequirements(self: Builder, enableRequirements: bool = True) -> Builder:
        self.requirementsEnabled = enableRequirements
        return self

    def enableLooseMainMatching(self: Builder, enableLooseMainMatching: bool = True) -> Builder:
        self.looseMainMatchingEnabled = enableLooseMainMatching
        return self

    def addPackage(self: Builder, packageName: str, packageVersion: Optional[str] = None) -> Builder:
        self.extraPackages[packageName] = packageVersion if packageVersion is not None else ""
        return self

    def addPackages(self: Builder, packages: List[Dict[str, str]]) -> Builder:
        for package in packages:
            self.extraPackages.update({package['name']: package['version']})

        return self

    def _addFileToMap(self, path: str, fileType: FileTypeMap) -> None:
        if fileType not in self.discoveredFileMap.keys():
            self.discoveredFileMap[fileType] = []

        self.discoveredFileMap[fileType].append(path)

    def _discoverSubmittedFiles(self, directoryToSearch: str) -> None:
        pathsToVisit: Iterable[str] = filter(filterSearchResults, os.listdir(directoryToSearch))

        if not pathsToVisit:
            return

        for path in pathsToVisit:
            if os.path.isdir(os.path.join(directoryToSearch, path)):
                self._discoverSubmittedFiles(os.path.join(directoryToSearch, path))
                continue

            if self.getTestFilesEnabled() and self.TEST_FILE_REGEX.match(path):
                self._addFileToMap(os.path.join(directoryToSearch, path), FileTypeMap.TEST_FILES)
                continue

            if self.PYTHON_FILE_REGEX.match(path):
                self._addFileToMap(os.path.join(directoryToSearch, path), FileTypeMap.PYTHON_FILES)
                continue

            if self.getRequirementsEnabled() and self.REQUIREMENTS_REGEX.match(path):
                self._addFileToMap(os.path.join(directoryToSearch, path), FileTypeMap.REQUIREMENTS)

    def _loadRequirements(self) -> None:
        if not self.getRequirementsEnabled() or FileTypeMap.REQUIREMENTS not in self.discoveredFileMap:
            return

        with open(self.discoveredFileMap[FileTypeMap.REQUIREMENTS][0], 'r') as r:
            # we are going to ignore any paths that aren't set up as package==version
            for line in r:
                line = line.strip()
                # we might want to add logging + telementry
                if not self.REQUIREMENTS_LINE_REGEX.match(line):
                    # we might want to add some logging here
                    continue
                line = line.split('==')

                self.addPackage(line[0], line[1] if len(line) == 2 else None)

    def _installRequirements(self) -> None:
        if not self.getRequirementsEnabled() or not self.extraPackages:
            return

        for package, version in self.extraPackages.items():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install",
                                       f"{package}=={version}" if version else package],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # this isn't testable :( – basically this reattempts install if it fails by adding the magic flag
            except subprocess.CalledProcessError as _:  # pragma: no cover
                try:  # pragma: no cover
                    subprocess.check_call([sys.executable, "-m", "pip", "install",  # pragma: no cover
                                           f"{package}=={version}" if version else package, "--break-system-packages"], # pragma: no cover

                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # pragma: no cover
                except subprocess.CalledProcessError as error:  # pragma: no cover
                    raise Exception(f"Failed to install '{package}'!")  # pragma: no cover

    def _identifyMainFile(self) -> str:
        if self.getLooseMainMatchingEnabled():
            return self.discoveredFileMap[FileTypeMap.PYTHON_FILES][0]

        for file in self.discoveredFileMap[FileTypeMap.PYTHON_FILES]:
            if os.path.basename(file) in self.ALLOWED_STRICT_MAIN_NAMES:
                return file

        # unreachable
        raise RuntimeError("Failed to identify main file! This error should be caught by a validator")

    def _readMainFile(self, mainPath) -> str:
        with open(mainPath, 'r', encoding="UTF-8") as r:
            return r.read()

    def _compileFile(self, filePath, code: str) -> CodeType:
        return compile(code, filePath, "exec")

    def doLoad(self):
        self._discoverSubmittedFiles(self.getSubmissionRoot())
        self._loadRequirements()

    def doBuild(self):
        self._installRequirements()
        mainFilePath = self._identifyMainFile()
        mainFileCode = self._readMainFile(mainFilePath)

        self.entryPoint = self._compileFile(mainFilePath, mainFileCode)

        # Huge todo here - This will be a seperate story i think
        # Basically by creating a meta hook in the import system, we can resolve modules from the students submission.
        # This also allows us to mock out imported libraries.
        # Im thinking this might be a seperate module as there is a decent amount of machinary that we need to override.

    def getExecutableSubmission(self) -> CodeType:
        if self.entryPoint is None:
            raise RuntimeError("Submission has not been built! No entrypoint has been defined!")
        return self.entryPoint

    def TEST_ONLY_removeRequirements(self):
        if not self.getRequirementsEnabled() or not self.extraPackages:
            return

        for package in self.extraPackages.keys():
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall",
                                   "-y", package],
                                  stdout=subprocess.DEVNULL)

    def getTestFilesEnabled(self) -> bool:
        return self.testFilesEnabled

    def getRequirementsEnabled(self) -> bool:
        return self.requirementsEnabled

    def getLooseMainMatchingEnabled(self) -> bool:
        return self.looseMainMatchingEnabled

    def getDiscoveredFileMap(self) -> Dict[FileTypeMap, List[str]]:
        return self.discoveredFileMap

    def getExtraPackages(self) -> Dict[str, str]:
        return self.extraPackages
