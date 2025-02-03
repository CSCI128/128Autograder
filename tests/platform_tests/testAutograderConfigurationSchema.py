import os
import shutil
import unittest

from autograder_platform.config.Config import AutograderConfigurationSchema, InvalidConfigException


class TestAutograderConfigurationSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.configFile = {
            "assignment_name": "HelloWold",
            "semester": "F99",
            "config": {
                "impl_to_use": "Python",
                "autograder_version": "2.0.0",
                "test_directory": ".",
                "enforce_submission_limit": True,
                "perfect_score": 10,
                "max_score": 10,
                "python": {},
            },
            "build": {
                "use_starter_code": False,
                "use_data_files": False,
                "build_student": True,
                "build_gradescope": True,
            }
        }

    @staticmethod
    def createAutograderConfigurationSchema() -> AutograderConfigurationSchema:
        return AutograderConfigurationSchema()

    def testValidNoOptionalFields(self):
        schema = self.createAutograderConfigurationSchema()

        actual = schema.validate(self.configFile)
        self.assertIn("submission_limit", actual["config"])
        self.assertIn("buffer_size", actual["config"]["python"])

    def testValidOptionalFields(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["python"] = {}
        actual = schema.validate(self.configFile)
        self.assertIn("extra_packages", actual["config"]["python"])
        self.assertIn("buffer_size", actual["config"]["python"])

    def testInvalidOptionalFields(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["python"] = {}
        self.configFile["config"]["python"]["extra_packages"] = [{"name": "package"}]
        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testValidOptionalNestedFields(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["python"] = {}
        packages = [{"name": "package", "version": "1.0.0"}]
        self.configFile["config"]["python"]["extra_packages"] = packages
        self.configFile["config"]["python"]["buffer_size"] = 2 * 2 ** 20

        actual = schema.validate(self.configFile)

        self.assertEqual(packages, actual["config"]["python"]["extra_packages"])
        self.assertEqual(2*2**20, actual["config"]["python"]["buffer_size"])

    def testExtraFields(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["new_field"] = "This field shouldn't exist"

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testInvalidAutograderVersion(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["autograder_version"] = "0.0"

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testBuildNoOptional(self):
        schema = self.createAutograderConfigurationSchema()

        data = schema.validate(self.configFile)

        actual = schema.build(data)

        self.assertEqual("F99", actual.semester)
        self.assertEqual(1000, actual.config.submission_limit)

    def testBuildWithOptional(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["python"] = {}

        data = schema.validate(self.configFile)

        actual = schema.build(data)

        if actual.config.python is None:
            self.fail("config.python was None when it shouldn't be!")

        self.assertIsNotNone(actual.config.python.extra_packages)

    @unittest.skip("C is no longer supported")
    def testBuildWithCImpl(self):
        schema = self.createAutograderConfigurationSchema()
        self.configFile["config"]["impl_to_use"] = "C"
        self.configFile["config"]["c"] = {}
        self.configFile["config"]["c"]["use_makefile"] = True
        self.configFile["config"]["c"]["clean_target"] = "clean"
        self.configFile["config"]["c"]["submission_name"] = "PROJECT"

        data = schema.validate(self.configFile)

        actual = schema.build(data)

        if actual.config.c is None:
            self.fail("config.c was None when it shouldn't be!")


        self.assertIsNotNone(actual.config.c.use_makefile)
        self.assertIsNotNone(actual.config.c.submission_name)

    def testBuildWithCImplInvalidName(self):
        schema = self.createAutograderConfigurationSchema()
        self.configFile["config"]["impl_to_use"] = "C"

        self.configFile["config"]["c"] = {}
        self.configFile["config"]["c"]["use_makefile"] = True
        self.configFile["config"]["c"]["clean_target"] = "clean"
        self.configFile["config"]["c"]["submission_name"] = ""

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testMissingLocationStarterCode(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["build"]["use_starter_code"] = True

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testMissingLocationDataFiles(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["build"]["use_data_files"] = True

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testMissingImplConfig(self):
        schema = self.createAutograderConfigurationSchema()

        self.configFile["config"]["python"] = None  # type: ignore

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testValidateImplValid(self):
        res = AutograderConfigurationSchema.validateImplSource("Python")

        self.assertTrue(res)

    def testValidateImplInvalid(self):
        res = AutograderConfigurationSchema.validateImplSource("DNE")

        self.assertFalse(res)

    def testAutograderRootDNE(self):
        schema = self.createAutograderConfigurationSchema()

        newDir = "autograder_root"

        self.configFile["autograder_root"] = newDir

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testAutograderRootNoConfig(self):
        schema = self.createAutograderConfigurationSchema()

        newDir = "autograder_root"

        if os.path.exists(newDir):
            shutil.rmtree(newDir)

        os.mkdir(newDir)

        self.configFile["autograder_root"] = newDir

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

        if os.path.exists(newDir):
            shutil.rmtree(newDir)

    def testAutograderRootValidWithConfig(self):
        schema = self.createAutograderConfigurationSchema()

        newDir = "autograder_root"

        if os.path.exists(newDir):
            shutil.rmtree(newDir)

        os.mkdir(newDir)

        with open(os.path.join(newDir, "config.toml"), 'w') as w:
            w.write("\n")

        self.configFile["autograder_root"] = newDir

        actual = schema.validate(self.configFile)


        if os.path.exists(newDir):
            shutil.rmtree(newDir)

        self.assertEqual(newDir, actual["autograder_root"])




