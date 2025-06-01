from importlib import import_module
from types import CodeType, ModuleType
from typing import TypeVar, Tuple, List, Final, Optional, Dict, Callable, TypedDict, Union

from autograder_platform.StudentSubmission.common import InvalidRunner, MissingFunctionDefinition
# from language_binds.ipython.source.autograder_binds.IPython import IPythonSubmission
from autograder_binds.Python.PythonSubmission import PythonSubmission
from autograder_binds.Python.common import PythonTaskResult
from autograder_platform.Tasks.TaskRunner import TaskRunner
from autograder_platform.Tasks.Task import Task
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock

Builder = TypeVar('Builder', bound="PythonRunnerBuilder")

class RunMethodResult(TypedDict):
    return_val: object
    parameters: Tuple[object, ...]


class Parameter:
    def __init__(self, value: Optional[object] = None, autowiredName: Optional[str] = None):
        if value is not None and autowiredName is not None:
            raise InvalidRunner("Value and Autowire cannot both be defined.")

        if value is None and autowiredName is None:
            raise InvalidRunner("Exactly one of value and autowire must be defined.")

        self._useAutowire: Final[bool] = autowiredName is not None

        self._autowire: Final[str] = autowiredName

        self._value: Final[object] = value

    @property
    def useAutowire(self) -> bool:
        return self._useAutowire

    @property
    def autowire(self) -> str:
        if not self._useAutowire:
            raise AttributeError("Attempt to access autowire when autowire is null!")
        return self._autowire

    @property
    def value(self) -> object:
        if self._useAutowire:
            raise AttributeError("Attempt to access value when value is null!")
        return self._value

    def get(self, module: ModuleType) -> object:
        if not self.useAutowire:
            return self.value

        autowiredParam: Optional[object] = getattr(module, self.autowire, None)

        if autowiredParam is None:
            raise RuntimeError(
                f"INVALID STATE: Failed to map '{self.autowire}' to type when resolving autowired parameters!")

        return autowiredParam


class PythonTaskLibrary:

    @staticmethod
    def attemptToImport(submission: CodeType) -> ModuleType:
        module = ModuleType("submission")

        exec(submission, vars(module))

        return module

    @staticmethod
    def applyInjectedCode(module: ModuleType, codeToInject: List[CodeType]) -> None:
        for code in codeToInject:
            exec(code, vars(module))

    @staticmethod
    def applyMocks(module: ModuleType, mocks: Dict[str, Optional[SingleFunctionMock]]) -> None:
        """
        This function applies the mocks to the student's submission at the module level.

        :param module: the module to apply mocks to
        :param mocks: the dictionary of mocks to apply

        :raises AttributeError: If a mock name cannot be resolved
        """
        for mockName, mock in mocks.items():
            if mock is None:
                continue

            if mock.spy:
                mock.setSpyFunction(getattr(module, mockName))

            setattr(module, mockName, mock)

    @staticmethod
    def getMethod(module: ModuleType, methodToRun: str) -> Callable:
        method: Optional[Callable] = getattr(module, methodToRun, None)

        if method is None:
            raise MissingFunctionDefinition(methodToRun)

        return method

    @staticmethod
    def runMethod(module: ModuleType, methodToRun: Callable[..., object],
                  parameters: List[Parameter]) -> RunMethodResult:
        processedParameters = tuple([parameter.get(module) for parameter in parameters])

        returnVal = methodToRun(*processedParameters)

        return {"return_val": returnVal, "parameters": processedParameters}

    @staticmethod
    def runMain(submission: CodeType) -> None:
        # Currently parameters are unsupported :(

        exec(submission, {'__name__': "__main__"})

    @staticmethod
    def resolveMocks(mocks: Dict[str, Optional[SingleFunctionMock]]) -> Dict[str, SingleFunctionMock]:
        subscribedMocks = [mockName for mockName, mock in mocks.items() if mock is None]
        # TODO logging

        for mock in subscribedMocks:
            splitName = mock.split('.')
            functionName = splitName[-1]

            try:
                mod = import_module(".".join(splitName[:-1]))
            except Exception as ex:
                raise ImportError(
                    f"Failed to import '{splitName}' during mock resolution. This is likely an autograder error.\n{str(ex)}")

            mockedFunction: Optional[SingleFunctionMock] = getattr(mod, functionName, None)

            if mockedFunction is None:
                raise ImportError(
                    f"Failed to locate '{functionName}' in '{splitName[:-1]}' during mock resolution. This is likely an autograder error.")

            mocks[mock] = mockedFunction

        return mocks

    @staticmethod
    def aggregateResults(runMethodResults: Optional[RunMethodResult],
                         mocks: Dict[str, SingleFunctionMock]) -> PythonTaskResult:
        return {
            "return_val": runMethodResults["return_val"] if runMethodResults is not None else None,
            "parameters": runMethodResults["parameters"] if runMethodResults is not None else None,
            "mocks": mocks,
        }


