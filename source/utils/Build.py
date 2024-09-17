import os
import re
import shutil
from typing import Dict, List
from utils.config.Config import AutograderConfiguration
from enum import Enum


class FilesEnum(Enum):
    PUBLIC_TEST = 0
    PRIVATE_TEST = 1
    PUBLIC_DATA = 2
    PRIVATE_DATA = 3
    STARTER_CODE = 4


class Build():
    IGNORE = ["__pycache__"]
    GRADESCOPE_ROOT = ["setup.sh", "run_autograder_gs"]
    GRADESCOPE_NAME_MAP = {'run_autograder_gs': 'run_autograder'}

    RENAMER = lambda map, x: map[x] if x in map.keys() else x

    def __init__(self, config: AutograderConfiguration, sourceRoot=os.getcwd(), binRoot="bin") -> None:
        self.config = config
        self.generationDirectory = os.path.join(binRoot, "generation")
        self.distDirectory = os.path.join(binRoot, "dist")
        self.binRoot = binRoot
        self.sourceDir = sourceRoot

    @staticmethod
    def _discoverTestFiles(allowPrivate: bool,
                           privateTestFileRegex: re.Pattern, publicTestFileRegex: re.Pattern,
                           testDirectory: str,
                           discoveredPrivateFiles: List[str], discoveredPublicFiles: List[str]):
        """
        Description
        ---

        This function discovers the test files in the testDirectory and puts them in the correct list
        based on the regex matches.

        Note: If allowPrivate is false, then all files that match the private regex will be added to the public list

        :param allowPrivate: If private files should be treated as private
        :param privateTestFileRegex: The regex pattern used to match private test files
        :param publicTestFileRegex: The regex pattern used to match public test files
        :param discoveredPrivateFiles: The list that contains the private files to be copied
        :param discoveredPublicFiles: The list that contains the public files to be copied
        """

        # test discovery is non recursive for now
        test_files = [file for file in os.listdir(testDirectory) if os.path.isfile(os.path.join(testDirectory, file))]

        for file in test_files:
            path = os.path.join(testDirectory, file)
            # Dont need to worry about double checking, the private test will only be run once in both of these cases
            if allowPrivate and privateTestFileRegex.match(file):
                discoveredPrivateFiles.append(path)
            elif publicTestFileRegex.match(file) or privateTestFileRegex.match(file):
                discoveredPublicFiles.append(path)

    @staticmethod
    def _discoverDataFiles(allowPrivate: bool, dataFilesSource: str,
                           discoveredPrivateFiles: List[str], discoveredPublicFiles: List[str]):
        """
        Description
        ---

        This function recursivly discovers the data files in the dataFilesSource.
        As opposed to the test file function, this will mark files as private if they contain 'private' anywhere in the path.

        Note: if allowPrivate is false, then all files that would otherwise be private will be added to the public list
        
        In the godforsaken event that some how we have a directory structure that exceeds 1000 folders, this will fail
        due to a recursion error

        :param allowPrivate: If private files should be treated as private
        :param dataFilesSource: The current search directory
        :param discoveredPrivateFiles: The list that contains the private files to be copied
        :param discoveredPublicFiles: the list that contains the public files to be copied
        """

        for file in os.listdir(dataFilesSource):
            # ignore hidden files + directories
            if file[0] == ".":
                continue

            path = os.path.join(dataFilesSource, file)

            # ignore any and all test files
            if os.path.isfile(path) and "test" in file.lower():
                continue

            if os.path.isdir(path):
                Build._discoverDataFiles(allowPrivate, path, discoveredPrivateFiles, discoveredPublicFiles)
                continue

            if allowPrivate and "private" in path.lower():
                discoveredPrivateFiles.append(path)
                continue

            discoveredPublicFiles.append(path)

    def discoverFiles(self) -> Dict[FilesEnum, List[str]]:
        """
        Description
        ---

        This function discovers all of the user defined files to copy.
        See :ref:`_discoverTestFiles` and :ref:`_discoverDataFiles` for more information on how this process works

        :returns: A map containing all the user defined files to copy
        """
        config = self.config.build

        files: Dict[FilesEnum, List[str]] = {
            FilesEnum.PUBLIC_TEST: [],
            FilesEnum.PRIVATE_TEST: [],
            FilesEnum.PUBLIC_DATA: [],
            FilesEnum.PRIVATE_DATA: [],
            FilesEnum.STARTER_CODE: [],
        }

        self._discoverTestFiles(config.allow_private,
                                re.compile(config.private_tests_regex), re.compile(config.public_tests_regex),
                                self.config.config.test_directory,
                                files[FilesEnum.PRIVATE_TEST], files[FilesEnum.PUBLIC_TEST])

        # imo, this is not worth moving into its function atm
        if config.use_starter_code:
            # we can assume that the file exists if the config has it
            files[FilesEnum.STARTER_CODE].append(config.starter_code_source)

        if config.use_data_files:
            self._discoverDataFiles(config.allow_private, config.data_files_source,
                                    files[FilesEnum.PRIVATE_DATA], files[FilesEnum.PUBLIC_DATA])

        return files

    @staticmethod
    def buildUtilsPath() -> List[str]:
        configSource = os.path.join("utils", "config")
        studentUtilsSource = os.path.join("utils", "student")
        gradescopeUtilsSource = os.path.join("utils", "Gradescope.py")
        utilsModuleSource = os.path.join("utils", "__init__.py")

        return [configSource, studentUtilsSource, gradescopeUtilsSource, utilsModuleSource]

    @staticmethod
    def buildStudentSubmissionPath(implToUse) -> List[str]:
        implSource = os.path.join("StudentSubmissionImpl", implToUse)
        studentSubmissionSource = os.path.join("StudentSubmission")

        return [implSource, studentSubmissionSource]

    @staticmethod
    def buildTasksPath() -> List[str]:
        tasksSource = os.path.join("Tasks")

        return [tasksSource]

    @staticmethod
    def buildTestingFrameworkPath() -> List[str]:
        testingFrameworkSource = os.path.join("TestingFramework")

        return [testingFrameworkSource]

    @staticmethod
    def buildExecutorsPath() -> List[str]:
        executorsSource = os.path.join("Executors")

        return [executorsSource]

    @staticmethod
    def buildBasePath() -> List[str]:
        runSource = "run.py"
        setupSource = "setup.sh"
        configSource = "config.toml"
        requirementsSource = "requirements.txt"
        runAutograderSource = "run_autograder"

        return [runSource, setupSource, configSource, requirementsSource, runAutograderSource]

    @staticmethod
    def buildStudentPath() -> List[str]:
        studentRoot = os.path.join("utils", "student")
        gradescopeUpload = os.path.join(studentRoot, "create_gradescope_upload.py")
        testWork = os.path.join(studentRoot, "test_my_work.py")

        return [gradescopeUpload, testWork]

    @staticmethod
    def copy(src, dest):
        if os.path.isdir(src):
            shutil.copytree(src, dest)
            return

        shutil.copy(src, dest)

    def createFolders(self):
        # clean build if it exists
        if os.path.exists(self.binRoot):
            try:
                shutil.rmtree(self.binRoot, ignore_errors=True)
            except OSError:
                print("WARN: Failed to clean bin directory")

        # create directories
        os.makedirs(self.generationDirectory, exist_ok=True)
        os.makedirs(self.distDirectory, exist_ok=True)

    @staticmethod
    def generateGradescope(generationPath: str, files: Dict[FilesEnum, List[str]], autograderFiles: List[str]):
        generationPath = os.path.join(generationPath, "gradescope")
        os.makedirs(generationPath, exist_ok=True)

        for file in autograderFiles:
            destPath = os.path.join(generationPath, Build.RENAMER(Build.GRADESCOPE_NAME_MAP, file))

            os.makedirs(os.path.dirname(generationPath), exist_ok=True)
            Build.copy(file, destPath)

        for key, listOfFiles in files.items():
            if key is FilesEnum.STARTER_CODE:
                continue

            for file in listOfFiles:
                destPath = os.path.join(generationPath, file)
                os.makedirs(os.path.dirname(destPath), exist_ok=True)
                Build.copy(file, destPath)

    @staticmethod
    def generateStudent(generationPath: str, files: Dict[FilesEnum, List[str]], autograderFiles: List[str],
                        studentFiles: List[str]):
        generationPath = os.path.join(generationPath, "student")
        os.makedirs(generationPath, exist_ok=True)

        # create student_work folder
        studentWorkFolder = os.path.join(generationPath, "student_work")
        os.makedirs(studentWorkFolder, exist_ok=True)

        for file in autograderFiles:
            if os.path.basename(file) in Build.GRADESCOPE_ROOT:
                continue

            destPath = os.path.join(generationPath, file)
            os.makedirs(os.path.dirname(generationPath), exist_ok=True)
            Build.copy(file, destPath)

        for file in files[FilesEnum.PUBLIC_TEST]:
            destPath = os.path.join(generationPath, file)
            os.makedirs(os.path.dirname(destPath), exist_ok=True)
            Build.copy(file, destPath)

        for file in files[FilesEnum.PUBLIC_DATA]:
            destPath = os.path.join(generationPath, file)
            os.makedirs(os.path.dirname(destPath), exist_ok=True)
            Build.copy(file, destPath)
            # also add to student work folder
            destPath = os.path.join(studentWorkFolder, os.path.basename(file))
            Build.copy(file, destPath)

        for file in files[FilesEnum.STARTER_CODE]:
            destPath = os.path.join(studentWorkFolder, os.path.basename(file))
            Build.copy(file, destPath)

        for file in studentFiles:
            destPath = os.path.join(generationPath, os.path.basename(file))
            Build.copy(file, destPath)

        # create .keep so that we dont loose the file
        with open(os.path.join(studentWorkFolder, ".keep"), "w") as w:
            w.write("DO NOT WRITE YOUR CODE HERE!\nCreate a *new* file in this directory!!!")

    @staticmethod
    def createDist(distType: str, generationPath: str, distPath: str, assignmentName: str):
        generationPath = os.path.join(generationPath, distType)
        if not os.path.exists(generationPath) or not os.path.isdir(generationPath):
            raise AttributeError(f"Invalid Gradescope generation path! {generationPath}")

        os.makedirs(distPath, exist_ok=True)

        assignmentName += f"-{distType}"
        distPath = os.path.join(distPath, assignmentName)

        shutil.make_archive(distPath, "zip", root_dir=generationPath)

    def build(self):
        files = self.discoverFiles()

        autograderFiles = []

        autograderFiles.extend(self.buildUtilsPath())
        autograderFiles.extend(self.buildStudentSubmissionPath(self.config.config.impl_to_use))
        autograderFiles.extend(self.buildTasksPath())
        autograderFiles.extend(self.buildTestingFrameworkPath())
        autograderFiles.extend(self.buildExecutorsPath())
        autograderFiles.extend(self.buildBasePath())

        studentFiles = self.buildStudentPath()

        self.createFolders()

        if self.config.build.build_gradescope:
            self.generateGradescope(self.generationDirectory, files, autograderFiles)
            self.createDist("gradescope", self.generationDirectory, self.distDirectory,
                            f"{self.config.semester}_{self.config.assignment_name}")

        if self.config.build.build_student:
            self.generateStudent(self.generationDirectory, files, autograderFiles, studentFiles)
            self.createDist("student", self.generationDirectory, self.distDirectory,
                            f"{self.config.semester}_{self.config.assignment_name}")
