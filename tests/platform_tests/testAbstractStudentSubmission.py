import unittest
import os
import shutil

from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.StudentSubmission.AbstractValidator import AbstractValidator
from autograder_platform.StudentSubmission.ITransformer import ITransformer
from autograder_platform.StudentSubmission.common import ValidationError, ValidationHook


class StudentSubmission(AbstractStudentSubmission[str]):
    def __init__(self):
        super().__init__()
        self.studentCode: str = "No code"

    def doLoad(self):
        self.studentCode = self.runTransformers("Loaded code!")

    def doBuild(self):
        self.studentCode = "Built code!"

    def getExecutableSubmission(self) -> str:
        return self.studentCode


class CodeLoadedValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.POST_LOAD

    def __init__(self):
        super().__init__()
        self.code = ""

    def setup(self, studentSubmission):
        self.code = studentSubmission.studentCode

    def run(self):
        if not self.code:
            self.addError(Exception("Code was not loaded!"))


class FileExistsValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.PRE_LOAD

    def __init__(self, fileName):
        super().__init__()
        self.submissionRoot = ""
        self.fileName = fileName

    def setup(self, studentSubmission):
        self.submissionRoot = studentSubmission.getSubmissionRoot()

    def run(self):
        if self.fileName not in self.submissionRoot:
            self.addError(Exception(f"{self.fileName} does not exist!"))

class ManualValidator(AbstractValidator):
    @staticmethod
    def getValidationHook() -> ValidationHook:
        return ValidationHook.MANUAL

    def __init__(self, raiseError=False):
        super().__init__()
        self.called = False
        self.raiseError = raiseError

    def setup(self, studentSubmission):
        self.called = True

    def run(self):
        if not self.called:
            self.addError(Exception("Setup was not called!"))
        if self.raiseError:
            self.addError(Exception("Manual validator error!"))


class SimpleTransformer(ITransformer):
    def __init__(self, textToSet: str):
        self.textToSet = textToSet

    def transform(self, string: str) -> str:
        return self.textToSet


class TestAbstractStudentSubmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.initialDirectory = os.getcwd()
        cls.TEST_DIR = os.path.join(cls.initialDirectory, "sandbox")

    def setUp(self) -> None:
        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)

        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)

    def tearDown(self) -> None:
        os.chdir(self.initialDirectory)

        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)

    def testSetSubmissionRootExists(self):
        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        studentSubmission = StudentSubmission()\
                .setSubmissionRoot(submissionRoot)\
                .addValidator(CodeLoadedValidator())\
                .load()\
                .build()\
                .validate()

        self.assertEqual("Built code!", studentSubmission.getExecutableSubmission())

    def testSetSubmissionRootDoesntExist(self):
        submissionRoot = "./submission"
        with self.assertRaises(ValidationError) as validationError:
            StudentSubmission()\
                .setSubmissionRoot(submissionRoot)\
                .load()

        exceptionText = str(validationError.exception)

        self.assertIn("Validation Errors:", exceptionText)
        self.assertIn(f"1. FileNotFoundError: {submissionRoot} does not exist", exceptionText)


    def testAddValidatorForExistingFile(self):
        filename = "file.txt"
        
        with self.assertRaises(ValidationError) as validationError:
            StudentSubmission()\
                .addValidator(FileExistsValidator(filename))\
                .setSubmissionRoot("./dne")\
                .load()

        exceptionText = str(validationError.exception)

        self.assertIn("2.", exceptionText)
        self.assertIn(f"{filename} does not exist", exceptionText)


    def testManualValidatorNotCalled(self):
        manualValidator = ManualValidator()

        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission()\
            .setSubmissionRoot(submissionRoot) \
            .addValidator(manualValidator) \
            .addValidator(CodeLoadedValidator()) \
            .load() \
            .build() \
            .validate()

        self.assertFalse(manualValidator.called)

    def testManualValidatorCalled(self):
        manualValidator = ManualValidator()

        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission() \
            .setSubmissionRoot(submissionRoot) \
            .addValidator(manualValidator) \
            .addValidator(CodeLoadedValidator()) \
            .load() \
            .build() \
            .validate()
        submission.runManualValidationHook(ManualValidator)

        self.assertTrue(manualValidator.called)

    def testNoManualValidatorsDefined(self):
        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission() \
            .setSubmissionRoot(submissionRoot) \
            .addValidator(CodeLoadedValidator()) \
            .load() \
            .build() \
            .validate()

        with self.assertRaises(RuntimeError):
            submission.runManualValidationHook(ManualValidator)

    def testIncorrectManualValidatorCalled(self):
        manualValidator = ManualValidator()
        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission() \
            .setSubmissionRoot(submissionRoot) \
            .addValidator(CodeLoadedValidator()) \
            .addValidator(manualValidator) \
            .load() \
            .build() \
            .validate()

        with self.assertRaises(RuntimeError):
            submission.runManualValidationHook(CodeLoadedValidator)

    def testManualValidatorRaisesError(self):
        manualValidator = ManualValidator(raiseError=True)
        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission() \
            .setSubmissionRoot(submissionRoot) \
            .addValidator(CodeLoadedValidator()) \
            .addValidator(manualValidator) \
            .load() \
            .build() \
            .validate()

        with self.assertRaises(ValidationError):
            submission.runManualValidationHook(ManualValidator)

    def testRunTransformer(self):
        expected = "this was transformed!"

        submissionRoot = "./submission"
        os.mkdir(submissionRoot)
        with open(os.path.join(submissionRoot, "file.txt"), 'w') as w:
            w.write("FILE!")

        submission = StudentSubmission() \
            .setSubmissionRoot(submissionRoot) \
            .addTransformer(SimpleTransformer(expected))\
            .load()

        self.assertEqual(expected, submission.getExecutableSubmission())
