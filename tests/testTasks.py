import unittest
from Tasks.Task import Task
from Tasks.TaskRunner import TaskRunner
from Tasks.common import TaskStatus, FailedToLoadSuppliers, TaskAlreadyExists


class TestTasks(unittest.TestCase):
    @staticmethod
    def returnBoi(data: object) -> object:
        return data

    @staticmethod
    def raiseBoi():
        raise AttributeError("Raise boi has spoken")

    def testTasksPopulateResults(self):
        expected = 3
        task = Task("Get data", TestTasks.returnBoi, [lambda: expected])

        task.doTask()

        actual = task.getResult()

        self.assertEqual(expected, actual)
        self.assertEqual(TaskStatus.COMPLETE, task.getStatus())

    def testExceptionSetTask(self):
        task = Task("Get data", TestTasks.raiseBoi, [])
        task.doTask()

        self.assertEqual(TaskStatus.ERROR, task.getStatus())

        with self.assertRaises(AttributeError):
            raise task.getError()

    def testExceptionSetSupplier(self):
        task = Task("Get data", TestTasks.returnBoi, [TestTasks.raiseBoi])
        task.doTask()

        self.assertEqual(TaskStatus.ERROR, task.getStatus())

        with self.assertRaises(FailedToLoadSuppliers):
            raise task.getError()

    def testTasksGetResultsFromPrevTask(self):
        expected = 3

        runner = TaskRunner()

        runner.add(Task("1", TestTasks.returnBoi, [lambda: expected]))
        runner.add(Task("2", TestTasks.returnBoi, [lambda: runner.getResult("1")]), isOverallResultTask=True)

        actual = runner.run()

        self.assertEqual(expected, actual)


    def testOnlyOneTaskPerName(self):
        expected = 3

        runner = TaskRunner()
        with self.assertRaises(TaskAlreadyExists):
            runner.add(Task("1", TestTasks.returnBoi, [lambda: expected]))
            runner.add(Task("1", TestTasks.returnBoi, [lambda: runner.getResult("1")]))

    def testTasksMustBeCompleted(self):
        expected = 3

        runner = TaskRunner()
        runner.add(Task("1", TestTasks.returnBoi, [lambda: runner.getResult("1")]), isOverallResultTask=True)

        actual = runner.run()

        self.assertEqual(None, actual)
        self.assertFalse(runner.wasSuccessful())
        self.assertEqual(1, len(runner.getAllErrors()))
