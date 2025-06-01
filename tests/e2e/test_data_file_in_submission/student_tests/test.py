import unittest
import os
from autograder_utils.Decorators import Weight

from autograder_platform.Executors.Executor import Executor
from autograder_platform.Executors.Environment import ExecutionEnvironmentBuilder, getResults
from autograder_platform.StudentSubmissionImpl.Python import PythonSubmission
from autograder_platform.config.Config import AutograderConfigurationProvider
from autograder_platform.StudentSubmissionImpl.Python import PythonRunnerBuilder


class DataFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.autograderConfig = AutograderConfigurationProvider.get()

        cls.studentSubmission = PythonSubmission()\
                .setSubmissionRoot(cls.autograderConfig.config.student_submission_directory)\
                .load()\
                .build()\
                .validate()

    def setUp(self) -> None:
        submissionDirectory = self.autograderConfig.config.student_submission_directory
        testFolder = os.path.join("autograder", "source", self.autograderConfig.config.test_directory, "data")

        self.environmentBuilder = ExecutionEnvironmentBuilder()\
                .setDataRoot("/")\
                .addFile(os.path.join(submissionDirectory, "file.dat"), "file.dat")\
                .addFile(os.path.join(testFolder, "public_file.dat"), "public_file.dat")


    @Weight(5)
    def testSubmissionData(self):
        runner = PythonRunnerBuilder(self.studentSubmission)\
            .setEntrypoint(function="readFile")\
            .addParameter("file.dat")\
            .build()

        environment = self.environmentBuilder.build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).return_val

        self.assertEqual("file.dat", actualOutput)

    @Weight(5)
    def testProvidedData(self):
        runner = PythonRunnerBuilder(self.studentSubmission) \
            .setEntrypoint(function="readFile") \
            .addParameter("public_file.dat") \
            .build()

        environment = self.environmentBuilder.build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).return_val

        self.assertEqual("public_file.dat", actualOutput)
