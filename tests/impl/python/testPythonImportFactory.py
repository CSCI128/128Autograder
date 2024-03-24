import importlib
import os
import shutil
import sys
import unittest

from StudentSubmissionImpl.Python.PythonFileImportFactory import PythonFileImportFactory

class TestPythonImportFactory(unittest.TestCase):
    TEST_FILE_DIRECTORY: str = "./sandbox"
    
    def setUp(self) -> None:
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)
        os.mkdir(self.TEST_FILE_DIRECTORY)

    def tearDown(self) -> None:
        if os.path.exists(self.TEST_FILE_DIRECTORY):
            shutil.rmtree(self.TEST_FILE_DIRECTORY)

    def writeTestFile(self, filename):
        with open(os.path.join(self.TEST_FILE_DIRECTORY, filename), 'w') as w:
            w.write(
                "import math\n"\
                "def sqrt(a):\n"\
                "   return math.sqrt(a)"
            )
        
    def testImportsFile(self):
        filename = "calc.py"
        self.writeTestFile(filename)
        PythonFileImportFactory.registerFile(os.path.join(self.TEST_FILE_DIRECTORY, filename), "calc")
        sys.meta_path.insert(0, PythonFileImportFactory.buildImport())
        
        importedModule = importlib.import_module("calc")
        self.assertEqual(importedModule.sqrt(4), 2)

    def testImportErrorRaised(self):
        filename = "bad.py"

        PythonFileImportFactory.registerFile(os.path.join(self.TEST_FILE_DIRECTORY, filename), "bad")
        sys.meta_path.insert(0, PythonFileImportFactory.buildImport())

        with self.assertRaises(ImportError):
            importlib.import_module("bad")
