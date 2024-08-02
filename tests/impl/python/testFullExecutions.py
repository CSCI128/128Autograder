import os
import shutil
import unittest

from Executors.Executor import Executor
from Executors.Environment import ExecutionEnvironmentBuilder, ExecutionEnvironment, getResults
from StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironment, PythonResults, PythonEnvironmentBuilder
from StudentSubmissionImpl.Python.PythonFileImportFactory import PythonFileImportFactory
from StudentSubmissionImpl.Python.PythonSubmission import PythonSubmission
from StudentSubmissionImpl.Python.Runners import PythonRunnerBuilder
from TestingFramework.SingleFunctionMock import SingleFunctionMock


# These serve as integration tests for the entire submission pipeline sans the gradescope stuff
class TestFullExecutions(unittest.TestCase):
    DATA_DIRECTORY: str = "./testData"
    TEST_FILE_NAME = "testFile.txt"
    OUTPUT_FILE_NAME = "outputFile.txt"

    PYTHON_PROGRAM_DIRECTORY: str = "./testPrograms"
    TEST_IMPORT_NAME = os.path.join(PYTHON_PROGRAM_DIRECTORY, "mod1.py")

    def setUp(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)
        os.mkdir(self.DATA_DIRECTORY)

        if os.path.exists(self.PYTHON_PROGRAM_DIRECTORY):
            shutil.rmtree(self.PYTHON_PROGRAM_DIRECTORY)

        os.mkdir(self.PYTHON_PROGRAM_DIRECTORY)

    def tearDown(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)

        if os.path.exists(ExecutionEnvironment.SANDBOX_LOCATION):
            shutil.rmtree(ExecutionEnvironment.SANDBOX_LOCATION)

        if os.path.exists(self.PYTHON_PROGRAM_DIRECTORY):
            shutil.rmtree(self.PYTHON_PROGRAM_DIRECTORY)

    @classmethod
    def writePythonFile(cls, filename, contents):
        path = os.path.join(cls.PYTHON_PROGRAM_DIRECTORY, filename)
        with open(path, 'w') as w:
            w.write(contents)

    def testFileIOFullExecution(self):
        # Because file io relies on the sandbox that the executor creates
        #  I am testing it as part of the executor tests

        expectedOutput = "this is a line in the file"
        program = \
            f"fileContents = None\n" \
            f"with open('{self.TEST_FILE_NAME}', 'r') as r:\n" \
            f"    fileContents = r.read()\n" \
            f"with open('{os.path.basename(self.OUTPUT_FILE_NAME)}', 'w') as w:\n" \
            f"     w.write(fileContents)\n"

        with open(os.path.join(self.DATA_DIRECTORY, self.TEST_FILE_NAME), 'w') as w:
            w.write(expectedOutput)

        self.writePythonFile("test_code.py", program)

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .enableLooseMainMatching() \
            .load() \
            .build() \
            .validate()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(module=True) \
            .build()

        environment = ExecutionEnvironmentBuilder() \
            .setDataRoot(self.DATA_DIRECTORY) \
            .addFile(self.TEST_FILE_NAME, self.TEST_FILE_NAME) \
            .build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).file_out[self.OUTPUT_FILE_NAME]

        self.assertEqual(expectedOutput, actualOutput)

    def testExecutorSetsParameters(self):
        program = \
            "def fun(param, *args):\n" \
            "    return (param, *args)"

        self.writePythonFile("test_code.py", program)

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .enableLooseMainMatching() \
            .load() \
            .build() \
            .validate()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(function="fun") \
            .addParameter(1) \
            .addParameter(2) \
            .addParameter(3) \
            .build()

        environment = ExecutionEnvironmentBuilder().build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).parameter

        self.assertEqual(3, len(actualOutput))
        self.assertEqual(3, actualOutput[2])

    def testImportFullExecution(self):
        expectedOutput = 10
        with open(self.TEST_IMPORT_NAME, 'w') as w:
            w.writelines("def fun1():\n"
                         f"  return {expectedOutput}\n"
                         "\n")
        with open(os.path.join(self.PYTHON_PROGRAM_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(
                "from mod1 import fun1\n" \
                "def run():\n" \
                "    return fun1()\n"
            )

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .load() \
            .build() \
            .validate()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(function="run") \
            .build()

        PythonFileImportFactory.registerFile(os.path.abspath(self.TEST_IMPORT_NAME), "mod1")

        importHandler = PythonFileImportFactory.buildImport()

        if importHandler is None:
            self.fail("This shouldn't happen")

        environment = ExecutionEnvironmentBuilder[PythonEnvironment, PythonResults]() \
            .setImplEnvironment(PythonEnvironmentBuilder, lambda x: x \
                                .addImportHandler(importHandler) \
                                .build()) \
            .build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).return_val

        self.assertEqual(expectedOutput, actualOutput)

    def testMockedImportFullExecution(self):
        # This test is flaky on windows - rerunning it helps.
        # It seems to be due to how windows implements the package cache when installing
        with open(os.path.join(self.PYTHON_PROGRAM_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(
                "import matplotlib.pyplot as plt\n" \
                "plt.plot([1, 2, 3, 4])\n" \
                "plt.plot('illegal!')\n"
            )

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .enableRequirements() \
            .addPackage("matplotlib") \
            .load() \
            .build() \
            .validate()

        plotMock = SingleFunctionMock("plot")

        environment = ExecutionEnvironmentBuilder[PythonEnvironment, PythonResults]() \
            .setTimeout(10) \
            .setImplEnvironment(PythonEnvironmentBuilder, lambda x: x \
                                .addModuleMock("matplotlib.pyplot", {"matplotlib.pyplot.plot": plotMock}) \
                                .build()
                                ) \
            .build()

        runner = PythonRunnerBuilder(submission) \
            .subscribeToMock("matplotlib.pyplot.plot") \
            .setEntrypoint(module=True) \
            .build()

        if environment.impl_environment is None:
            self.fail()

        Executor.execute(environment, runner)

        submission.TEST_ONLY_removeRequirements()

        actualOutput = getResults(environment).impl_results.mocks["matplotlib.pyplot.plot"]

        actualOutput.assertCalledWith([1, 2, 3, 4])
        actualOutput.assertCalledWith("illegal!")

    def testSpyImportFullExecution(self):
        # This test is flaky on windows - rerunning it helps.
        # It seems to be due to how windows implements the package cache when installing
        with open(os.path.join(self.PYTHON_PROGRAM_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(
                "import matplotlib.pyplot as plt\n" \
                "plt.plot([1, 2, 3, 4])\n" \
                "plt.savefig('out.png')"

            )

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .enableRequirements() \
            .addPackage("matplotlib") \
            .load() \
            .build() \
            .validate()

        plotMock = SingleFunctionMock("plot", spy=True)
        savefigMock = SingleFunctionMock("savefig", spy=True)

        environment = ExecutionEnvironmentBuilder[PythonEnvironment, PythonResults]() \
            .setTimeout(10) \
            .setImplEnvironment(PythonEnvironmentBuilder, lambda x: x \
                                .addModuleMock("matplotlib.pyplot", {"matplotlib.pyplot.plot": plotMock}) \
                                .addModuleMock("matplotlib.pyplot", {"matplotlib.pyplot.savefig": savefigMock}) \
                                .build()
                                ) \
            .build()

        runner = PythonRunnerBuilder(submission) \
            .subscribeToMock("matplotlib.pyplot.plot") \
            .subscribeToMock("matplotlib.pyplot.savefig") \
            .setEntrypoint(module=True) \
            .build()

        if environment.impl_environment is None:
            self.fail()

        Executor.execute(environment, runner)

        submission.TEST_ONLY_removeRequirements()

        plotResult = getResults(environment).impl_results.mocks["matplotlib.pyplot.plot"]
        saveFigResult = getResults(environment).impl_results.mocks["matplotlib.pyplot.savefig"]

        plotResult.assertCalledWith([1, 2, 3, 4])
        saveFigResult.assertCalled()

        actualFile = getResults(environment).file_out["out.png"]

        self.assertGreater(len(actualFile), 0)

    def testImportFullExecutionWithDataFiles(self):
        # Huge shout out to Nate T from F23 for finding this issue.
        # What a wild corner case

        expectedFileContents = "Called from a different file!!"
        testFileName = "test.txt"

        with open(self.TEST_IMPORT_NAME, 'w') as w:
            w.writelines("def fun1():\n"
                         f"  with open('{testFileName}', 'w') as w:\n"
                         f"    w.write('{expectedFileContents}')\n"
                         "\n")
        with open(os.path.join(self.PYTHON_PROGRAM_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(
                "from mod1 import fun1\n" \
                "fun1()\n"
            )

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .load() \
            .build() \
            .validate()

        PythonFileImportFactory.registerFile(os.path.abspath(self.TEST_IMPORT_NAME), "mod1")
        importHandler = PythonFileImportFactory.buildImport()

        if importHandler is None:
            self.fail("This shouldn't happen")

        environment = ExecutionEnvironmentBuilder[PythonEnvironment, PythonResults]() \
            .setImplEnvironment(PythonEnvironmentBuilder, lambda x: x \
                                .addImportHandler(importHandler) \
                                .build()) \
            .build()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(module=True) \
            .build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).file_out[testFileName]

        self.assertEqual(expectedFileContents, actualOutput)

    def testImportWithFunction(self):
        expectedOutput = 10
        program = \
            "from mod1 import fun1\n" \
            "def run():\n" \
            "    return fun1()\n"

        with open(self.TEST_IMPORT_NAME, 'w') as w:
            w.writelines(
                "def fun1():\n"
                f"  return {expectedOutput}"
                "\n"
            )

        self.writePythonFile("main.py", program)

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .load() \
            .build() \
            .validate()

        PythonFileImportFactory.registerFile(os.path.abspath(self.TEST_IMPORT_NAME), "mod1")
        PythonFileImportFactory.registerFile(os.path.abspath(os.path.join(self.PYTHON_PROGRAM_DIRECTORY, "main.py")),
                                             "main")
        importHandler = PythonFileImportFactory.buildImport()

        if importHandler is None:
            self.fail("This shouldn't happen")

        environment = ExecutionEnvironmentBuilder[PythonEnvironment, PythonResults]() \
            .setImplEnvironment(PythonEnvironmentBuilder, lambda x: x \
                                .addImportHandler(importHandler) \
                                .build()) \
            .build()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(function="run") \
            .build()

        Executor.execute(environment, runner)

        actualOutput = getResults(environment).return_val

        self.assertEqual(expectedOutput, actualOutput)

    def testExceptionRaisedResultPopulated(self):
        expectedOutput = "Huzzah"
        program = \
            f"print('OUTPUT {expectedOutput}')\n" \
            "raise Exception()"

        self.writePythonFile("test_code.py", program)

        submission = PythonSubmission() \
            .setSubmissionRoot(self.PYTHON_PROGRAM_DIRECTORY) \
            .enableLooseMainMatching() \
            .load() \
            .build() \
            .validate()

        environment = ExecutionEnvironmentBuilder() \
            .setTimeout(1000) \
            .build()

        runner = PythonRunnerBuilder(submission) \
            .setEntrypoint(module=True) \
            .build()

        with self.assertRaises(AssertionError):
            Executor.execute(environment, runner)

        stdout = getResults(environment).stdout
        exception = getResults(environment).exception

        self.assertEqual([expectedOutput], stdout)
        self.assertIsInstance(exception, Exception)
