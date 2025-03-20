import os

from autograder_utils.ResultBuilders import prairieLearnResultBuilder
from autograder_utils.ResultFinalizers import prairieLearnResultFinalizer
from autograder_utils.JSONTestRunner import JSONTestRunner

# CLI tools should only be able to import from the CLI part of the library
from autograder_platform.cli import AutograderCLITool
from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfiguration


class PrairieLearnAutograderCLI(AutograderCLITool):
    def __init__(self):
        super().__init__("PrairieLearn")

    def configure_options(self):  # pragma: no cover
        self.parser.add_argument("--results-location", default="/grade/results/results.json",
                                 help="The location for the autograder JSON results")
        self.parser.add_argument("--metadata-path", default="/grade/data/data.json",
                                 help="The location for the submission metadata JSON")
        self.parser.add_argument("--autograder-root", default="/grade/tests",
                                 help="The base location for the autograder")
        self.parser.add_argument("--test-directory", default="student_tests",
                                 help="The location for the student tests")
        self.parser.add_argument("--submission-directory", default="/grade/student",
                                 help="The directory where the student's submission is located")

    def set_config_arguments(self, configBuilder: AutograderConfigurationBuilder[AutograderConfiguration]):  # pragma: no cover
        if self.arguments is None:
            return

        configBuilder.setStudentSubmissionDirectory(self.arguments.submission_directory)
        configBuilder.setAutograderRoot(self.arguments.autograder_root)
        configBuilder.setTestDirectory(str(os.path.join(self.arguments.autograder_root, self.arguments.test_directory)))

    def run(self) -> bool:  # pragma: no cover
        self.configure_options()

        self.load_config()

        if self.arguments is None:
            return True

        self.discover_tests()

        with open(self.arguments.results_location, 'w') as w:
            testRunner = JSONTestRunner(visibility='visible', stream=w,
                                        result_builder=prairieLearnResultBuilder,
                                        result_finalizer=prairieLearnResultFinalizer)

            res = testRunner.run(self.tests)

            return not res.wasSuccessful()


tool = PrairieLearnAutograderCLI().run

if __name__ == "__main__":
    res = tool()

    exit(res)

