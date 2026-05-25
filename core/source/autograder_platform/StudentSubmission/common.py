from enum import Enum
from typing import List, Any


class ValidationHook(Enum):
    PRE_LOAD = 1
    POST_LOAD = 2
    PRE_BUILD = 3
    POST_BUILD = 4
    VALIDATION = 5
    MANUAL = 6


class MissingFunctionDefinition(Exception):
    def __init__(self, functionName: str):
        super().__init__(
            f"Failed to find function with name: {functionName}.\n"
            "Are you missing the function definition?"
        )

        self.functionName = functionName

    # https://stackoverflow.com/questions/16244923/how-to-make-a-custom-exception-class-with-multiple-init-args-pickleable
    # Basically - reduce has to return something that we construct the og class from
    def __reduce__(self):
        # Need to be (something,) so that it actually gets processed as a tuple in the pickler
        return MissingFunctionDefinition, (self.functionName,)


class InvalidTestCaseSetupCode(Exception):
    def __init__(self, *args):
        super().__init__(
            "Failed to find 'autograder_setup' function to run.\n"
            "Ensure that your setup code contains a 'autograder_setup' function.\n"
            "This is an autograder error."
        )


class StudentSubmissionException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ValidationError(Exception):
    @staticmethod
    def combineErrorMessages(exceptions: List[Exception]) -> str:
        msg = ""
        for i, ex in enumerate(exceptions):
            msg += f"{i + 1}. {type(ex).__qualname__}: {ex}\n"

        return msg

    def __init__(self, exceptions: List[Exception]):
        msg = self.combineErrorMessages(exceptions)

        super().__init__("Validation Errors:\n" + msg)


class InvalidRunner(Exception):
    def __init__(self, msg):
        super().__init__("Invalid Runner State: " + msg)
