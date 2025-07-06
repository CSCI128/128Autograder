import abc
from autograder_platform.Executors.Environment import ExecutionEnvironment

from autograder_platform.Tasks.TaskRunner import TaskRunner


class ISubmissionProcess(abc.ABC):
    @abc.abstractmethod
    def setup(self, environment: ExecutionEnvironment, runner: TaskRunner):
        pass

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def populateResults(self, environment: ExecutionEnvironment):
        pass

    @abc.abstractmethod
    def cleanup(self):
        pass

    @classmethod
    @abc.abstractmethod
    def processAndRaiseExceptions(cls, environment: ExecutionEnvironment):
        pass
