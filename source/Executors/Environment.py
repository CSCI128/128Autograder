from importlib import import_module
from importlib.abc import MetaPathFinder
import os
from types import ModuleType
from typing import List, Dict, Optional, Tuple, TypeVar, Union, Any
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

T = TypeVar("T", str, Exception, object)

@dataclasses.dataclass
class ExecutionEnvironment:
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
    import_loader: List[MetaPathFinder] = dataclasses.field(default_factory=list)
    """The import loader. This shouldn't be set directly"""
    mocks: Dict[str, Optional[SingleFunctionMock]] = dataclasses.field(default_factory=dict)
    """What mocks have been defined for this run of the student's submission"""
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

Builder = TypeVar("Builder", bound="ExecutionEnvironmentBuilder")

class ExecutionEnvironmentBuilder():
    """
    Description
    ===========

    This class helps build the execution environments.

    See :ref:`ExecutionEnvironment` for more information
    """

    def __init__(self, submission: AbstractStudentSubmission):
        self.environment = ExecutionEnvironment(submission)
        self.dataRoot = "."
        self.parameters: List[Any] = []
        self.moduleMocks: Dict[str, Dict[str, object]] = {}

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

    def addModuleMock(self: Builder, moduleName: str, mockedMethods: Dict[str, object]) -> Builder:
        """
        Description
        ---
        This function sets up a mock for a complete module. 
        All mocks must be the same 'level' meaning we cant mock a.b.fun and a.fun. We have to choose. 

        We also  cant mock both a.b and a in the same submission currently without mocking the entirety of a.

        :param moduleName: The name of the module that will be mocked.
        :param mockedMethods: the map of the methods to mock in the module
        """
        if moduleName in self.moduleMocks:
            for mockName, mockObject in mockedMethods.items():
                self.moduleMocks[moduleName][mockName] = mockObject

            return self

        self.moduleMocks[moduleName] = mockedMethods

        return self

    def addMock(self: Builder, mockName: str, mockObject: SingleFunctionMock) -> Builder:
        """
        This needs to be updated once we decide how to do mocks
        """
        self.environment.mocks[mockName] = mockObject

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

    def addImportHandler(self: Builder, importHandler: MetaPathFinder) -> Builder:
        """
        Description
        ---
        This adds an import handler to the environment

        :param importHandler: the meta path finder
        """
        self.environment.import_loader.append(importHandler)

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

    def _processAndValidateModuleMocks(self):
        try:
            from StudentSubmissionImpl.Python.PythonModuleImportFactory import ModuleFinder
        except ImportError:
            return

        for moduleName in self.moduleMocks.keys():
            try:
                module = import_module(moduleName)
            except ImportError:
                raise AttributeError(f"Failed to import {moduleName}!")

            for methodName, mock in self.moduleMocks[moduleName].items():
                splitName = methodName.split('.')

                if not isinstance(mock, SingleFunctionMock):
                    raise AttributeError(f"Invalid mock for {methodName}")

                if mock.spy:
                    mock.setSpyFunction(getattr(module, splitName[-1]))

                self.environment.mocks[methodName] = None
                setattr(module, splitName[-1], mock)

            self.environment.import_loader.append(ModuleFinder(moduleName, module))

    def build(self) -> ExecutionEnvironment:
        """
        Description
        ---
        This function validates that the execution environment is valid and then returns the environment.

        :returns: The build environment
        """
        self.environment.parameters = tuple(self.parameters)
        
        self._processAndValidateModuleMocks()

        self._validate(self.environment)
        
        return self.environment
