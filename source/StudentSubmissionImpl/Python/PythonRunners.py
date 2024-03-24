from abc import abstractmethod
from importlib import import_module
from types import CodeType, ModuleType
from typing import Dict, Optional, Tuple, Any

from StudentSubmission.common import MissingFunctionDefinition, InvalidTestCaseSetupCode
from TestingFramework.SingleFunctionMock import SingleFunctionMock
from StudentSubmission.Runners import IRunner

class GenericPythonRunner(IRunner[CodeType]):
    """
    :Description:
    This class contains common code needed for each runner.

    A runner is a unit of execution that controls how the student's submission is executed.

    Child classes should implement ``Runner.run`` which is what is called at run time by
    ``RunnableStudentSubmissionProcess``.

    If mocks are supported by runner, then ``Runner.applyMocks`` should be called after the student is loaded into
    the current frame.
    """

    AUTOGRADER_SETUP_NAME: str = "autograder_setup"

    def __init__(self):
        self.studentSubmission: Optional[CodeType] = None
        self.mocks: Optional[Dict[str, Optional[SingleFunctionMock]]] = None
        self.parameters: Tuple[Any] = tuple()
        self.setupCode = None

    def setSubmission(self, submission: CodeType):
        self.studentSubmission = submission

    def setParameters(self, parameters: Tuple[Any]):
        self.parameters = parameters

    def getParameters(self) -> Tuple[Any]:
        return self.parameters

    def setMocks(self, mocks: Dict[str, Optional[SingleFunctionMock]]):
        self.mocks = mocks

    def getMocks(self) -> Optional[Dict[str, Optional[SingleFunctionMock]]]:
        return self.mocks

    def _resolveMocks(self):
        if self.mocks is None:
            return

        mocksToResolve = [ mockName for mockName, mock in self.mocks.items() if mock is None]
        # prolly add logging here

        for mock in mocksToResolve:
            splitName = mock.split('.')
            functionName = splitName[-1]

            try:
                mod = import_module(".".join(splitName[:-1]))
            except Exception as ex:
                raise ImportError(f"Failed to import {splitName} during mock resolution. This is likely an autograder error.\n{str(ex)}")

            mockedFunction: Optional[SingleFunctionMock] = getattr(mod, functionName, None)

            if mockedFunction is None:
                raise ImportError(f"Failed to locate {functionName} in {splitName[:-1]} during mock resolution. This is likely an autograder error.")

            self.mocks[mock] = mockedFunction

    def setSetupCode(self, setupCode):
        self.setupCode = compile(setupCode, "setup_code", "exec")

    def applyMocks(self, module: ModuleType) -> None:
        """
        This function applies the mocks to the student's submission at the module level.

        :param module: the module to apply mocks to 

        :raises AttributeError: If a mock name cannot be resolved
        """
        if not self.mocks:
            return

        for mockName, mock in self.mocks.items():
            if mock is None:
                continue

            if mock.spy:
                mock.setSpyFunction(getattr(module, mockName))

            setattr(module, mockName, mock)

    @abstractmethod
    def run(self):
        raise NotImplementedError("Must use implementation of runner.")

    def __call__(self):
        returnVal = self.run()

        self._resolveMocks()

        return returnVal


class MainModuleRunner(GenericPythonRunner):
    def run(self):
        if self.studentSubmission == None:
            raise RuntimeError("INVALID STATE: Submission was NONE when should be a non-none type!")

        exec(self.studentSubmission, {'__name__': "__main__"})


class FunctionRunner(GenericPythonRunner):

    def __init__(self, functionToCall: str):
        super().__init__()
        self.functionToCall: str = functionToCall

    def attemptToImport(self) -> ModuleType:
        if self.studentSubmission == None:
            raise RuntimeError("INVALID STATE: Submission was NONE when should be a non-none type!")

        importedModule: ModuleType = ModuleType("submission")

        exec(self.studentSubmission, vars(importedModule))

        return importedModule

    @staticmethod
    def getMethod(module: ModuleType, functionName: str):
        function = getattr(module, functionName, None)

        if function is None:
            raise MissingFunctionDefinition(functionName)

        return function

    def run(self):
        module = self.attemptToImport()
        
        self.applyMocks(module)

        if self.setupCode is not None:
            # apply to actual imported module
            exec(self.setupCode, vars(module))

            if self.AUTOGRADER_SETUP_NAME not in vars(module):
                raise InvalidTestCaseSetupCode()

            setUpCode = self.getMethod(module, self.AUTOGRADER_SETUP_NAME)

            setUpCode()

        functionToCall = self.getMethod(module, self.functionToCall)

        return functionToCall(*self.parameters)
