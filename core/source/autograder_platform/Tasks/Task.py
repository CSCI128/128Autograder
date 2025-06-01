from typing import Callable, Final, List, Optional, Tuple
from autograder_platform.Tasks.common import TaskStatus, FailedToLoadSuppliers, AttemptToGetInvalidResults


class Task:
    def __init__(self, taskName: str, step: Callable[..., object], inputs: List[Callable[[], object]]):
        self.taskName: Final[str] = taskName
        self.step: Final[Callable[..., object]] = step
        self.inputs: Final[List[Callable[[], object]]] = inputs
        self.result: object = None
        self.status: TaskStatus = TaskStatus.NOT_STARTED
        self.error: Optional[Exception] = None

    def doTask(self):
        # TODO logging

        self.status = TaskStatus.RUNNING

        try:
            inputs: Tuple[object, ...] = tuple([getInput() for getInput in self.inputs])
        except Exception as ex:
            # TODO logging
            self.status = TaskStatus.ERROR
            self.error = FailedToLoadSuppliers(ex)
            return

        try:
            self.result = self.step(*inputs)
        except Exception as ex:
            # TODO logging
            self.status = TaskStatus.ERROR
            self.error = ex
            return

        self.status = TaskStatus.COMPLETE
        # TODO logging

    def getResult(self) -> object:
        if self.error or self.status != TaskStatus.COMPLETE:
            raise AttemptToGetInvalidResults()

        return self.result

    def getStatus(self) -> TaskStatus:
        return self.status

    def getName(self) -> str:
        return self.taskName

    def getError(self) -> Optional[Exception]:
        return self.error
