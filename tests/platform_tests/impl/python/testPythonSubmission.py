import os
import shutil
import string
import unittest
from unittest.mock import patch
from io import StringIO
import random
from autograder_platform.StudentSubmission.common import ValidationError

from autograder_platform.StudentSubmissionImpl.Python import PythonSubmission
from autograder_platform.StudentSubmissionImpl.Python.common import FileTypeMap


class TestStudentSubmission(unittest.TestCase):
    TEST_FILE_DIRECTORY: str = "./sandbox"
    TEST_FILE_MAIN: str = "\n" \
                          "if __name__ == '__main__':" \
                          " print('TEST_FILE_MAIN')\n"

    TEST_FILE_NON_MAIN: str = "\n" \
                              "print('TEST_FILE_NON_MAIN')\n"

    def setUp(self) -> None:
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)
        os.mkdir(self.TEST_FILE_DIRECTORY)

    def tearDown(self) -> None:
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)

    def testDiscoverMainModuleSinglePy(self):
        filename = os.path.join(self.TEST_FILE_DIRECTORY, "non_main.py")

        with open(filename, 'w') as w:
            w.writelines(self.TEST_FILE_NON_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .enableLooseMainMatching()\
                .enableRequirements()\
                .enableTestFiles()\
                .load()\
                .build()\
                .validate()

        self.assertIn(filename, submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES])


    def testDiscoverFileWithDashes(self):
        filename = os.path.join(self.TEST_FILE_DIRECTORY, "file-with-dashes.py")

        with open(filename, 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .enableLooseMainMatching()\
                .load()\
                .build()\
                .validate()

        self.assertIn(filename, submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES])

    def testDiscoverFileTest(self):
        filename = os.path.join(self.TEST_FILE_DIRECTORY, "test.py")

        with open(filename, 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .enableTestFiles()\
                .load()\
                .build()\
                .validate()

        self.assertIn(filename, submission.getDiscoveredFileMap()[FileTypeMap.TEST_FILES])


    def testDiscoverMainModuleRandomNonPy(self):
        filename = os.path.join(self.TEST_FILE_DIRECTORY, "main.py")
        with open(filename, 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)])

            with open(os.path.join(self.TEST_FILE_DIRECTORY, fileName), 'w') as w:
                w.writelines("RAND")

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .load()\
                .build()\
                .validate()

        self.assertIn(filename, submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES])
        self.assertEqual(1, len(submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES]))

    def testDiscoverNoPyFiles(self):
        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)])

            with open(os.path.join(self.TEST_FILE_DIRECTORY, fileName), 'w') as w:
                w.writelines("RAND")

        with self.assertRaises(ValidationError) as error:
            PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .enableLooseMainMatching()\
                    .load()\
                    .build()\
                    .validate()

        exceptionText = str(error.exception)

        self.assertIn("Expected at least one `.py` file", exceptionText)
        self.assertIn("Are you writing your code in a file that ends with `.py`", exceptionText)

    def testDiscoverNoMainPyFile(self):
        fileNames = []

        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)]) + ".py"

            fileNames.append(fileName)

            with open(os.path.join(self.TEST_FILE_DIRECTORY, fileName), 'w') as w:
                w.writelines("RAND")

        with self.assertRaises(ValidationError) as error:
            PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .enableLooseMainMatching()\
                    .load()\
                    .build()\
                    .validate()

        exceptionText = str(error.exception)

        self.assertIn(fileNames[3], exceptionText)
        self.assertIn("Expected one `.py` file", exceptionText)
        self.assertIn("delete extra `.py` files", exceptionText)


    def testDiscoverTestFiles(self):
        testFileNames: list[str] = [
            "test.py",
            "testFile.py",
            "test_file.py",
            "test_FileWith_longName.py"
        ]

        for file in testFileNames:
            with open(os.path.join(self.TEST_FILE_DIRECTORY, file), 'w') as w:
                w.writelines("pass")

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .enableTestFiles()\
                    .enableLooseMainMatching()\
                    .load()\
                    .build()\
                    .validate()

        testFileNames = [f"{os.path.join(self.TEST_FILE_DIRECTORY, file)}" for file in testFileNames]

        self.assertCountEqual(testFileNames, submission.getDiscoveredFileMap()[FileTypeMap.TEST_FILES])
        self.assertEqual(1, len(submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES]))

    def testDiscoverNestedFiles(self):
        nestedDirectory = os.path.join(self.TEST_FILE_DIRECTORY, "nested1", "nested2")
        os.makedirs(nestedDirectory)
        file = os.path.join(nestedDirectory, "main.py")
        
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "non_main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_NON_MAIN)
        with open(file, 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .load()\
                    .build()\
                    .validate()

        self.assertEqual(2, len(submission.getDiscoveredFileMap()[FileTypeMap.PYTHON_FILES]))


    def testManyNestedMainFiles(self):
        nestedDirectory = os.path.join(self.TEST_FILE_DIRECTORY, "nested1", "nested2")
        os.makedirs(nestedDirectory)

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "nested1", "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "nested1", "nested2", "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with self.assertRaises(ValidationError):
            PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .load()\
                    .build()\
                    .validate()

    def testIgnoreHiddenFiles(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, ".py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with self.assertRaises(ValidationError):
            PythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .enableLooseMainMatching()\
                .load() \
                .build() \
                .validate()

    def testIgnorePycacheFiles(self):
        os.makedirs(os.path.join(self.TEST_FILE_DIRECTORY, "__pycache__"))
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "__pycache__", "main.pyc"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with self.assertRaises(ValidationError):
            PythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .enableLooseMainMatching() \
                .load() \
                .build() \
                .validate()

    def testIgnorePathsWithSpaces(self):
        os.makedirs(os.path.join(self.TEST_FILE_DIRECTORY, "code folder"))
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "code folder", "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with self.assertRaises(ValidationError):
            PythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .load() \
                .build() \
                .validate()


    @patch('sys.stdout', new_callable=StringIO)
    def testDiscoverEntrypointManyPy(self, capturedStdout):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "non_main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_NON_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .load()\
                .build()\
                .validate()

        exec(submission.getExecutableSubmission(), {'__name__': "__main__"})

        self.assertEqual("TEST_FILE_MAIN\n", capturedStdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def testDiscoveryEntrypointLooseMatching(self, capturedStdout):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "non_main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_NON_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .enableLooseMainMatching()\
                .load()\
                .build()\
                .validate()

        exec(submission.getExecutableSubmission())

        self.assertEqual("TEST_FILE_NON_MAIN\n", capturedStdout.getvalue())

    def testAddPackages(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .addPackages([{'name': "pip-install-test", 'version': "0.5"}, {'name': "minimal", 'version': ""}])\
                .load()\
                .build()\
                .validate()

        packages = submission.getExtraPackages()

        self.assertIn("pip-install-test", packages)
        self.assertIn("minimal", packages)
        self.assertEqual(packages['minimal'], '')

        submission.TEST_ONLY_removeRequirements()

    def testAddPackage(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .addPackage("pip-install-test")\
                .load()\
                .build()\
                .validate()

        self.assertEqual({"pip-install-test": ""}, submission.getExtraPackages())

        submission.TEST_ONLY_removeRequirements()

    def testGetPackagesFromRequirements(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "requirements.txt"), 'w') as w:
            w.writelines("pip-install-test==0.5\n")

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines("import pip_install_test")

        submission = PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .enableRequirements()\
                .load()\
                .build()\
                .validate()

        self.assertEqual({"pip-install-test": "0.5"}, submission.getExtraPackages())

        submission.TEST_ONLY_removeRequirements()

    def testNonExistentPackageInRequirements(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "requirements.txt"), 'w') as w:
            w.writelines("does-not-exist\ndoes-not-exist2==2.0\n")

        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines("import pip_install_test")

        with self.assertRaises(ValidationError) as error:
            PythonSubmission()\
                    .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                    .enableRequirements()\
                    .load()\
                    .build()\
                    .validate()

        exceptionText = str(error.exception)

        self.assertIn("Unable to locate package, 'does-not-exist'", exceptionText)
        self.assertIn("Unable to locate package, 'does-not-exist2'", exceptionText)

    def testInvalidPackageVersion(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "main.py"), 'w') as w:
            w.writelines(self.TEST_FILE_MAIN)

        with self.assertRaises(ValidationError) as error:
            PythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .addPackage("pip-install-test", "-1")\
                .load()\
                .build()\
                .validate()

        exceptionText = str(error.exception)

        self.assertIn("Unable to locate package, 'pip-install-test' at version -1", exceptionText)

