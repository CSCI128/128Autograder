import os
from types import NoneType
from typing import Callable, Generic, List, Dict, Optional, Tuple, Type, TypeVar, Union, Any
from enum import Enum

import dataclasses
from StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from TestingFramework.SingleFunctionMock import SingleFunctionMock


class PossibleResults(Enum):
    STDOUT = "stdout"
    RETURN_VAL = "return_val"
    FILE_OUT = "file_out"
    MOCK_SIDE_EFFECTS = "mock"
    EXCEPTION = "exception"
    PARAMETERS = "parameters"

class Results():
    pass

ImplEnvironment = TypeVar("ImplEnvironment")

@dataclasses.dataclass
class ExecutionEnvironment(Generic[ImplEnvironment]):
    """
    Description
    ===========

    This class defines the execution environment for the student's submission. It controls what data
    is provided and what 'pre-run' tasks are completed (ie: creating a class instance).
    This class does not define the actual executor.
    """

    submission: AbstractStudentSubmission
    """The student submission that will be executed"""
    stdin: List[str] = dataclasses.field(default_factory=list)
    """If stdin will be passed to the student's submission"""
    files: Dict[str, str] = dataclasses.field(default_factory=dict)
    """What files need to be added to the students submission. 
    The key is the file name, and the value is the file name with its relative path"""
    parameters: Tuple[Any] = dataclasses.field(default_factory=tuple)
    """What arguments to pass to the submission"""
    impl_environment: Optional[ImplEnvironment] = None
    """The implementation environment options. Can be None"""
    timeout: int = 10
    """What timeout has been defined for this run of the student's submission"""
    resultData: Dict[PossibleResults, Any] = dataclasses.field(default_factory=dict)
    """
    This dict contains the data that was generated from the student's submission. This should not be accessed
    directly, rather, use getOrAssert method
    """

    SANDBOX_LOCATION: str = "./sandbox"


# TODO - Update this to be strongly typed
def getOrAssert(environment: ExecutionEnvironment,
                field: PossibleResults,
                file: Optional[str] = None,
                mock: Optional[str] = None) -> Union[Dict[str, object], object]:
    """
    This function gets the requested field from the results or will raise an assertion error.

    If a file is requested, the file name must be specified with the ``file`` parameter. The contents of the file
    will be returned.
    If a mock is requested, the mocked method's name must `also` be requested. The mocked method will be returned.
    :param environment: the execution environment that contains the results from execution
    :param field: the field to get data from in the results file. Must be a ``PossibleResult``
    :param file: if ``PossibleResults.FILE_OUT`` is specified, ``file`` must also be specified. This is the file
    name to load from.
    :param mock: if ``PossibleResults.MOCK_SIDE_EFFECT`` is specified, ``mock`` must also be specified. This is the
    mocked method name (usually from ``method.__name__``)

    :return: The requested data if it exists
    :raises AssertionError: if the data cannot be retrieved for whatever reason
    """
    resultData = environment.resultData

    if field not in resultData.keys():
        raise AssertionError(f"Missing result data. Expected: {field.value}.")

    if field is PossibleResults.STDOUT and not resultData[field]:
        raise AssertionError(f"No OUTPUT was created by the student's submission.\n"
                             f"Are you missing an 'OUTPUT' statement?")

    if field is PossibleResults.FILE_OUT and not file:
        raise AttributeError("File must be defined.")

    if field is PossibleResults.FILE_OUT and file not in resultData[PossibleResults.FILE_OUT].keys():
        raise AssertionError(f"File '{file}' was not created by the student's submission")


    if field is PossibleResults.MOCK_SIDE_EFFECTS and not mock:
        raise AttributeError("Mock most be defined.")

    if field is PossibleResults.MOCK_SIDE_EFFECTS \
            and mock not in resultData[PossibleResults.MOCK_SIDE_EFFECTS].keys():
        raise AttributeError(
            f"Mock '{mock}' was not returned by the student submission. This is an autograder error.")

    # now that all that validation is done, we can actually give the data requested lol

    if field is PossibleResults.FILE_OUT and file is not None:
        # load the file from disk and return it
        readFile: Union[str, bytes] = ""

        try:
            with open(resultData[field][file], 'r') as r:
                readFile  = r.read()
        except UnicodeDecodeError:
            with open(resultData[field][file], 'rb') as rb:
                readFile = rb.read()

        return readFile

    if field is PossibleResults.MOCK_SIDE_EFFECTS:
        return resultData[field][mock]

    return resultData[field]

