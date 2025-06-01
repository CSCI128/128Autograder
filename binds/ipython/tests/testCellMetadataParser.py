import ast
import unittest
from typing import Optional

from language_binds.ipython.source.autograder_binds.IPython.CellMetadataParser import CellMetadata, parseCellMetadata


class TestCellMetadataParser(unittest.TestCase):
    def testParseCellMetadataTestableCellPresent(self):
        expectedId = "testable_cell_1"
        expectedDep = (1, "dep_1")

        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="{expectedId}", deps=[{expectedDep}])
        """

        metadata: Optional[CellMetadata] = parseCellMetadata(ast.parse(program))

        self.assertIsNotNone(metadata)

        self.assertEqual(expectedId, metadata.id)
        self.assertEqual(1, len(metadata.deps))
        self.assertEqual(expectedDep, metadata.deps[0])
        self.assertTrue(metadata.runnable)

    def testParseCellMetadataCellPresent(self):
        expectedId = "dep_1"

        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import Cell
Cell(id="{expectedId}")
        """

        metadata: Optional[CellMetadata] = parseCellMetadata(ast.parse(program))

        self.assertIsNotNone(metadata)

        self.assertEqual(expectedId, metadata.id)
        self.assertEqual(0, len(metadata.deps))
        self.assertFalse(metadata.runnable)

    def testParseCellMetadataCellManyPresent(self):
        expectedId = "dep_1"

        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import Cell
Cell(id="{expectedId}")
Cell(id="ignore_1")
Cell(id="ignore_2")
        """

        metadata: Optional[CellMetadata] = parseCellMetadata(ast.parse(program))

        self.assertIsNotNone(metadata)

        self.assertEqual(expectedId, metadata.id)
        self.assertEqual(0, len(metadata.deps))
        self.assertFalse(metadata.runnable)

    def testParseCellMetadataCellNonePresent(self):
        program = "print('hello world!')"

        metadata: Optional[CellMetadata] = parseCellMetadata(ast.parse(program))

        self.assertIsNone(metadata)

    def testParseCellMetadataIdTypeError(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id=1, deps=[])
        """

        with self.assertRaises(TypeError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception)

        self.assertIn("expected a string", msg.lower())

    def testParseCellMetadataIdSyntaxError(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
id = "testable_cell_1"
TestableCell(id=id, deps=[])
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception.msg)

        self.assertIn("should be a constant", msg.lower())

    def testParseCellMetadataDepsSyntaxErrorNoTuple(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=["dep_1"])
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception.msg)

        self.assertIn("expected a tuple with ordering and id", msg.lower())

    def testParseCellMetadataDepsSyntaxErrorInvalidTuple(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=[(1, "dep_1", "a helpful comment")])
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception.msg)

        self.assertIn("expected a tuple with exactly ordering and id", msg.lower())

    def testParseCellMetadataDepsSyntaxErrorOrdering(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
order = 1
TestableCell(id="testable_cell", deps=[(order, "dep_1")])
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception.msg)

        self.assertIn("expected a constant", msg.lower())

    def testParseCellMetadataDepsSyntaxErrorId(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
dep = "dep_1"
TestableCell(id="testable_cell", deps=[(1, dep)])
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception.msg)

        self.assertIn("expected a constant", msg.lower())

    def testParseCellMetadataDepsTypeErrorOrdering(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=[("1", "dep_1")])
        """

        with self.assertRaises(TypeError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception)

        self.assertIn("expected an int", msg.lower())

    def testParseCellMetadataDepsTypeErrorId(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=[(1, 1)])
        """

        with self.assertRaises(TypeError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception)

        self.assertIn("expected a str", msg.lower())

    def testParseCellMetadataMissingId(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell()
        """

        with self.assertRaises(SyntaxError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception)

        self.assertIn("missing required field", msg.lower())

    def testParseCellMetadataInvalidDeps(self):
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
TestableCell(id="testable_cell", deps=(1, 1))
        """

        with self.assertRaises(TypeError) as ex:
            parseCellMetadata(ast.parse(program))

        msg = str(ex.exception)

        self.assertIn("expected a list", msg.lower())

    def testIgnoreIrrelevantFunctionCalls(self):
        expected_id = "testable_cell"
        program = \
            f"""
from autograder_platform.StudentSubmissionImpl.ipython.metadata import TestableCell
print("this is irrelevant")
TestableCell(id="{expected_id}", deps=[(1, "1")])
        """

        cellMetadata: Optional[CellMetadata] = parseCellMetadata(ast.parse(program))

        self.assertIsNotNone(cellMetadata)
        self.assertEqual(expected_id, cellMetadata.id)

