import shutil
from importlib import import_module
import os
import unittest

from autograder_platform.StudentSubmissionImpl.Python import PythonSubmission
from autograder_platform.StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironment, PythonResults

from autograder_platform.StudentSubmissionImpl.Python.PythonSubmissionProcess import RunnableStudentSubmission
from autograder_platform.Executors.Environment import ExecutionEnvironment, Results, getResults
from autograder_platform.StudentSubmissionImpl.Python.Runners import PythonRunnerBuilder, Parameter
from autograder_platform.Tasks.TaskRunner import TaskRunner
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock
from autograder_platform.StudentSubmission.common import MissingFunctionDefinition
from autograder_platform.Executors.common import MissingOutputDataException
from autograder_platform.StudentSubmissionImpl.Python.PythonModuleMockImportFactory import MockedModuleFinder


class TestPythonSubmissionProcess(unittest.TestCase):
    def setUp(self):
        self.environment = ExecutionEnvironment()
        self.environment.sandbox_location = "."
        self.environment.impl_environment = PythonEnvironment()
        self.runnableSubmission = RunnableStudentSubmission()
        self.submission: PythonSubmission = PythonSubmission()

    def runSubmission(self, runner: TaskRunner) -> Results:
        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = getResults(self.environment)

        return results

    def testStdIO(self):
        program = \
             "\n"\
             "userIn = input()\n"\
             "print('OUTPUT', userIn)\n"


        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(module=True)\
            .build()

        self.environment.stdin = ["this is input"]
        self.environment.timeout = 3600

        results = self.runSubmission(runner)

        self.assertEqual(self.environment.stdin, results.stdout)

    def testStdIOWithMain(self):
        program = \
            "if __name__ == '__main__':\n" \
            "   userIn = input()\n" \
            "   print('OUTPUT', userIn)\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        self.environment.stdin = ["this is input"]

        results = self.runSubmission(runner)

        self.assertEqual(self.environment.stdin, results.stdout)

    def testFunctionStdIO(self):
        program = \
             "def runMe():\n"\
             "  userIn = input()\n"\
             "  print('OUTPUT', userIn)\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(function="runMe")\
            .build()

        self.environment.stdin = ["this is input"]

        results = self.runSubmission(runner)

        self.assertEqual(self.environment.stdin, results.stdout)

    def testFunctionParameterStdIO(self):
        program = \
             "def runMe(value: str):\n"\
             "  print('OUTPUT', value)\n"

        strInput = "this was passed as a parameter"
        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .addParameter(strInput)\
            .build()

        results = self.runSubmission(runner)

        self.assertEqual([strInput], results.stdout)

    def testFunctionParameterReturn(self):
        program = \
             "def runMe(value: int):\n"\
             "  return value\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        intInput = 128

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .addParameter(intInput) \
            .build()

        results = self.runSubmission(runner)

        self.assertEqual(intInput, results.return_val)
        self.assertEqual(intInput, results.parameter[0])

    def testFunctionMock(self):
        program = \
                "def mockMe(parm1, parm2, parm3):\n"\
                "   pass\n"\
                "\n"\
                "def runMe():\n"\
                "   mockMe(1, 2, 3)\n"\
                "   mockMe(1, 2, 3)\n"\

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .addMock("mockMe", SingleFunctionMock("mockMe", None))\
            .build()

        results: Results[PythonResults] = self.runSubmission(runner)

        mockMeMock = results.impl_results.mocks["mockMe"]

        mockMeMock.assertCalledWith(1, 2, 3)
        mockMeMock.assertCalledTimes(2)

    def testFunctionSpy(self):
        program = \
            "def mockMe(a, b, c):\n"\
            "    return a + b + c\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="mockMe") \
            .addParameter(1) \
            .addParameter(2) \
            .addParameter(3)\
            .addMock("mockMe", SingleFunctionMock("mockMe", spy=True)) \
            .build()


        results: Results[PythonResults] = self.runSubmission(runner)

        self.assertIsNone(results.exception)

        mockMeMock = results.impl_results.mocks["mockMe"]
        returnVal = results.return_val

        self.assertEqual(6, returnVal)
        mockMeMock.assertCalledTimes(1)

    def testMissingFunctionDeclaration(self):
        program = \
                "def ignoreMe():\n"\
                "   return True\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(function="runMe")\
            .build()

        self.environment.timeout = 10000

        results: Results[PythonResults] = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(MissingFunctionDefinition) as ex:
            raise results.exception

        exceptionText = str(ex.exception)

        self.assertIn("missing the function definition", exceptionText)
        self.assertEqual(exceptionText.count("missing the function definition"), 1)

    def testTerminateInfiniteLoop(self):
        program = \
                "while True:\n"\
                "   print('OUTPUT LOOP:)')\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        self.environment.timeout = 5

        results: Results = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(TimeoutError) as ex:
            raise results.exception

        res = None
        with self.assertRaises(AssertionError):
            res = results.stdout

        exceptionText = str(ex.exception)
        self.assertIn("timed out after 5 seconds", exceptionText)


        self.assertIsNone(res)

    def testTerminateInfiniteLoopWithInput(self):
        program = \
                "import time\n"\
                "while True:\n"\
                "   time.sleep(.25)\n"\
                "   var = input()\n"\
                "   print(var)\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        self.environment.stdin = str("hello\n" * 9999).splitlines()
        self.environment.timeout = 5

        results: Results = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(TimeoutError):
            raise results.exception

        res = None
        with self.assertRaises(AssertionError):
            res = results.stdout

        self.assertIsNone(res)


    def testHandledExceptionInfiniteRecursion(self):
        program = \
                "def loop():\n"\
                "   print('OUTPUT RECURSION')\n"\
                "   loop()\n"\
                "loop()\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        self.environment.timeout = 5

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        results: Results = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(RecursionError):
            raise results.exception

        # Make sure that data is still populated even when we have an error
        self.assertTrue(len(results.stdout) > 10)

    def testHandledExceptionBlockedInput(self):
        program = \
                "var1 = input()\n"\
                "var2 = input()\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        self.environment.stdin = ["1"]

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        with self.assertRaises(AssertionError) as ex:
            self.runnableSubmission.processAndRaiseExceptions(self.environment)

        exceptionText = str(ex.exception)

        self.assertIn("Do you have the correct number of input statements?", exceptionText)

    def testHandleExit(self):
        program = \
                "exit(0)"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        results: Results = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(MissingOutputDataException):
            raise results.exception

    def testHandleManyFailedRuns(self):
        # This test enforces that we prefer a resource leak to crashing tests
        # This might need to be re-evaluated in the future
        program = "print('Hi Mom!')\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        runnableSubmission = RunnableStudentSubmission()
        runnableSubmission.setup(self.environment, runner)
        runnableSubmission.run()
        memToDeallocate = runnableSubmission.inputSharedMem, runnableSubmission.outputSharedMem

        runnableSubmission.setup(self.environment, runner)
        runnableSubmission.run()
        runnableSubmission.cleanup()
        
        if memToDeallocate[0] is None or memToDeallocate[1] is None:
            return

        memToDeallocate[0].close(); memToDeallocate[0].unlink()
        memToDeallocate[1].close(); memToDeallocate[1].unlink()

    def testImportedFunction(self):
        program = \
            "import random\n" \
            "def runMe():\n" \
            "    random.seed('autograder')\n" \
            "    return random.randint(0, 5)\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .build()

        results: Results = self.runSubmission(runner)

        self.assertIsNone(results.exception)
        self.assertEqual(4, results.return_val)

    def testRunFunctionSetupCode(self):
        program = \
            "import random\n" \
            "def test():\n" \
            "   return random.randint(0, 5)\n"

        setup = \
            "def INJECTED_autograder_setup():\n" \
            "   random.seed('autograder')\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(function="test")\
            .addInjectedCode("INJECTED_autograder_setup", src=setup)\
            .addSetupMethod("INJECTED_autograder_setup")\
            .build()


        results: Results = self.runSubmission(runner)

        self.assertIsNone(results.exception)

        self.assertEqual(4, results.return_val)

    def testBadFunctionSetupCode(self):
        program = \
            "def test():\n" \
            "   pass\n"

        setup = \
            "def this_is_a_bad_name():\n" \
            "   pass\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="test") \
            .addInjectedCode("INJECTED_autograder_setup", src=setup) \
            .addSetupMethod("INJECTED_autograder_setup") \
            .build()

        results: Results = self.runSubmission(runner)

        if results.exception is None:
            self.fail("Exception was None when should derive from BaseException")

        with self.assertRaises(MissingFunctionDefinition):
            raise results.exception

    def testMockImportedFunction(self):
        program = \
            "import random\n" \
            "def runMe():\n" \
            "   return random.randint(10, 15)\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .build()

        self.environment.timeout = 5

        randMod = import_module("random")
        randIntMock = SingleFunctionMock("randint", [1])

        self.environment.impl_environment = PythonEnvironment()

        self.environment.impl_environment.import_loader.append(MockedModuleFinder("random", randMod, {"randint": randIntMock}))

        results: Results = self.runSubmission(runner)

        self.assertEqual(1, results.return_val)

    def testFunctionCallsOtherFunction(self):
        program = \
            "def test1():\n" \
            "   return test2('hello from test2')\n" \
            "\n" \
            "def test2(var):\n" \
            "   return var\n"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(function="test1")\
            .build()

        results: Results = self.runSubmission(runner)

        self.assertIsNone(results.exception)
        self.assertEqual("hello from test2", results.return_val)
    
    def testFunctionMutableParameters(self):
        program = \
            "def runMe(lst):\n"\
            "   lst.append(1)\n"

        listToUpdate = [0]
        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission)\
            .setEntrypoint(function="runMe")\
            .addParameter(listToUpdate)\
            .build()

        results: Results = self.runSubmission(runner)

        self.assertEqual(len(results.parameter[0]), 2)
        self.assertIn(1, results.parameter[0])

    def testFindNewFiles(self):
        program = "pass"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        self.environment.sandbox_location = "./sandbox"

        if os.path.exists(self.environment.sandbox_location):
            shutil.rmtree(self.environment.sandbox_location)

        os.mkdir(self.environment.sandbox_location)

        fileLocation = os.path.join(self.environment.sandbox_location, "file.txt")

        with open(fileLocation, 'w') as w:
            w.write("this is a line in the file")

        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(module=True) \
            .build()

        results: Results = self.runSubmission(runner)

        self.assertIsNotNone(results.file_out[os.path.basename(fileLocation)])


    def testAutowiringExists(self):
        expected = 3
        program = \
            "def autowireMe(val):\n"\
            "   return val\n\n"\
            "def runMe(funToCall):\n"\
            f"   return funToCall({expected})"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .addParameter(parameter=Parameter(autowiredName="autowireMe")) \
            .build()

        results: Results = self.runSubmission(runner)

        self.assertEqual(expected, results.return_val)

    def testAutowiringDoesNotExist(self):
        expected = 3
        program = \
            "def runMe(funToCall):\n" \
            f"   return funToCall({expected})"

        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .addParameter(parameter=Parameter(autowiredName="autowireMe")) \
            .build()

        results: Results = self.runSubmission(runner)

        self.assertIsNotNone(results.exception)

        with self.assertRaises(RuntimeError) as ex:
            raise results.exception

        exceptionText = str(ex.exception)

        self.assertIn("Failed to map 'autowireMe'", exceptionText)

    def testOverrunDataBuffer(self):
        program = \
            "def runMe():" \
            f"   return bytearray({self.environment.impl_environment.buffer_size + 1})"


        self.submission.getExecutableSubmission = lambda: compile(program, "test_code", "exec")
        runner = PythonRunnerBuilder(self.submission) \
            .setEntrypoint(function="runMe") \
            .build()

        results: Results = self.runSubmission(runner)

        self.assertIsNotNone(results.exception)

        with self.assertRaises(MissingOutputDataException):
            raise results.exception