class PythonRunnerBuilder:
    INJECTED_PREFIX: Final[str] = "INJECTED_"

    def __init__(self: Builder, submission: Union[PythonSubmission]):
        self.submission: Final[CodeType] = submission.getExecutableSubmission()
        self.parameters: List[Parameter] = []
        self.mocks: Dict[str, Optional[SingleFunctionMock]] = {}
        self.injectedMethods: Dict[str, CodeType] = {}
        self.setupMethods: List[str] = []
        self.useModuleEntrypoint: bool = False
        self.functionEntrypoint: Optional[str] = None

    def addParameter(self: Builder, value: object = None, parameter: Optional[Parameter] = None) -> Builder:
        if parameter is None:
            parameter = Parameter(value)

        self.parameters.append(parameter)

        return self

    def addMock(self: Builder, name: str, mock: SingleFunctionMock) -> Builder:
        if name in self.mocks:
            raise InvalidRunner(f"Mock '{name}' has already been added to the runner.")

        if mock is None:
            raise InvalidRunner(f"Injected mock '{name}' must be defined! \nIf you are trying to subscribe to the output of a module mock, use 'subscribeToMock'")

        self.mocks[name] = mock

        return self

    def subscribeToMock(self: Builder, name: str) -> Builder:
        if name in self.mocks:
            raise InvalidRunner(f"Mock '{name}' has already been added to the runner.")

        self.mocks[name] = None

        return self

    def addInjectedCode(self: Builder, name: str, src: Optional[str] = None,
                        code: Optional[CodeType] = None) -> Builder:
        if name[0: len(PythonRunnerBuilder.INJECTED_PREFIX)] != PythonRunnerBuilder.INJECTED_PREFIX:
            raise InvalidRunner(
                f"Injected methods must be prefixed with '{PythonRunnerBuilder.INJECTED_PREFIX}'. Was '{name}'.")

        if src is not None and code is not None:
            raise InvalidRunner(f"Multiple injected method implementations provided. Expected either source *or* code.")

        if src is None and code is None:
            raise InvalidRunner(f"No injected method implementation provided. Expected *exactly* one.")

        if src is not None:
            try:
                code = compile(src, name, "exec")
            except SyntaxError as syntaxError:
                raise InvalidRunner(
                    f"Syntax Error when compiling injected method!\nEnsure that you are using dill.getsource(..., lstrip=True,...)\n{syntaxError}")
            except ValueError:
                raise InvalidRunner(f"Null Bytes detected when compiling injected method!")

        self.injectedMethods[name] = code

        return self

    def addSetupMethod(self: Builder, setupMethodName: str) -> Builder:
        self.setupMethods.append(setupMethodName)

        return self

    def setEntrypoint(self: Builder, module: bool = False, function: Optional[str] = None) -> Builder:
        if module and function is not None:
            raise InvalidRunner(f"Duplicate entrypoints defined. Only one can be defined!")

        self.useModuleEntrypoint = module
        self.functionEntrypoint = function

        return self

    def build(self) -> TaskRunner:
        if not self.functionEntrypoint and not self.useModuleEntrypoint:
            raise InvalidRunner(f"No entrypoint defined!")

        if self.functionEntrypoint and (
                PythonRunnerBuilder.INJECTED_PREFIX in self.functionEntrypoint and self.functionEntrypoint not in self.injectedMethods):
            raise InvalidRunner(f"Injected method '{self.functionEntrypoint}' has not been injected!")

        if self.useModuleEntrypoint and len(self.parameters) != 0:
            raise InvalidRunner(
                f"Incompatible options! No parameters can be defined when using module entrypoint. Use a environment mock of the 'sys' module instead.")

        taskRunner = TaskRunner(PythonSubmission)

        if self.useModuleEntrypoint:
            taskRunner.add(Task("main", PythonTaskLibrary.runMain, [lambda: self.submission]))
            taskRunner.add(Task("resolve_mocks", PythonTaskLibrary.resolveMocks, [lambda: self.mocks]))
            taskRunner.add(Task("results", PythonTaskLibrary.aggregateResults,
                                [lambda: None, lambda: taskRunner.getResult("resolve_mocks")]), isOverallResultTask=True)
            return taskRunner

        taskRunner.add(Task("import", PythonTaskLibrary.attemptToImport, [lambda: self.submission]))
        taskRunner.add(Task("injection", PythonTaskLibrary.applyInjectedCode,
                            [lambda: taskRunner.getResult("import"), lambda: self.injectedMethods.values()]))
        taskRunner.add(Task("apply_mock", PythonTaskLibrary.applyMocks, [lambda: taskRunner.getResult("import"), lambda: self.mocks]))
        methodOrder = self.setupMethods

        for method in methodOrder:
            taskRunner.add(Task(f"get_{method}", PythonTaskLibrary.getMethod,
                                [lambda: taskRunner.getResult("import"), lambda: method]))
            taskRunner.add(Task(f"run_{method}", PythonTaskLibrary.runMethod,
                                [lambda: taskRunner.getResult("import"), lambda: taskRunner.getResult(f"get_{method}"),
                                 lambda: []]))

        taskRunner.add(Task(f"get_{self.functionEntrypoint}", PythonTaskLibrary.getMethod,
                            [lambda: taskRunner.getResult("import"), lambda: self.functionEntrypoint]))
        taskRunner.add(Task(f"run_{self.functionEntrypoint}", PythonTaskLibrary.runMethod,
                            [lambda: taskRunner.getResult("import"),
                             lambda: taskRunner.getResult(f"get_{self.functionEntrypoint}"), lambda: self.parameters]))

        taskRunner.add(Task("resolve_mocks", PythonTaskLibrary.resolveMocks, [lambda: self.mocks]))
        taskRunner.add(Task("results", PythonTaskLibrary.aggregateResults,
                            [lambda: taskRunner.getResult(f"run_{self.functionEntrypoint}"),
                             lambda: taskRunner.getResult("resolve_mocks")]), isOverallResultTask=True)

        return taskRunner
