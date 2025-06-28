import os.path
import shutil
import unittest
from io import StringIO
from unittest.mock import patch

from autograder_platform.StudentSubmission.common import ValidationError
from language_binds.IPython.IPythonSubmission import IPythonSubmission
from .NotebookBuilder import NotebookBuilder


class TestIPythonSubmission(unittest.TestCase):
    TEST_FILE_DIRECTORY: str = "./sandbox"
    VALID_TESTABLE_CELL: str = \
        """
from language_binds.IPython.metadata import TestableCell
TestableCell(id="testable_cell", deps=[])
print("VALID_TESTABLE_CELL")
    """

    VALID_CELL: str = \
        """
from language_binds.IPython.metadata import Cell 
Cell(id="cell")
print("VALID_CELL")
    """

    def setUp(self):
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)

        os.mkdir(self.TEST_FILE_DIRECTORY)

    def tearDown(self):
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)

    def testDiscoverSingleFile(self):
        filename = NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission()\
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
            .load()

        discoveredFiles = submission.getDiscoveredFiles()

        self.assertIn(filename, discoveredFiles)

        cells = submission.getCells()

        self.assertEqual(2, len(cells))

    def testDiscoverSingleFileNested(self):
        fullpath = os.path.join(self.TEST_FILE_DIRECTORY, "nested")
        os.mkdir(fullpath)
        filename = NotebookBuilder("notebook.ipynb", fullpath) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load()

        discoveredFiles = submission.getDiscoveredFiles()

        self.assertIn(filename, discoveredFiles)

        cells = submission.getCells()

        self.assertEqual(2, len(cells))

    def testDiscoverManyFiles(self):
        NotebookBuilder("notebook1.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        NotebookBuilder("notebook2.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        with self.assertRaises(ValidationError) as ex:
            IPythonSubmission()\
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
                .load()

        msg = str(ex.exception)

        self.assertIn("expected one `.ipynb` file", msg.lower())


    def testDiscoverNoNotebooks(self):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, "data.txt"), "w") as w:
            w.write("content")

        with self.assertRaises(ValidationError) as ex:
            IPythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .load()

        msg = str(ex.exception)

        self.assertIn("no `.ipynb` files were submitted!", msg.lower())

    def testNoTestableCells(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        with self.assertRaises(ValidationError) as ex:
            IPythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .load()

        msg = str(ex.exception)

        self.assertIn("at least one cell to be testable", msg.lower())

    @patch('sys.stdout', new_callable=StringIO)
    def testTestableCellWithDependency(self, capturedStdout):
        expected = 100
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(f"""
from language_binds.IPython.metadata import Cell, TestableCell
Cell(id="imports")
value = {expected}
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell("""
TestableCell(id="testable", deps=[(0, "imports")])
print(value)
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission()\
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
            .load()\
            .build()\
            .validate()

        cells = submission.getCells()

        self.assertIn("testable", cells.keys())
        self.assertEqual("imports", cells["testable"].metadata.deps[0].id)

        exec(submission.getExecutableSubmission())

        self.assertEqual(f"{expected}\n", capturedStdout.getvalue())

    def testTestableCellMissingDependency(self):
        expected = 100
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(f"""
from language_binds.IPython.metadata import Cell, TestableCell
Cell(id="imports")
value = {expected}
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell("""
TestableCell(id="testable", deps=[(0, "dne")])
print(value)
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        with self.assertRaises(ValidationError) as ex:
            IPythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .load()

        msg = str(ex.exception)

        self.assertIn("missing dependency 'dne' for cell 'testable'", msg.lower())

    def testOnlyRunnableCellsCanBeActivated(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load()\
            .build()\
            .validate()

        with self.assertRaises(RuntimeError) as ex:
            submission.setActiveCell("cell")

        msg = str(ex.exception)

        self.assertIn("invalid active cell", msg.lower())

    def testActiveCellMustBeSetWhenManyUnset(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(f"""
from language_binds.IPython.metadata import Cell, TestableCell
Cell(id="imports")
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell("""
TestableCell(id="testable", deps=[(0, "imports")])
            """) \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load() \
            .build() \
            .validate()

        with self.assertRaises(RuntimeError) as ex:
            submission.getExecutableSubmission()

        msg = str(ex.exception)

        self.assertIn("no active cell has been defined", msg.lower())

    @patch('sys.stdout', new_callable=StringIO)
    def testActiveCellMustBeSetWhenManySet(self, capturedStdout):
        expected = "imported!"
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(f"""
from language_binds.IPython.metadata import Cell, TestableCell
TestableCell(id="imports", deps=[])
value = '{expected}'
            """) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell("""
TestableCell(id="testable", deps=[(0, "imports")])
print(value)
            """) \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load() \
            .build() \
            .validate()

        submission.setActiveCell("testable")

        exec(submission.getExecutableSubmission())

        self.assertEqual(f"{expected}\n", capturedStdout.getvalue())


    def testGenerateHTMLFailsWhenDisabled(self):
        NotebookBuilder("notebook2.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission()\
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
            .load()

        with self.assertRaises(RuntimeError) as ex:
            submission.getNotebookHtml()

        msg = str(ex.exception)

        self.assertIn("notebook html requested, but not available", msg.lower())

    def testGenerateHTML(self):
        NotebookBuilder("notebook2.ipynb", self.TEST_FILE_DIRECTORY) \
            .addMarkdownCell("# Markdown Cell") \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .addMarkdownCell("# Markdown Cell") \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .enableHtmlTransformation()\
            .load()

        html = submission.getNotebookHtml()

        # we are going to assume that the generation worked and nbconvert doesn't gaslight us
        self.assertIsNotNone(html)

    def testTransformMagicCommand(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY)\
            .addCodeCell(
            """
from language_binds.IPython.metadata import Cell, TestableCell
TestableCell(id="testable", deps=[])
%matplotlib inline
!pip install yippee
            """)\
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load()

        cell = submission.getCells()["testable"]

        self.assertNotIn("%", cell.code)
        self.assertNotIn("!", cell.code)


    def testTransformMatplotlibShow(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell(
            """
from language_binds.IPython.metadata import Cell, TestableCell
import matplotlib.pyplot as plt
TestableCell(id="testable", deps=[])
plt.show()
matplotlib.pyplot.show()
            """) \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .load()

        cell = submission.getCells()["testable"]

        self.assertNotIn("show()", cell.code)
        self.assertIn("fig_1.png", cell.code)
        self.assertIn("fig_2.png", cell.code)

    def testVerifyIgnoresHiddenCacheAndSpacedFiles(self):
        os.makedirs(os.path.join(self.TEST_FILE_DIRECTORY, "dir", "__pycache__"))

        NotebookBuilder(".notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell(self.VALID_TESTABLE_CELL)\
            .toFile()

        NotebookBuilder("a notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .toFile()

        NotebookBuilder("a notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .toFile()

        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell(self.VALID_TESTABLE_CELL) \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY)\
            .load()

        cells = submission.getCells()

        self.assertEqual(1, len(cells))


    @patch("sys.stdout", new_callable=StringIO)
    def testInstallPackages(self, capturedStdout):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell("""
from language_binds.IPython.metadata import TestableCell
TestableCell(id="testable", deps=[])
import pip_install_test
            """) \
            .toFile()

        submission = IPythonSubmission() \
            .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
            .addPackages([
                {"name": "pip-install-test", "version": "0.5"},
                {"name": "minimal", "version": ""}
            ])\
            .load()\
            .build()\
            .validate()

        exec(submission.getExecutableSubmission())

        self.assertIn("good job", capturedStdout.getvalue().lower())

        submission.TEST_ONLY_removeRequirements()

    def testPackageDNE(self):
        NotebookBuilder("notebook.ipynb", self.TEST_FILE_DIRECTORY) \
            .addCodeCell("""
from langauge_binds.IPython.metadata import TestableCell
TestableCell(id="testable", deps=[])
import pip_install_test
            """) \
            .toFile()

        with self.assertRaises(ValidationError) as ex:
            IPythonSubmission() \
                .setSubmissionRoot(self.TEST_FILE_DIRECTORY) \
                .addPackages([
                {"name": "dne", "version": "0.5"},
                {"name": "dne2", "version": ""},
            ]) \
                .load() \
                .build()

        msg = str(ex.exception)

        self.assertIn("Unable to locate package, 'dne'", msg)
        self.assertIn("Unable to locate package, 'dne2'", msg)
