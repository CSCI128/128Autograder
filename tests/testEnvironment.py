import os
import shutil
from sys import stdout
import unittest

from StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from Executors.Environment import ExecutionEnvironment, ExecutionEnvironmentBuilder, Results, getResults

class MockSubmission(AbstractStudentSubmission[str]):
    def __init__(self):
        super().__init__()
        

    def doLoad(self):
       pass

    def doBuild(self):
        pass

    def getExecutableSubmission(self) -> str:
        return "Code!"


class TestEnvironmentBuilder(unittest.TestCase):
    # For builds, we are only testing the non-trival functions and the non trivial cases
    # Its just not really valuable to have assertions on one line functions imo
    DATA_ROOT = "./test_data"

    def setUp(self) -> None:
        if os.path.exists(self.DATA_ROOT):
            shutil.rmtree(self.DATA_ROOT)

        os.makedirs(self.DATA_ROOT, exist_ok=True)


    def tearDown(self) -> None:
        if os.path.exists(self.DATA_ROOT):
            shutil.rmtree(self.DATA_ROOT)


    def testStdinAsStr(self):
        environment = ExecutionEnvironmentBuilder(MockSubmission())\
                .setStdin("1\n2")\
                .build()
        
        self.assertEqual(["1", "2"], environment.stdin)

    def testAddFileExists(self):
        os.mkdir(os.path.join(self.DATA_ROOT, "sub"))

        with open(os.path.join(self.DATA_ROOT, "sub", "file.txt"), 'w') as w:
            w.write("")

        environment = ExecutionEnvironmentBuilder(MockSubmission())\
                .setDataRoot(self.DATA_ROOT)\
                .addFile(os.path.join("./sub", "file.txt"), "file.txt")\
                .addFile(os.path.join("sub", "file.txt"), "file.txt")\
                .build()

        self.assertIn(os.path.join(self.DATA_ROOT, "sub", "file.txt"), environment.files.keys())
        self.assertEqual(1, len(environment.files))

    def testFileDoesntExist(self):
        with self.assertRaises(EnvironmentError) as error:
            ExecutionEnvironmentBuilder(MockSubmission())\
                .setDataRoot(self.DATA_ROOT)\
                .addFile("file.txt", "file.txt")\
                .build()

        exceptionText = str(error.exception)

        self.assertIn("file.txt does not exist", exceptionText)

    def testValidTimeout(self):
        environment = ExecutionEnvironmentBuilder(MockSubmission())\
                .setTimeout(10)\
                .build()

        self.assertEqual(10, environment.timeout)


    def test0Timeout(self):
        with self.assertRaises(AttributeError):
            ExecutionEnvironmentBuilder(MockSubmission())\
                .setTimeout(0)\
                .build()

class TestEnvironmentGetResults(unittest.TestCase):
    DATA_DIRECTORY: str = "./test_data"
    OUTPUT_FILE_LOCATION = os.path.join(
        DATA_DIRECTORY,
        "outputFile.txt"
    )

    def setUp(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)

        os.mkdir(self.DATA_DIRECTORY)

        self.environment = ExecutionEnvironment(MockSubmission())

    def tearDown(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)

    def testGetOrAssertFilePresent(self):
        expectedOutput = "this is a line in the file"

        with open(self.OUTPUT_FILE_LOCATION, 'w') as w:
            w.write(expectedOutput)

        self.environment.resultData = Results(file_out={
                os.path.basename(self.OUTPUT_FILE_LOCATION): self.OUTPUT_FILE_LOCATION
        })

        actualOutput = getResults(self.environment).file_out[os.path.basename(self.OUTPUT_FILE_LOCATION)]

        self.assertEqual(expectedOutput, actualOutput)

    def testGetOrAssertFileNotPresent(self):
        self.environment.resultData = Results(file_out={})

        with self.assertRaises(AssertionError):
            getResults(self.environment).file_out["dne.txt"]

    def testGetOrAssertEmptyStdout(self):
        self.environment.resultData = Results(stdout=[])

        with self.assertRaises(AssertionError) as error:
            getResults(self.environment).stdout

        exceptionText = str(error.exception)

        self.assertIn("No OUTPUT was created by the student's submission.", exceptionText)


