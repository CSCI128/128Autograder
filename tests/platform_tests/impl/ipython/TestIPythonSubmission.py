import os.path
import shutil
import unittest

from autograder_platform.StudentSubmission.common import ValidationError
from autograder_platform.StudentSubmissionImpl.ipython.IPythonSubmission import IPythonSubmission
from platform_tests.impl.ipython.NotebookBuilder import NotebookBuilder


class TestIPythonSubmission(unittest.TestCase):
    TEST_FILE_DIRECTORY: str = "./sandbox"
    VALID_TESTABLE_CELL: str = \
        """
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=[])
print("VALID_TESTABLE_CELL")
    """

    VALID_CELL: str = \
        """
from autograder_platform.StudentSubmissionImpl.ipython.metadata import Cell 
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
