from dataclasses import dataclass, field
import os
import shutil
from typing import Dict, List
import unittest

from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfigurationProvider
from autograder_platform.config.common import BaseSchema


@dataclass
class MockConfiguration:
    string_property: str
    int_property: int
    autograder_root: str = ""
    list_of_tables: List[Dict[str, str]] = field(default_factory=list)
    config: Dict = field(default_factory=dict)


class MockSchema(BaseSchema[MockConfiguration]):
    def __init__(self) -> None:
        pass

    def validate(self, data):
        return data

    def build(self, data) -> MockConfiguration:
        return MockConfiguration(**data)


class TestAutograderConfigurationBuilder(unittest.TestCase):
    DATA_DIRECTORY: str = "./testData/"
    DATA_FILE: str = os.path.join(DATA_DIRECTORY, "config.toml")

    def setUp(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)

        os.mkdir(self.DATA_DIRECTORY)

    def tearDown(self) -> None:
        if os.path.exists(self.DATA_DIRECTORY):
            shutil.rmtree(self.DATA_DIRECTORY)

    def testBuildValidConfig(self):
        expectedString = "TOML!"
        expectedInt = 5

        with open(self.DATA_FILE, 'w') as w:
            w.write(
                f"string_property = '{expectedString}'\n" \
                f"int_property = {expectedInt}\n"
            )

        actual = \
            AutograderConfigurationBuilder(configSchema=MockSchema()) \
                .fromTOML(file=self.DATA_FILE) \
                .build()

        self.assertEqual(expectedString, actual.string_property)
        self.assertEqual(expectedInt, actual.int_property)

    def testMalformedToml(self):
        expectedString = "TOML!"
        expectedInt = 5

        with open(self.DATA_FILE, 'w') as w:
            w.write(
                f"string_property: '{expectedString}'\n" \
                f"int_property = {expectedInt}\n"
            )

        with self.assertRaises(Exception):
            # Might want to wrap this in the future
            AutograderConfigurationBuilder(configSchema=MockSchema()) \
                .fromTOML(file=self.DATA_FILE) \
                .build()

    def testCreateKeyAsNeeded(self):
        expectedDir = "./huzzah"

        with open(self.DATA_FILE, 'w') as w:
            w.write(
                f"string_property = 'hello'\n" \
                f"int_property = 0\n"
            )

        actual = \
            AutograderConfigurationBuilder(configSchema=MockSchema()) \
                .fromTOML(file=self.DATA_FILE) \
                .setStudentSubmissionDirectory(expectedDir) \
                .setTestDirectory(expectedDir) \
                .setAutograderRoot(expectedDir) \
                .build()

        self.assertEqual(expectedDir, actual.config["student_submission_directory"])
        self.assertEqual(expectedDir, actual.config["test_directory"])
        self.assertEqual(expectedDir, actual.autograder_root)

    def testNoneDoesntModifyConfig(self):
        with open(self.DATA_FILE, 'w') as w:
            w.write(
                f"string_property = 'hello'\n" \
                f"int_property = 0\n"
            )

        actual = \
            AutograderConfigurationBuilder(configSchema=MockSchema()) \
                .fromTOML(file=self.DATA_FILE) \
                .setStudentSubmissionDirectory(None) \
                .setTestDirectory(None).build()  # type: ignore

        self.assertNotIn("test_directory", actual.config)
        self.assertNotIn("student_submission_directory", actual.config)

    def testNestedTableInList(self):
        expectedNested = [{'type': "int", 'value': 6}, {'type': "str", 'value': "huzzah!"}]

        with open(self.DATA_FILE, 'w') as w:
            w.write(
                f"string_property = 'hello'\n" \
                f"int_property = 0\n" \
                f"[[list_of_tables]]\n" \
                f"type='int'\n" \
                f"value=6\n" \
                f"[[list_of_tables]]\n" \
                f"type='str'\n" \
                f"value='huzzah!'\n"
            )

        actual = \
            AutograderConfigurationBuilder(configSchema=MockSchema()) \
                .fromTOML(file=self.DATA_FILE) \
                .build()

        self.assertEqual(actual.list_of_tables, expectedNested)


class TestAutograderConfigurationProvider(unittest.TestCase):
    # Ig i need tests for this??
    CONFIG = MockConfiguration("string!", 10)

    def testOnlyOneSetAllowed(self):
        AutograderConfigurationProvider.set(self.CONFIG)  # type: ignore

        with self.assertRaises(AttributeError):
            AutograderConfigurationProvider.set(self.CONFIG)  # type: ignore

        AutograderConfigurationProvider.config = None

    def testEmptyGetError(self):
        with self.assertRaises(AttributeError):
            AutograderConfigurationProvider.get()

        AutograderConfigurationProvider.config = None

    def testGetConfig(self):
        AutograderConfigurationProvider.set(self.CONFIG)  # type: ignore

        self.assertEqual(self.CONFIG, AutograderConfigurationProvider.get())

        AutograderConfigurationProvider.config = None
