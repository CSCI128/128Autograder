import unittest
from unittest.mock import patch
import sys
import os
import shutil
from io import StringIO
import subprocess
import importlib.util
from autograder_cli.run_local import LocalAutograderCLI
import random
import string

class TestStudentTestMyWork(unittest.TestCase):
    TEST_DIRECTORY: str = "./testData"
    SUBMISSION_DIRECTORY: str = os.path.join(TEST_DIRECTORY, "submission")

    
    def setUp(self) -> None:
        if os.path.exists(self.TEST_DIRECTORY):
            shutil.rmtree(self.TEST_DIRECTORY)

        os.mkdir(self.TEST_DIRECTORY)

        os.mkdir(self.SUBMISSION_DIRECTORY)

        self.localCLI = LocalAutograderCLI()


    def tearDown(self) -> None:
        if os.path.exists(self.TEST_DIRECTORY):
            shutil.rmtree(self.TEST_DIRECTORY)


    @patch('sys.stdout', new_callable=StringIO)
    def testStudentWorkNotPresent(self, capturedStdout: StringIO):
        result = self.localCLI.verify_student_work_present(self.SUBMISSION_DIRECTORY)

        self.assertFalse(result)

        self.assertIn("No valid files found", capturedStdout.getvalue())
        
    
    @patch('sys.stdout', new_callable=StringIO)
    def testStudentWorkInvalidDirectory(self, capturedStdout: StringIO):
        result = self.localCLI.verify_student_work_present("./DNE")

        self.assertFalse(result)

        self.assertIn("Failed to locate student work", capturedStdout.getvalue())


    @patch('sys.stdout', new_callable=StringIO)
    def testStudentWorkNoPy(self, capturedStdout: StringIO):
        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)])

            with open(os.path.join(self.SUBMISSION_DIRECTORY, fileName), 'w') as w:
                w.write("\n")

        result = self.localCLI.verify_student_work_present(self.SUBMISSION_DIRECTORY)

        self.assertFalse(result)

        self.assertIn("No valid files found", capturedStdout.getvalue())

    def testStudentWorkPresentManyFiles(self):
        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)]) + ".py"

            with open(os.path.join(self.SUBMISSION_DIRECTORY, fileName), 'w') as w:
                w.write("\n")

        result = self.localCLI.verify_student_work_present(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

    @patch('sys.stdout', new_callable=StringIO)
    def testCleanPrevSubmission(self, _):
        for _ in range(10):
            fileName = "".join([random.choice(string.ascii_letters) for _ in range(10)]) + ".zip"

            with open(os.path.join(self.TEST_DIRECTORY, fileName), 'w') as w:
                w.write("\n")
        
        self.assertTrue(len(os.listdir(self.TEST_DIRECTORY)) > 1)
        
        self.localCLI.clean_previous_submissions(self.TEST_DIRECTORY)

        self.assertFalse(len(os.listdir(self.TEST_DIRECTORY)) > 1)

    def testChangesDetectedFirstRun(self):
        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission.py"), 'w') as w:
            w.write("First run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

    def testChangesDetectedManyRuns(self):
        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission.py"), 'w') as w:
            w.write("First run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission.py"), 'a') as w:
            w.write("Second run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

    def testUnchangedDetected(self):
        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission.py"), 'w') as w:
            w.write("Frist run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertFalse(result)

    def testChangesInManyFiles(self):
        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission1.py"), 'w') as w:
            w.write("First run!")

        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission2.py"), 'w') as w:
            w.write("First run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)
        
        self.assertTrue(result)

        with open(os.path.join(self.SUBMISSION_DIRECTORY, "submission2.py"), 'a') as w:
            w.write("Second run!")

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)
        
        self.assertTrue(result)

    def testEmptyJson(self):
        with open(os.path.join(self.SUBMISSION_DIRECTORY, self.localCLI.FILE_HASHES_NAME), "w") as _:
            pass

        result = self.localCLI.verify_file_changed(self.SUBMISSION_DIRECTORY)

        self.assertTrue(result)

    def testDiscoverAutogradersOneAvailable(self):
        config_loc = os.path.join(self.TEST_DIRECTORY, "config.toml")

        with open(config_loc, 'w') as w:
            w.write("")

        autograders = []
        self.localCLI.discover_autograders(self.TEST_DIRECTORY, autograders)

        self.assertEqual([config_loc], autograders)

    def testDiscoverManyAutograders(self):
        config_paths = []

        for i in range(5):
            path = os.path.join(self.TEST_DIRECTORY, str(i), "config.toml")
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'w') as w:
                w.write(f"assignment_name=\"A{i:02}\"")

            config_paths.append(path)

        autograders = []
        self.localCLI.discover_autograders(self.TEST_DIRECTORY, autograders)

        autograders.sort()
        config_paths.sort()

        self.assertEqual(config_paths, autograders)

    # def testSelectRoot(self, ):

    def testCompareVersionExactMatch(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.0.0"

        res = self.localCLI.compare_autograder_versions("2.0.0")

        self.assertTrue(res)

        self.localCLI.get_version = get_version

    def testCompareVersionCurrentIsNewerPatch(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.0.1"

        res = self.localCLI.compare_autograder_versions("2.0.0")

        self.assertTrue(res)

        self.localCLI.get_version = get_version

    def testCompareVersionCurrentIsNewerMinor(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.1.0"

        res = self.localCLI.compare_autograder_versions("2.0.0")

        self.assertTrue(res)

        self.localCLI.get_version = get_version

    def testCompareVersionCurrentIsNewerMinorPatchHigher(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.1.0"

        res = self.localCLI.compare_autograder_versions("2.0.1")

        self.assertTrue(res)

        self.localCLI.get_version = get_version

    def testCompareVersionCurrentIsOlderMinorPatchHigher(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.0.1"

        res = self.localCLI.compare_autograder_versions("2.1.0")

        self.assertFalse(res)

        self.localCLI.get_version = get_version

    def testCompareVersionCurrentIsOlderPatch(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "2.0.1"

        res = self.localCLI.compare_autograder_versions("2.0.2")

        self.assertFalse(res)

        self.localCLI.get_version = get_version

    def testMajorMismatch(self):
        get_version = self.localCLI.get_version
        self.localCLI.get_version = lambda: "3.1.0"

        res = self.localCLI.compare_autograder_versions("2.0.2")

        self.assertFalse(res)

        self.localCLI.get_version = get_version

    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testMissingPackage(self, _):
        self.assertIsNone(importlib.util.find_spec("pip_install_test"))

        res = self.localCLI.verifyRequiredPackages({"pip_install_test": "pip-install-test"})

        self.assertIsNotNone(importlib.util.find_spec("pip_install_test"))

        self.assertTrue(res)

        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pip-install-test"], stdout=subprocess.DEVNULL)
        
    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testPackageDoesNotExist(self, _):
        self.assertIsNone(importlib.util.find_spec("this_package_doesnt_exist"))

        res = self.localCLI.verifyRequiredPackages({"this_package_doesnt_exist": "this_package_doesnt_exist"})

        self.assertFalse(res)

    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testPackagesPresent(self, _):
        self.assertIsNotNone(importlib.util.find_spec("dill"))

        self.localCLI.verifyRequiredPackages({"dill": "dill-install-test"})

        self.assertIsNotNone(importlib.util.find_spec("dill"))

    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testMinPythonVersionTooLow(self, _):
        self.assertFalse(self.localCLI.verifyPythonVersion((3, 12), (3, 11, 2, 'final', 0)))

    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testMinPythonVersionValid(self, _):
        self.assertTrue(self.localCLI.verifyPythonVersion((3, 11), (3, 11, 2, 'final', 0)))
        self.assertTrue(self.localCLI.verifyPythonVersion((3, 11), (3, 12, 2, 'final', 0)))

    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testWorkingDirectoryIncorrect(self, _):
        self.assertFalse(self.localCLI.verifyWorkingDirectory("./sandbox"))
       
    @patch('sys.stdout', new_callable=StringIO)
    @unittest.skip("This feature is no longer available in the CLI")
    def testWorkingDirectoryIsCorrect(self, _):
        self.assertTrue(self.localCLI.verifyWorkingDirectory(os.getcwd()))
