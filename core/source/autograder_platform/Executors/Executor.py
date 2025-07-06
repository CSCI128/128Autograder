import shutil
import os
import sys
from typing import Dict

from autograder_platform.Executors.Environment import ExecutionEnvironment

from autograder_platform.StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory
from autograder_platform.Tasks.TaskRunner import TaskRunner
from autograder_platform.config.Config import AutograderConfigurationProvider, AutograderConfiguration

# For typing only
from autograder_platform.StudentSubmission.ISubmissionProcess import ISubmissionProcess


class Executor:
    @staticmethod
    def _copyFiles(files: Dict[str, str]):
        for src, dest in files.items():
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(src, dest)
            except OSError as ex:  # pragma: no coverage
                raise EnvironmentError(f"Failed to move file '{src}' to '{dest}'. Error is: {ex}")  # pragma: no coverage

    @classmethod
    def setup(cls, environment: ExecutionEnvironment, runner: TaskRunner, autograderConfig: AutograderConfiguration) -> ISubmissionProcess:
        if not os.path.exists(environment.sandbox_location):
            try:
                os.mkdir(environment.sandbox_location)
            except OSError as ex:  # pragma: no coverage
                raise EnvironmentError(f"Failed to create sandbox for test run. Error is: {ex}")  # pragma: no coverage

        # TODO Logging

        process = SubmissionProcessFactory.createProcess(environment, runner, autograderConfig)

        if environment.files:
            Executor._copyFiles(environment.files)

        return process
        
    @classmethod
    def execute(cls, environment: ExecutionEnvironment, runner: TaskRunner, raiseExceptions: bool = True) -> None:
        submissionProcess: ISubmissionProcess = cls.setup(environment, runner, AutograderConfigurationProvider.get())

        submissionProcess.run()

        cls.postRun(environment, submissionProcess, raiseExceptions)

    @classmethod
    def postRun(cls, environment: ExecutionEnvironment, 
                submissionProcess: ISubmissionProcess, raiseExceptions: bool) -> None:

        submissionProcess.cleanup()

        submissionProcess.populateResults(environment)

        if raiseExceptions:
            # Moving this into the actual submission process allows for each process type to
            # handle their exceptions differently
            submissionProcess.processAndRaiseExceptions(environment)


    @classmethod
    def cleanup(cls, environment: ExecutionEnvironment):
        if os.path.exists(environment.sandbox_location):
            try:
                shutil.rmtree(environment.sandbox_location)
            except OSError:  # pragma: no coverage
                pass
