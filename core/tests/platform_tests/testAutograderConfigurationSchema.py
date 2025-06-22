import os
import shutil
import unittest
from dataclasses import dataclass
from typing import Dict, Optional as OptionalType

from schema import Schema, Optional

from autograder_platform.config.BaseSchema import BaseSchema
from autograder_platform.config.Config import AutograderConfigurationSchema, InvalidConfigException, \
    AutograderConfiguration


@dataclass(frozen=True)
class TestImplConfig:
    a: bool
    required: bool

class SubSchema(BaseSchema[OptionalType[TestImplConfig]]):
    def __init__(self):
        self.schema: Schema = Schema({
            "test_impl": {
                Optional("a", default=False): bool,
                "required": bool,
            },
        }, ignore_extra_keys=True, name="TestImplSchema")

    def validate(self, data: Dict) -> Dict:
        if "test_impl" not in data:
            return data

        data["test_impl"] = self.schema.validate(data)["test_impl"]

        return data

    def build(self, data: Dict) -> OptionalType[TestImplConfig]:
        if "test_impl" not in data or not data["test_impl"]:
            return None

        return TestImplConfig(**data["test_impl"])

class TestAutograderConfigurationSchema(unittest.TestCase):

    def setUp(self) -> None:
        AutograderConfigurationSchema.register_sub_schema("test_impl", SubSchema())
        self.configFile = {
            "assignment_name": "HelloWold",
            "semester": "F99",
            "config": {
                "language_to_use": "test_impl",
                "autograder_version": "2.0.0",
                "test_directory": ".",
                "enforce_submission_limit": True,
                "perfect_score": 10,
                "max_score": 10,
            },
            "build": {
                "use_starter_code": False,
                "use_data_files": False,
                "build_student": True,
                "build_gradescope": True,
            },
            "test_impl": {
                "required": False,
            },
        }

    def tearDown(self):
        AutograderConfigurationSchema.deregister_sub_schema("test_impl")

    def testValidNoOptionalFields(self):
        schema = AutograderConfigurationSchema()

        actual = schema.validate(self.configFile)
        self.assertIn("submission_limit", actual["config"])

    def testValidOptionalFields(self):
        schema = AutograderConfigurationSchema()

        self.configFile["config"]["take_highest"] = True
        actual = schema.validate(self.configFile)
        self.assertIn("take_highest", actual["config"])
        self.assertEqual(False, actual["test_impl"]["a"])

    def testInvalidOptionalFields(self):
        schema = AutograderConfigurationSchema()

        self.configFile["config"]["take_highest"] = 10
        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testExtraFields(self):
        schema = AutograderConfigurationSchema()

        self.configFile["new_field"] = "This field shouldn't exist"

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testInvalidAutograderVersion(self):
        schema = AutograderConfigurationSchema()

        self.configFile["config"]["autograder_version"] = "0.0"

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testBuildNoOptional(self):
        schema = AutograderConfigurationSchema()

        data = schema.validate(self.configFile)

        actual = schema.build(data)

        self.assertEqual("F99", actual.semester)
        self.assertEqual(1000, actual.config.submission_limit)

    def testMissingLocationStarterCode(self):
        schema = AutograderConfigurationSchema()

        self.configFile["build"]["use_starter_code"] = True

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testMissingLocationDataFiles(self):
        schema = AutograderConfigurationSchema()

        self.configFile["build"]["use_data_files"] = True

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testMissingImplConfig(self):
        schema = AutograderConfigurationSchema()

        self.configFile["test_impl"] = None  # type: ignore

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testValidateImplValid(self):
        res = AutograderConfigurationSchema.validateImplSource("test_impl")

        self.assertTrue(res)

    def testValidateImplInvalid(self):
        res = AutograderConfigurationSchema.validateImplSource("DNE")

        self.assertFalse(res)

    def testAutograderRootDNE(self):
        schema = AutograderConfigurationSchema()

        newDir = "DNE"

        self.configFile["autograder_root"] = newDir

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testAutograderRootNoConfig(self):
        schema = AutograderConfigurationSchema()

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
        schema = AutograderConfigurationSchema()

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

    def testBuildSubSchema(self):
        schema = AutograderConfigurationSchema()

        self.configFile["test_impl"]["required"] = True

        validated = schema.validate(self.configFile)

        actual: AutograderConfiguration[TestImplConfig] = schema.build(validated)

        if actual.language_config is None:
            self.fail("language config was unexpectedly null")

        self.assertEqual(self.configFile["test_impl"]["required"], actual.language_config.required)
        self.assertEqual(False, actual.language_config.a)

    def testUndefinedSubSchema(self):
        schema = AutograderConfigurationSchema()
        self.configFile["config"]["language_to_use"] = "DNE"

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    @unittest.skip("For now, I dont think I want this to be an error")
    def testMultipleSubSchemas(self):
        schema = AutograderConfigurationSchema()
        self.configFile["new_sub_schema"] = {}

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)

    def testBuildUndefinedSubSchema(self):
        schema = AutograderConfigurationSchema()
        self.configFile["test_impl"] = None  # type: ignore

        with self.assertRaises(InvalidConfigException):
            schema.build(self.configFile)


    def testIncorrectImplConfig(self):
        schema = AutograderConfigurationSchema()

        self.configFile["new_sub_schema"] = {}
        del self.configFile["test_impl"]

        with self.assertRaises(InvalidConfigException):
            schema.validate(self.configFile)



