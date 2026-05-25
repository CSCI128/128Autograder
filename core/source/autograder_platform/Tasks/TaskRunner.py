from collections import deque
from typing import Dict, List, Optional, Type, Deque

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.Tasks.Task import Task
from autograder_platform.Tasks.common import TaskAlreadyExists, TaskDoesNotExist, TaskStatus


class TaskRunner:
    def __init__(self, submissionType: Type[AbstractStudentSubmission]):
        self.tasks: Dict[str, Task] = {}
        self.order: Deque[str] = deque()
        self.overallResultTask: Optional[str] = None
        self.errorOccurred = False
        self.submissionType: Type[AbstractStudentSubmission] = submissionType

    def add(self, task: Task, isOverallResultTask: bool = False):
        if task.getName() in self.tasks:
            raise TaskAlreadyExists(task.getName())

        self.tasks[task.getName()] = task
        self.order.append(task.getName())

        if isOverallResultTask:
            self.overallResultTask = task.getName()

    def getResult(self, taskName: str) -> object:
        if taskName not in self.tasks:
            raise TaskDoesNotExist(taskName)

        return self.tasks[taskName].getResult()


    def run(self) -> object:
        result: object = None
        while self.order:
            task: Task = self.tasks[self.order.popleft()]

            task.doTask()

            if task.getStatus() != TaskStatus.COMPLETE:
                self.errorOccurred = True
                break

            if task.getName() == self.overallResultTask:
                result = task.getResult()

        return result

    def wasSuccessful(self):
        return not self.order and not self.errorOccurred

    def getAllErrors(self) -> List[Exception]:
        errors: List[Exception] = []
        for task in self.tasks.values():
            error = task.getError()
            if error is None:
                continue

            errors.append(error)


        return errors

    def getSubmissionType(self) -> Type[AbstractStudentSubmission]:
        return self.submissionType

    def __getstate__(self):
        return {"tasks": self.tasks, "order": self.order, "overallResultTask": self.overallResultTask, "errorOccurred": self.errorOccurred}

    def __setstate__(self, state):
        self.tasks = state["tasks"]
        self.order = state["order"]
        self.overallResultTask = state["overallResultTask"]
        self.errorOccurred = state["errorOccurred"]