Builder = TypeVar("Builder", bound="ExecutionEnvironmentBuilder[Any]")
ImplEnvironmentBuilder = TypeVar("ImplEnvironmentBuilder")

class ExecutionEnvironmentBuilder(Generic[ImplEnvironment]):
    """
    Description
    ===========

    This class helps build the execution environments.

    See :ref:`ExecutionEnvironment` for more information
    """

    def __init__(self, submission: AbstractStudentSubmission):
        self.environment = ExecutionEnvironment[ImplEnvironment](submission)
        self.dataRoot = "."
        self.parameters: List[Any] = []

    def setDataRoot(self: Builder, dataRoot: str) -> Builder:
        """
        Description
        ---
        This function sets the data root for the execution environment, 
        meaning what prefix should be added to all the files supplied to executor

        IE: if we had a file at ``tests/data/public/file.txt``, data root should be set to 
        ``tests/data`` or ``tests/data/public``

        :param dataRoot: the data root to use.
        """
        self.dataRoot = dataRoot

        return self

    def setStdin(self: Builder, stdin: Union[List[str], str]) -> Builder:
        """
        Description
        ---
        This function sets the STDIN to supply to the student's submission.

        This should be set to the number of input lines that the submission should use.

        If stdin is supplied as a string, it will be turned into a list seperated by newlines.

        :param stdin: Either a list of input strings or a string seperated by newlines (``\n``).
        """
        if isinstance(stdin, str):
            stdin = stdin.splitlines()

        self.environment.stdin = stdin

        return self

    def addParameter(self: Builder, parameter: Any) -> Builder:
        """
        Description
        ---
        This function adds a parameter to be passed to the submission. 
        During build, this is converted to an immutable tuple!
        Order is preverved.
        :param parameter: The parameter to pass to the submission
        """
        self.parameters.append(parameter)

        return self

    def addFile(self: Builder, fileSrc: str, fileDest: str) -> Builder:
        """
        Description
        ---
        This function adds a file to be pulled into the environment.

        :param fileSrc: The path to the file, relative to the specified data root. 
        IE: if we had a file at ``tests/data/public/file.txt``, and data root was set to ``tests/data``, 
        then ``fileSrc`` should be ``./public/file.txt``.
        :param fileDest: The path relative to ``SANDBOX_LOCATION`` that the file should be dropped at.
        """
        if fileSrc[0:2] == "./":
            fileSrc = fileSrc[2:]

        fileSrc = os.path.join(self.dataRoot, fileSrc)
        fileDest = os.path.join(self.environment.SANDBOX_LOCATION, fileDest)

        self.environment.files[fileSrc] = fileDest

        return self


    def setTimeout(self: Builder, timeout: int) -> Builder:
        """
        Description
        ---
        This function sets the timeout to kill the student's submission in if it doesn't end before that.

        The timeout must be integer greater than 1.

        :param timeout: The timeout to use.
        """

        self.environment.timeout = timeout

        return self

    def setImplEnviroment(self: Builder, implEnvironmentBuilder: Type[ImplEnvironmentBuilder], builder: Callable[[ImplEnvironmentBuilder], ImplEnvironment]) -> Builder:

        if self.environment.impl_environment is not None:
            raise EnvironmentError("ImplEnvironment has already been defined! Should be None!")

        self.environment.impl_environment = builder(implEnvironmentBuilder())
        
        return self


    @staticmethod
    def _validate(environment: ExecutionEnvironment):
        # For now this only validating that the files actually exist

        for src in environment.files.keys():
            if not os.path.exists(src):
                raise EnvironmentError(f"File {src} does not exist or is not accessible!")

        if not isinstance(environment.timeout, int):
            raise AttributeError(f"Timeout MUST be an integer. Was {type(environment.timeout).__qualname__}")

        if environment.timeout < 1:
            raise AttributeError(f"Timeout MUST be greater than 1. Was {environment.timeout}")

        # TODO - Validate requested features


    def build(self) -> ExecutionEnvironment[ImplEnvironment]:
        """
        Description
        ---
        This function validates that the execution environment is valid and then returns the environment.

        :returns: The build environment
        """
        self.environment.parameters = tuple(self.parameters)
        
        self._validate(self.environment)
        
        return self.environment
