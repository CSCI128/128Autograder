from importlib import import_module
import os
import shutil
import sys
from typing import Dict, Optional
import unittest
from StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironment

from StudentSubmissionImpl.Python.PythonSubmissionProcess import RunnableStudentSubmission
from Executors.Environment import PossibleResults
from StudentSubmissionImpl.Python.PythonRunners import MainModuleRunner, FunctionRunner
from Executors.Environment import ExecutionEnvironment
from TestingFramework.SingleFunctionMock import SingleFunctionMock
from StudentSubmission.common import MissingFunctionDefinition, InvalidTestCaseSetupCode
from Executors.common import MissingOutputDataException
from StudentSubmissionImpl.Python.PythonModuleMockImportFactory import ModuleFinder


class TestPythonSubmissionProcess(unittest.TestCase):
    def setUp(self):
        self.environment = ExecutionEnvironment(None) # type: ignore
        self.environment.SANDBOX_LOCATION = "."
        self.runnableSubmission = RunnableStudentSubmission()

    def testStdIO(self):
        program = \
             "\n"\
             "userIn = input()\n"\
             "print('OUTPUT', userIn)\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.stdin = ["this is input"]

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(self.environment.stdin, results[PossibleResults.STDOUT])

    def testStdIOWithMain(self):
        program = \
            "if __name__ == '__main__':\n" \
            "   userIn = input()\n" \
            "   print('OUTPUT', userIn)\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.stdin = ["this is input"]

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(self.environment.stdin, results[PossibleResults.STDOUT])

    def testFunctionStdIO(self):
        program = \
             "def runMe():\n"\
             "  userIn = input()\n"\
             "  print('OUTPUT', userIn)\n"

        runner = FunctionRunner("runMe")
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(self.environment.stdin, results[PossibleResults.STDOUT])

    def testFunctionParameterStdIO(self):
        program = \
             "def runMe(value: str):\n"\
             "  print('OUTPUT', value)\n"

        strInput = "this was passed as a parameter"

        runner = FunctionRunner("runMe")

        runner.setSubmission(compile(program, "test_code", "exec"))
        runner.setParameters((strInput,))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual([strInput], results[PossibleResults.STDOUT])

    def testFunctionParameterReturn(self):
        program = \
             "def runMe(value: int):\n"\
             "  return value\n"

        intInput = 128
        runner = FunctionRunner("runMe")
        runner.setSubmission(compile(program, "test_code", "exec"))
        runner.setParameters((intInput,))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(intInput, results[PossibleResults.RETURN_VAL])
        self.assertEqual(intInput, results[PossibleResults.PARAMETERS][0])

    def testFunctionMock(self):
        program = \
                "def mockMe(parm1, parm2, parm3):\n"\
                "   pass\n"\
                "\n"\
                "def runMe():\n"\
                "   mockMe(1, 2, 3)\n"\
                "   mockMe(1, 2, 3)\n"\

        runner = FunctionRunner("runMe")
        runner.setSubmission(compile(program, "test_code", "exec"))
        runner.setMocks({"mockMe": SingleFunctionMock("mockMe", None)})

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        mockMeMock: SingleFunctionMock = results[PossibleResults.MOCK_SIDE_EFFECTS]["mockMe"]

        mockMeMock.assertCalledWith(1, 2, 3)
        mockMeMock.assertCalledTimes(2)

    def testFunctionSpy(self):
        program = \
            "def mockMe(a, b, c):\n"\
            "    return a + b + c\n"

        runner = FunctionRunner("mockMe")
        mocks: Dict[str, Optional[SingleFunctionMock]] = {"mockMe": SingleFunctionMock("mockMe", spy=True)}

        runner.setMocks(mocks)
        runner.setParameters((1, 2, 3))
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData
        mockMeMock: SingleFunctionMock = results[PossibleResults.MOCK_SIDE_EFFECTS]["mockMe"]
        returnVal = results[PossibleResults.RETURN_VAL]

        self.assertEqual(6, returnVal)
        mockMeMock.assertCalledTimes(1)

    def testMissingFunctionDeclaration(self):
        program = \
                "def ignoreMe():\n"\
                "   return True\n"

        runner = FunctionRunner("runMe")
        runner.setSubmission(compile(program, "test_code", "exec"))
        self.environment.timeout = 10000

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(MissingFunctionDefinition) as ex:
            raise results[PossibleResults.EXCEPTION]

        exceptionText = str(ex.exception)

        self.assertIn("missing the function definition", exceptionText)
        self.assertEqual(exceptionText.count("missing the function definition"), 1)

    def testTerminateInfiniteLoop(self):
        program = \
                "while True:\n"\
                "   print('OUTPUT LOOP:)')\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.timeout = 5

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(TimeoutError):
            raise results[PossibleResults.EXCEPTION]

        self.assertNotIn(PossibleResults.STDOUT, results)

    def testTerminateInfiniteLoopWithInput(self):
        program = \
                "import time\n"\
                "while True:\n"\
                "   time.sleep(.25)\n"\
                "   var = input()\n"\
                "   print(var)\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.stdin = str("hello\n" * 9999).splitlines()
        self.environment.timeout = 5

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(TimeoutError):
            raise results[PossibleResults.EXCEPTION] # type: ignore

        self.assertNotIn(PossibleResults.STDOUT, results)

    def testCorrectTimeoutError(self):
        program = \
                "while True:\n"\
                "   print('OUTPUT LOOP:)')\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.timeout = 5

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(TimeoutError) as ex:
            raise results[PossibleResults.EXCEPTION]
        
        exceptionText = str(ex.exception)
        self.assertIn("timed out after 5 seconds", exceptionText)

        self.assertNotIn(PossibleResults.STDOUT, results)

    def testHandledExceptionInfiniteRecursion(self):
        program = \
                "def loop():\n"\
                "   print('OUTPUT RECURSION')\n"\
                "   loop()\n"\
                "loop()\n"

        self.environment.timeout = 5

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(RecursionError):
            raise results[PossibleResults.EXCEPTION]

        # Make sure that data is still populated even when we have an error
        self.assertIn(PossibleResults.STDOUT, results)
        self.assertTrue(len(results[PossibleResults.STDOUT]) > 10)

    def testHandledExceptionBlockedInput(self):
        program = \
                "var1 = input()\n"\
                "var2 = input()\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.environment.stdin = ["1"]

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        with self.assertRaises(AssertionError) as ex:
            self.runnableSubmission.processAndRaiseExceptions(self.environment)

        exceptionText = str(ex.exception)

        self.assertIn("missing if __name__ == '__main__'", exceptionText)

    def testHandleExit(self):
        program = \
                "exit(0)"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(MissingOutputDataException):
            raise results[PossibleResults.EXCEPTION]

    def testHandleManyFailedRuns(self):
        # This test enforces that we prefer a resource leak to crashing tests
        # This might need to be re-evaluated in the future
        program = "print('Hi Mom!')\n"

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

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
            "def test():\n" \
            "    random.seed('autograder')\n" \
            "    return random.randint(0, 5)\n"

        runner = FunctionRunner("test")
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertIsNone(results[PossibleResults.EXCEPTION])

        self.assertEqual(4, results[PossibleResults.RETURN_VAL])

    def testRunFunctionSetupCode(self):
        program = \
            "import random\n" \
            "def test():\n" \
            "   return random.randint(0, 5)\n"

        setup = \
            "def autograder_setup():\n" \
            "   random.seed('autograder')\n"

        runner = FunctionRunner("test")
        runner.setSubmission(compile(program, "test_code", "exec"))
        runner.setSetupCode(setup)

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(4, results[PossibleResults.RETURN_VAL])

    def testBadFunctionSetupCode(self):
        program = \
            "def test():\n" \
            "   pass\n"

        setup = \
            "def this_is_a_bad_name():\n" \
            "   pass\n"

        runner = FunctionRunner("test")
        runner.setSubmission(compile(program, "test_code", "exec"))
        runner.setSetupCode(setup)

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        with self.assertRaises(InvalidTestCaseSetupCode):
            raise results[PossibleResults.EXCEPTION]

    @unittest.expectedFailure
    def testMockImportedFunction(self):
        program = \
            "import random\n" \
            "def test():\n" \
            "   return random.randint(10, 15)\n"

        runner = FunctionRunner("test")
        runner.setSubmission(compile(program, "test_code", "exec"))
        randIntMock = SingleFunctionMock("randint", [1])
        self.environment.timeout = 10000

        randMod = import_module("random")
        trueRandInt = getattr(randMod, "randint")

        setattr(randMod, "randint", randIntMock)

        runner.setMocks({"random.randint": None})

        self.environment.impl_environment = PythonEnvironment()

        self.environment.impl_environment.import_loader.append(ModuleFinder("random", randMod))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        setattr(randMod, "randint", trueRandInt)

        self.assertEqual(1, results[PossibleResults.RETURN_VAL])

    def testFunctionCallsOtherFunction(self):
        program = \
            "def test1():\n" \
            "   return test2('hello from test2')\n" \
            "\n" \
            "def test2(var):\n" \
            "   return var\n"

        runner = FunctionRunner("test1")
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertIsNone(results[PossibleResults.EXCEPTION])
        self.assertEqual("hello from test2", results[PossibleResults.RETURN_VAL])
    
    def testFunctionMutableParameters(self):
        program = \
            "def test1(lst):\n"\
            "   lst.append(1)\n"

        listToUpdate = [0]
        runner = FunctionRunner("test1")
        runner.setParameters((listToUpdate,))

        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        self.assertEqual(len(results[PossibleResults.PARAMETERS][0]), 2)
        self.assertIn(1, results[PossibleResults.PARAMETERS][0])

    def testFindNewFiles(self):
        program = "pass"

        self.environment.SANDBOX_LOCATION = "./sandbox"
        os.mkdir(self.environment.SANDBOX_LOCATION)

        fileLocation = os.path.join(self.environment.SANDBOX_LOCATION, "file.txt")

        with open(fileLocation, 'w') as w:
            w.write("this is a line in the file")

        runner = MainModuleRunner()
        runner.setSubmission(compile(program, "test_code", "exec"))

        self.runnableSubmission.setup(self.environment, runner)
        self.runnableSubmission.run()
        self.runnableSubmission.cleanup()

        self.runnableSubmission.populateResults(self.environment)

        results = self.environment.resultData

        shutil.rmtree(self.environment.SANDBOX_LOCATION)

        self.assertIn(PossibleResults.FILE_OUT, results)
        self.assertDictEqual({os.path.basename(fileLocation): fileLocation}, results[PossibleResults.FILE_OUT])

