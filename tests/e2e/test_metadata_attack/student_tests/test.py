import unittest
from autograder_utils.Decorators import Weight, ImageResult

from autograder_platform.Executors.Executor import Executor
from autograder_platform.Executors.Environment import ExecutionEnvironmentBuilder, getResults
from autograder_platform.StudentSubmissionImpl.Python import PythonSubmission
from autograder_platform.config.Config import AutograderConfigurationProvider
from autograder_platform.StudentSubmissionImpl.Python.Runners import PythonRunnerBuilder

class RequirementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.autograderConfig = AutograderConfigurationProvider.get()

        cls.studentSubmission = PythonSubmission()\
                .setSubmissionRoot(cls.autograderConfig.config.student_submission_directory)\
                .load()\
                .build()\
                .validate()

    def setUp(self) -> None:
        self.environmentBuilder = ExecutionEnvironmentBuilder()

    @Weight(10)
    @ImageResult()
    def testCode(self, encode_image_data=None, set_image_data=None):
        environment = self.environmentBuilder.build()

        runner = PythonRunnerBuilder(self.studentSubmission)\
            .setEntrypoint(module=True)\
            .build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).stdout

        self.assertEqual(1, len(actualOutput))

        imageData = encode_image_data(getResults(environment).file_out["plt.png"])

        set_image_data("Plot", imageData)
