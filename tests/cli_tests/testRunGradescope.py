import os
import unittest
from unittest import mock
import json

from autograder_cli.run_gradescope import GradescopeAutograderCLI


# noinspection PyDataclass
class TestGradescopeUtils(unittest.TestCase):
    METADATA_PATH = "./metadata.json"

    def setUp(self) -> None:
        self.metadata = {
            "previous_submissions": []
        }

        self.autograderResults = {
            "tests": [
                {
                    "name": 'This is a test',
                    "status": 'passed',
                },

            ],
            "score": 0
        }
        self.gradescopeCLI = GradescopeAutograderCLI()

        self.gradescopeCLI.config = mock.Mock()
        self.gradescopeCLI.arguments = mock.Mock()
        self.gradescopeCLI.arguments.metadata_path = self.METADATA_PATH

    def tearDown(self) -> None:
        if os.path.exists(self.METADATA_PATH):
            os.remove(self.METADATA_PATH)

    def writeMetadata(self):
        with open(self.METADATA_PATH, 'w') as w:
            json.dump(self.metadata, w)

    def testNoPriorSubmissions(self):
        self.writeMetadata()

        self.autograderResults["score"] = 10

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testNegativeScore(self):
        self.writeMetadata()

        self.autograderResults["score"] = -1

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(0, self.autograderResults["score"])

    def testMetadataDoesntExist(self):
        # This should never happen, but if it does, then we are just going to accept the raw autograder results
        self.autograderResults["score"] = 10

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testHigherPriorSubmission(self):
        self.metadata["previous_submissions"].append({
            "results": {
                "score": 10
            }

        })

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 1000
        self.gradescopeCLI.config.config.take_highest = True


        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testLowerPreviousLimitExceeded(self):
        self.metadata["previous_submissions"].append({
            "results": {
                "score": 9
            }
        })

        self.metadata["previous_submissions"].append({
            "results": {
                "score": 9.5
            }
        })

        self.metadata["previous_submissions"].append({
            "results": {
                "score": 2
            }
        })

        self.autograderResults["score"] = 10

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True


        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(9.5, self.autograderResults["score"])

    def testLowerPrevious(self):
        self.metadata["previous_submissions"].append({
            "results": {
                "score": 9
            }
        })

        self.metadata["previous_submissions"].append({
            "results": {
                "score": 9.5
            }
        })

        self.autograderResults["score"] = 10

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True


        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testInvalidPreviousSubmission(self):
        self.metadata["previous_submissions"].append({
            "results": {}
        })

        self.metadata["previous_submissions"].append({
            "results": {}
        })

        self.autograderResults["score"] = 10

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 3
        self.gradescopeCLI.config.config.take_highest = True


        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testInvalidSubmissionInSubset(self):
        self.metadata["previous_submissions"].append({
            "results": {}
        })

        self.autograderResults["score"] = 10

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 1
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])

    def testMissingScore(self):
        del self.autograderResults["score"]

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 1
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertIn("Autograder run was INVALID", self.autograderResults["output"])

    def testMissingMetadata(self):
        self.gradescopeCLI.config.config.submission_limit = 1
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertIn("Autograder run was INVALID", self.autograderResults["output"])

    def testIgnoreFailedRuns(self):
        for _ in range(100):
            self.metadata["previous_submissions"].append({
                "results": {}
            })

        self.autograderResults["score"] = 10

        self.writeMetadata()

        self.gradescopeCLI.config.config.submission_limit = 1
        self.gradescopeCLI.config.config.take_highest = True

        self.gradescopeCLI.gradescope_post_processing(self.autograderResults)

        self.assertEqual(10, self.autograderResults["score"])


    # TODO Add test for score greater than autograder score
    # TODO Add test for not enforcing submission limit
