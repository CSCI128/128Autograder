import os
import re
import shutil
from enum import Enum
from typing import List, Dict, Callable

from autograder_platform.cli import AutograderCLITool
from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfiguration


class FilesEnum(Enum):
    PUBLIC_TEST = 0
    PRIVATE_TEST = 1
    PUBLIC_DATA = 2
    PRIVATE_DATA = 3
    STARTER_CODE = 4
    CONFIG_FILE = 5


class Build:
    IGNORE = ["__pycache__"]

    def __init__(self, config: AutograderConfiguration, sourceRoot, binRoot, version) -> None:
        self.config = config
        self.generationDirectory = os.path.join(binRoot, "generation")
        self.distDirectory = os.path.join(binRoot, "dist")
        self.binRoot = binRoot
        self.sourceDir = sourceRoot
        self.version = version

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

        This function recursively discovers the data files in the dataFilesSource.
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
            FilesEnum.CONFIG_FILE: [],
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

        files[FilesEnum.CONFIG_FILE] = [os.path.join(self.sourceDir, "config.toml")]

        return files

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
            except OSError:  # pragma: no coverage
                print("WARN: Failed to clean bin directory")  # pragma: no coverage

        # create directories
        os.makedirs(self.generationDirectory, exist_ok=True)
        os.makedirs(self.distDirectory, exist_ok=True)

    @staticmethod
    def createSetupForGradescope(path: str, version: str):
        with open(os.path.join(path, "setup.sh"), "w") as w:
            w.write(
                "add-apt-repository ppa:deadsnakes/ppa -y\n"
                "apt update\n"
                "apt-get install python3.12 -y\n"
                "apt-get install python3.12-venv -y\n"
                "python3.12 -m venv /autograder/.venv\n"
                "source /autograder/.venv/bin/activate\n"
                f"pip install 128Autograder=={version}\n"
            )

    @staticmethod
    def createRunFileForGradescope(path: str):
        with open(os.path.join(path, "run_autograder"), "w") as w:
            w.write(
                "#!/bin/bash\n"
                "source /autograder/.venv/bin/activate\n"
                "pushd source > /dev/null || echo 'Autograder failed to open source'\n"
                "run_gradescope\n"
                "popd > /dev/null || true\n"
            )

    @staticmethod
    def createRunForPrairieLearn(path: str):
        with open(os.path.join(path, "run_autograder"), "w") as w:
            w.write(
                "#!/bin/bash\n"
                "cd /grade > /dev/null || echo 'Autograder failed to open source'\n"
                "mkdir results\n"
                "echo '{}' > /grade/results/results.json\n"
                "run_prairielearn --config-file /grade/tests/config.toml\n"
            )

    @staticmethod
    def generateDocker(generationPath: str, platform, files: Dict[FilesEnum, List[str]], version: str,
                       setupFileGenerator: Callable[[str, str], None], runFileGenerator: Callable[[str], None]):
        generationPath = os.path.join(generationPath, "docker", platform)
        os.makedirs(generationPath, exist_ok=True)

        setupFileGenerator(generationPath, version)
        runFileGenerator(generationPath)

        for key, listOfFiles in files.items():
            if key is FilesEnum.STARTER_CODE:
                continue

            for file in listOfFiles:
                destPath = os.path.join(generationPath, file)
                os.makedirs(os.path.dirname(destPath), exist_ok=True)
                Build.copy(file, destPath)

    @staticmethod
    def generatePrairieLearn(generationPath: str, files: Dict[FilesEnum, List[str]], runFileGenerator: Callable[[str], None]):
        # autograder needs to be generated in the test folder as that is the only folder that PL will mount
        generationPath = os.path.join(generationPath, "prairielearn")
        sourcePath = os.path.join(generationPath, "tests")

        os.makedirs(generationPath, exist_ok=True)
        os.makedirs(sourcePath, exist_ok=True)

        runFileGenerator(sourcePath)

        for key, listOfFiles in files.items():
            if key is FilesEnum.STARTER_CODE:
                for file in listOfFiles:
                    destPath = os.path.join(generationPath, os.path.basename(file))
                    os.makedirs(os.path.dirname(destPath), exist_ok=True)
                    Build.copy(file, destPath)
                continue

            for file in listOfFiles:
                destPath = os.path.join(sourcePath, file)
                os.makedirs(os.path.dirname(destPath), exist_ok=True)
                Build.copy(file, destPath)



    @staticmethod
    def generateStudent(generationPath: str, files: Dict[FilesEnum, List[str]], studentWorkFolder: str):
        generationPath = os.path.join(generationPath, "student")
        os.makedirs(generationPath, exist_ok=True)

        # create student_work folder
        studentWorkFolder = os.path.join(generationPath, studentWorkFolder)
        os.makedirs(studentWorkFolder, exist_ok=True)

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

        for file in files[FilesEnum.CONFIG_FILE]:
            destPath = os.path.join(generationPath, os.path.basename(file))
            Build.copy(file, destPath)

        # create .keep so that we dont loose the file
        with open(os.path.join(studentWorkFolder, ".keep"), "w") as w:
            w.write("DO NOT WRITE YOUR CODE HERE!\nCreate a *new* file in this directory!!!")

    @staticmethod
    def createDist(distType: str, generationPath: str, distPath: str, assignmentName: str):
        generationPath = os.path.join(generationPath, distType)
        if not os.path.exists(generationPath) or not os.path.isdir(generationPath):
            raise AttributeError(f"Invalid generation path: {generationPath}")

        os.makedirs(distPath, exist_ok=True)

        assignmentName += f"-{'-'.join(distType.split('/'))}"
        distPath = os.path.join(distPath, assignmentName)

        shutil.make_archive(distPath, "zip", root_dir=generationPath)

    def build(self):
        files = self.discoverFiles()

        self.createFolders()

        if self.config.build.build_gradescope:
            self.generateDocker(self.generationDirectory, "gradescope", files, self.version,
                                self.createSetupForGradescope, self.createRunFileForGradescope)
            self.createDist("docker/gradescope", self.generationDirectory, self.distDirectory,
                            f"{self.config.semester}_{self.config.assignment_name}")
        if self.config.build.build_prairie_learn:
            # this build is a touch bigger than it needs to be, but for now I'm not super concerned about it
            self.generatePrairieLearn(self.generationDirectory,  files, self.createRunForPrairieLearn)
            self.createDist("prairielearn", self.generationDirectory, self.distDirectory,
                            f"{self.config.semester}_{self.config.assignment_name}")

        if self.config.build.build_student:
            self.generateStudent(self.generationDirectory, files,
                                 self.config.build.student_work_folder)
            self.createDist("student", self.generationDirectory, self.distDirectory,
                            f"{self.config.semester}_{self.config.assignment_name}")


class BuildAutograderCLI(AutograderCLITool):
    def __init__(self):
        super().__init__(f"Builder v{AutograderCLITool.get_version()}")

    def configure_options(self):
        self.parser.add_argument("--source", default=".", help="Autograder source root")
        self.parser.add_argument("-o", default="./bin", help="Output folder")

    def run(self) -> bool:
        self.configure_options()
        self.load_config()

        build = Build(self.config, self.arguments.source, self.arguments.o, self.get_version())

        build.build()

        return False

    def set_config_arguments(self, configBuilder: AutograderConfigurationBuilder[AutograderConfiguration]):
        pass


tool = BuildAutograderCLI().run

if __name__ == "__main__":
    res = tool()
    exit(res)
