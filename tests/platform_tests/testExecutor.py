import shutil
from typing import Optional, List
import unittest
import os
from unittest.mock import MagicMock

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.StudentSubmission.ISubmissionProcess import ISubmissionProcess
from autograder_platform.StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory
from autograder_platform.Executors.Executor import Executor
from autograder_platform.Executors.Environment import ExecutionEnvironment, Results
from autograder_platform.Tasks.Task import Task
from autograder_platform.Tasks.TaskRunner import TaskRunner
from autograder_platform.config.Config import AutograderConfigurationProvider


class MockSubmission(AbstractStudentSubmission[List[str]]):
    def __init__(self):
        super().__init__()
        self.studentCode: List[str] = ["No code"]

    def doLoad(self):
        self.studentCode += ["Loaded code!"]

    def doBuild(self):
        self.studentCode += ["Built code!"]

    def getExecutableSubmission(self) -> List[str]:
        return self.studentCode


class MockSubmissionProcess(ISubmissionProcess):
    def __init__(self):
        self.output: List[str] = []
        self.exceptions: Optional[Exception] = None
        self.runner: Optional[TaskRunner] = None

    def setup(self, _, runner: TaskRunner):
        self.runner = runner

    def run(self):
        if self.runner is None:
            return

        self.output = self.runner.run()

        if not self.runner.wasSuccessful():
            self.exceptions = self.runner.getAllErrors()[0]

    def populateResults(self, environment: ExecutionEnvironment):
        environment.resultData = Results()
        environment.resultData.stdout = self.output
        environment.resultData.exception = self.exceptions

    def cleanup(self):
        pass

    @classmethod
    def processAndRaiseExceptions(cls, environment: ExecutionEnvironment):
        if environment.resultData is None or environment.resultData.exception is not None:
            raise AssertionError()


class MockTaskLibrary:
    @staticmethod
    def loadSubmission(submission: List[str]) -> List[str]:
        return submission

    @staticmethod
    def returnBoi(data: object) -> object:
        return data

    @staticmethod
    def raiseException(exception: Exception):
        raise exception


SubmissionProcessFactory.register(MockSubmission, MockSubmissionProcess)


class TestExecutor(unittest.TestCase):
    TEST_FILE_ROOT = "./test_data"
    TEST_FILE_LOCATION = os.path.join(TEST_FILE_ROOT, "sub", "test.txt")
    OUTPUT_FILE_LOCATION = os.path.join(ExecutionEnvironment.sandbox_location,
                                        os.path.basename(TEST_FILE_LOCATION))

    def setUp(self) -> None:
        os.makedirs(os.path.dirname(self.TEST_FILE_LOCATION), exist_ok=True)

        self.submission = MockSubmission().build()
        self.environment = ExecutionEnvironment()
        self.runner = TaskRunner(MockSubmission)
        self.config = MagicMock()

    def tearDown(self) -> None:
        if os.path.exists(self.environment.sandbox_location):
            shutil.rmtree(self.environment.sandbox_location)

        if os.path.exists(self.TEST_FILE_ROOT):
            shutil.rmtree(self.TEST_FILE_ROOT)

    def testCreateSandbox(self):
        Executor.setup(self.environment, self.runner, self.config)

        self.assertIn(os.path.basename(self.environment.sandbox_location), os.listdir("."))

    def testMoveFiles(self):
        self.environment.files = {
            self.TEST_FILE_LOCATION: self.OUTPUT_FILE_LOCATION
        }

        with open(self.TEST_FILE_LOCATION, 'w') as w:
            w.write("this is a line in the file")

        Executor.setup(self.environment, self.runner, self.config)

        self.assertIn(os.path.basename(self.TEST_FILE_LOCATION), os.listdir(self.environment.sandbox_location))

    def testMoveFilesWithAlais(self):
        self.environment.files = {
            self.TEST_FILE_LOCATION:
                os.path.join(self.environment.sandbox_location, "this_is_alais.txt")
        }

        with open(self.TEST_FILE_LOCATION, 'w') as w:
            w.write("this is a line in the file")

        Executor.setup(self.environment, self.runner, self.config)

        self.assertIn("this_is_alais.txt", os.listdir(self.environment.sandbox_location))

    def testExceptionRaised(self):

        AutograderConfigurationProvider.set(MagicMock())

        self.runner.add(Task("raise_exception", MockTaskLibrary.raiseException, [lambda: Exception()]))

        with self.assertRaises(AssertionError):
            Executor.execute(self.environment, self.runner)

        AutograderConfigurationProvider.reset()

    def testSandboxNotCreatedCleanup(self):
        exception = None
        try:
            Executor.cleanup(self.environment)
        except Exception as e:
            exception = e

        self.assertIsNone(exception)

    def testSandboxCreatedAndCleanedUp(self):
        self.assertFalse(os.path.exists(self.environment.sandbox_location))
        Executor.setup(self.environment, self.runner, self.config)
        self.assertTrue(os.path.exists(self.environment.sandbox_location))
        Executor.cleanup(self.environment)
        self.assertFalse(os.path.exists(self.environment.sandbox_location))
