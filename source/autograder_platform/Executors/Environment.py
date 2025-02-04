import os
import tempfile
from typing import Callable, Generic, List, Dict, Optional, Tuple, Type, TypeVar, Union, Any

import dataclasses

ImplResults = TypeVar("ImplResults")


class Results(Generic[ImplResults]):
    class Files:
        def __init__(self, files: Optional[Dict[str, str]]):
            self.files = files

        def __getitem__(self, file: str) -> Union[str, bytes]:
            if self.files is None:
                raise AssertionError(f"Missing result data. Expected: 'files'.")
            if file not in self.files:
                raise AssertionError(f"File '{file}' was not created by the student's submission!")

            readFile: Union[str, bytes] = ""

            try:
                with open(self.files[file], 'r') as r:
                    readFile = r.read()
            except UnicodeDecodeError:
                with open(self.files[file], 'rb') as rb:
                    readFile = rb.read()

            return readFile

    def __init__(self, stdout=None, return_val=None, file_out=None, exception=None, parameters=None,
                 impl_results=None) -> None:
        self.stdout = stdout
        self.return_val = return_val
        self.file_out = file_out
        self.exception = exception
        self.parameter = parameters
        self.impl_results = impl_results

    @property
    def stdout(self) -> List[str]:
        if self._stdout is None:
            raise AssertionError(f"No OUTPUT was created by the student's submission.\n"
                                 f"Are you missing an 'OUTPUT' statement?")
        if not self._stdout:
            raise AssertionError(f"No OUTPUT was created by the student's submission.\n"
                                 f"Are you missing an 'OUTPUT' statement?")
        return self._stdout

    @stdout.setter
    def stdout(self, value: Optional[List[str]]):
        self._stdout = value

    @property
    def return_val(self) -> Optional[object]:
        return self._return_val

    @return_val.setter
    def return_val(self, value: Optional[object]):
        self._return_val = value

    @property
    def file_out(self) -> Files:
        return self._files

    @file_out.setter
    def file_out(self, value: Optional[Dict[str, str]]):
        self._files = Results.Files(value)

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    @exception.setter
    def exception(self, value: Optional[Exception]):
        self._exception = value

    @property
    def parameter(self) -> Tuple[Any, ...]:
        if self._parameter is None:
            raise AssertionError("No parameters were set!")

        return self._parameter

    @parameter.setter
    def parameter(self, value: Optional[Tuple[Any, ...]]):
        self._parameter = value

    @property
    def impl_results(self) -> ImplResults:
        if self._impl_results is None:
            raise AssertionError("No implementation results were set!")

        return self._impl_results

    @impl_results.setter
    def impl_results(self, value: Optional[ImplResults]):
        self._impl_results = value


ImplEnvironment = TypeVar("ImplEnvironment")


@dataclasses.dataclass
class ExecutionEnvironment(Generic[ImplEnvironment, ImplResults]):
    """
    Description
    ===========

    This class defines the execution environment for the student's submission. It controls what data
    is provided and what 'pre-run' tasks are completed (ie: creating a class instance).
    This class does not define the actual executor.
    """
    sandbox_location: str = "./sandbox"
    """The location for the sandbox folder"""
    stdin: List[str] = dataclasses.field(default_factory=list)
    """If stdin will be passed to the student's submission"""
    files: Dict[str, str] = dataclasses.field(default_factory=dict)
    """What files need to be added to the students submission. 
    The key is the file name, and the value is the file name with its relative path"""
    impl_environment: Optional[ImplEnvironment] = None
    """The implementation environment options. Can be None"""
    timeout: int = 10
    """What timeout has been defined for this run of the student's submission"""
    resultData: Optional[Results[ImplResults]] = None
    """
    This dict contains the data that was generated from the student's submission. This should not be accessed
    directly, rather, use getOrAssert method
    """

def getResults(environment: ExecutionEnvironment[ImplEnvironment, ImplResults]) -> Results[ImplResults]:
    """
    This method gets the results from the environment. 
    If they aren't populated, then an assertion error is raised.
    Results should be accessed directly from the Results object by their key name.
    :param environment: the execution environment.
    :raises AssertionError: if the results aren't populated.
    """
    if environment.resultData is None:
        raise AssertionError(
            "Results are were no populated! Student submission likely crashed before writing to results object")

    return environment.resultData


Builder = TypeVar("Builder", bound="ExecutionEnvironmentBuilder[Any, Any]")
ImplEnvironmentBuilder = TypeVar("ImplEnvironmentBuilder")


class ExecutionEnvironmentBuilder(Generic[ImplEnvironment, ImplResults]):
    """
    Description
    ===========

    This class helps build the execution environments.

    See :ref:`ExecutionEnvironment` for more information
    """

    def __init__(self):
        # windows doesn't clean out temp files by default (for compatibility reasons),
        # so we are going to be good boys and girls, and delete the *contents* of this folder at the end of a run.
        # however, as it is a different folder each time, we are going to silently fail.
        self.environment = ExecutionEnvironment[ImplEnvironment, ImplResults]()
        self.dataRoot = "."

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

    def setImplEnvironment(self: Builder, implEnvironmentBuilder: Type[ImplEnvironmentBuilder],
                           builder: Callable[[ImplEnvironmentBuilder], ImplEnvironment]) -> Builder:

        if self.environment.impl_environment is not None:
            raise EnvironmentError("ImplEnvironment has already been defined! Should be None!")

        self.environment.impl_environment = builder(implEnvironmentBuilder())

        return self

    def _setAndResolveSandbox(self):
        tempLocation = tempfile.mkdtemp(prefix="autograder_")

        self.environment.sandbox_location = tempLocation

        for src, dest in self.environment.files.items():
            self.environment.files[src] = os.path.join(self.environment.sandbox_location, dest)

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

    def build(self) -> ExecutionEnvironment[ImplEnvironment, ImplResults]:
        """
        Description
        ---
        This function validates that the execution environment is valid and then returns the environment.

        :returns: The build environment
        """

        self._setAndResolveSandbox()

        self._validate(self.environment)

        return self.environment
