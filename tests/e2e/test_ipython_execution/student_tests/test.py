import unittest
from autograder_utils.Decorators import Weight, ImageResult

from autograder_platform.Executors.Executor import Executor
from autograder_platform.Executors.Environment import ExecutionEnvironmentBuilder, getResults, Results
from language_binds.ipython.source.autograder_binds.IPython import IPythonSubmission
from autograder_platform.StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironmentBuilder, PythonResults
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock
from autograder_platform.config.Config import AutograderConfigurationProvider
from autograder_platform.StudentSubmissionImpl.Python import PythonRunnerBuilder


class IPythonExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.autograderConfig = AutograderConfigurationProvider.get()

        cls.studentSubmission = IPythonSubmission() \
            .setSubmissionRoot(cls.autograderConfig.config.student_submission_directory) \
            .addPackages(cls.autograderConfig.config.python.extra_packages) \
            .enableHtmlTransformation()\
            .load() \
            .build() \
            .validate()

        plotMock = SingleFunctionMock("plot", spy=True)

        cls.environment = ExecutionEnvironmentBuilder() \
            .setTimeout(20) \
            .setImplEnvironment(
            PythonEnvironmentBuilder,
            lambda x: x \
                .addModuleMock("matplotlib.pyplot", {"matplotlib.pyplot.plot": plotMock}) \
                .build()) \
            .build()

    @Weight(5)
    @ImageResult()
    def testRunPlot(self, encode_image_data=None, set_image_data=None):
        self.studentSubmission.setActiveCell("plot")

        runner = PythonRunnerBuilder(self.studentSubmission) \
            .subscribeToMock("matplotlib.pyplot.plot") \
            .setEntrypoint(module=True) \
            .build()

        Executor.execute(self.environment, runner)

        res: Results[PythonResults] = getResults(self.environment)

        imageData = encode_image_data(res.file_out["fig_1.png"])

        set_image_data("Plot", imageData)

        plotMock = res.impl_results.mocks["matplotlib.pyplot.plot"]

        plotMock.assertCalled()


    @Weight(5)
    def testProvidedData(self):
        self.studentSubmission.setActiveCell("generate_range")
        runner = PythonRunnerBuilder(self.studentSubmission) \
            .setEntrypoint(function="generateRange") \
            .addParameter(5) \
            .addParameter(6) \
            .addParameter(5) \
            .addParameter(6) \
            .build()

        Executor.execute(self.environment, runner)

        x, y = getResults(self.environment).return_val

        self.assertEqual(1, len(x))
        self.assertEqual(1, len(y))


    @Weight(0)
    def testShowEntireHTML(self):
        print(self.studentSubmission.getNotebookHtml())
