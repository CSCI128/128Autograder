import os
import shutil
import unittest
from unittest.mock import Mock

from autograder_cli.build_autograder import Build, FilesEnum

class TestBuildFileDiscovery(unittest.TestCase):
    SANDBOX = "sandbox"
    TEST_ROOT = os.path.join(SANDBOX, "tests")
    DATA_SOURCE_ROOT = os.path.join(SANDBOX, "data")

    def setUp(self) -> None:
        if os.path.exists(self.SANDBOX):
            shutil.rmtree(self.SANDBOX)

        os.makedirs(self.TEST_ROOT, exist_ok=True)
        os.makedirs(self.DATA_SOURCE_ROOT, exist_ok=True)

        self.config = Mock()
        self.setUpConfig()

        self.privateFiles = ["test_private.py", "test_private1.py", "test_private_1.py", "test_private_test2.py"]
        self.publicFiles = ["test.py", "test_public.py", "test_im_crying.py"]

        self.privateDataFiles = ["private_data.dat", os.path.join("private", "data.dat"), os.path.join("public", "private", "data.dat")]
        self.publicDataFiles = ["file.dat", os.path.join("nested", "nested", "file.dat")]

    def setUpConfig(self):
        # There has to be a better way to setup this mock
        self.config.config.test_directory = self.TEST_ROOT
        self.config.build.allow_private=True
        self.config.build.private_tests_regex=r"^test_private_?\w*\.py$"
        self.config.build.public_tests_regex=r"^test_?\w*\.py$"
        self.config.build.use_stater_code=False
        self.config.build.starter_code_source = "."
        self.config.build.use_data_files = False
        self.config.build.data_files_source = self.DATA_SOURCE_ROOT


    def tearDown(self) -> None:
        if os.path.exists(self.SANDBOX):
            shutil.rmtree(self.SANDBOX)

    def writeTestFiles(self):
        for file in self.privateFiles:
            with open(os.path.join(self.TEST_ROOT, file), "w") as w:
                w.write("Private!")


        for file in self.publicFiles:
            with open(os.path.join(self.TEST_ROOT, file), "w") as w:
                w.write("Public!")

    def writeDataFiles(self):
        for file in self.privateDataFiles:
            path = os.path.join(self.DATA_SOURCE_ROOT, file)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as w:
                w.write("Private!")

        for file in self.publicDataFiles:
            path = os.path.join(self.DATA_SOURCE_ROOT, file)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as w:
                w.write("Public!")

    def testDiscoverPublicAndPrivateTests(self):
        build = Build(self.config, ".", "./bin", "1.0.0")

        self.writeTestFiles()

        result = build.discoverFiles()

        self.assertEqual(len(self.privateFiles), len(result[FilesEnum.PRIVATE_TEST]))
        self.assertEqual(len(self.publicFiles), len(result[FilesEnum.PUBLIC_TEST]))

    def testPrivateTestFilesWhenConflict(self):
        self.config.build.private_tests_regex=r"^test_?\w*\.py$"
        build = Build(self.config, ".", "./bin", "1.0.0")

        self.writeTestFiles()

        result = build.discoverFiles()

        self.assertEqual(len(self.privateFiles) + len(self.publicFiles), len(result[FilesEnum.PRIVATE_TEST]))
        self.assertEqual(0, len(result[FilesEnum.PUBLIC_TEST]))

    def testAllPublicWhenPrivateFalse(self):
        self.config.build.allow_private = False

        build = Build(self.config, ".", "./bin", "1.0.0")

        self.writeTestFiles()

        result = build.discoverFiles()

        self.assertEqual(0, len(result[FilesEnum.PRIVATE_TEST]))
        self.assertEqual(len(self.privateFiles) + len(self.publicFiles), len(result[FilesEnum.PUBLIC_TEST]))


    def testDataFileDiscoveryIgnoresTestFiles(self):
        self.config.build.use_data_files = True
        self.config.build.data_files_source = self.TEST_ROOT

        build = Build(self.config, ".", "./bin", "1.0.0")

        self.writeTestFiles()

        result = build.discoverFiles()

        self.assertEqual(0, len(result[FilesEnum.PRIVATE_DATA]))
        self.assertEqual(0, len(result[FilesEnum.PUBLIC_DATA]))

    def testDiscoverPublicAndPrivateDataFiles(self):
        self.config.build.use_data_files = True

        build = Build(self.config, ".", "./bin", "1.0.0") 

        self.writeDataFiles()

        result = build.discoverFiles()

        self.assertEqual(len(self.privateDataFiles), len(result[FilesEnum.PRIVATE_DATA]))
        self.assertEqual(len(self.publicDataFiles), len(result[FilesEnum.PUBLIC_DATA]))

    def testIgnoresHiddenFiles(self):
        self.config.build.use_data_files = True

        with open(os.path.join(self.DATA_SOURCE_ROOT, ".data.dat"), "w") as w:
            w.write("Ignore!")

        os.makedirs(os.path.join(self.DATA_SOURCE_ROOT, ".hidden"), exist_ok=True)

        with open(os.path.join(self.DATA_SOURCE_ROOT, ".hidden", "data.dat"), "w") as w:
            w.write("Ignore!")
        
        build = Build(self.config, ".", "./bin", "1.0.0") 

        result = build.discoverFiles()

        self.assertEqual(0, len(result[FilesEnum.PRIVATE_DATA]))
        self.assertEqual(0, len(result[FilesEnum.PUBLIC_DATA]))

    def testAddsStarterCode(self):
        starterCodePath = os.path.join(self.SANDBOX, "starterCode.py")

        self.config.build.use_stater_code = True
        self.config.build.starter_code_source = starterCodePath

        with open(starterCodePath, 'w') as w:
            w.write("Starter Code!")

        build = Build(self.config, ".", "./bin", "1.0.0") 

        result = build.discoverFiles()

        self.assertEqual(1, len(result[FilesEnum.STARTER_CODE]))



