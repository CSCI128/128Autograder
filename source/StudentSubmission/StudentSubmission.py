"""
This class exposes a student submission to a test suite.
It helps facitate the reading of a submission, the standard i/o of a submission,
and the running of functions and classes with in a submission.

MUST SUPPORT:
-   tracing AST for disallowed functions
-   providing an interface for calling functions
-   provide an interface for calling classes
-   standard i/o mocking
-   discovering student submissions
-   supporting multiple files

"""
import ast
import multiprocessing
import os
from io import StringIO

import dill

from .RunnableStudentSubmission import RunnableStudentSubmission

# We need to use the dill pickle-ing library to pass functions in the processes
dill.Pickler.dumps, dill.Pickler.loads = dill.dumps, dill.loads
multiprocessing.reduction.dump = dill.dump


class StudentSubmission:
    def __init__(self, _submissionDirectory: str, _disallowedFunctionSignatures: list[str] | None):
        mainModuleTuple = StudentSubmission._discoverMainModule(_submissionDirectory)
        self.studentMainModule: ast.Module = mainModuleTuple[0]
        self.validationError: str = mainModuleTuple[1]
        self.isValid: bool = True if self.studentMainModule else False

        self.disallowedFunctionCalls: list[ast.Call] = \
            StudentSubmission._generateDisallowedFunctionCalls(_disallowedFunctionSignatures) \
                if _disallowedFunctionSignatures else []

    @staticmethod
    def _discoverMainModule(_submissionDirectory: str) -> (ast.Module, str):
        """
        @brief This function locates the main module
        """
        if not (os.path.exists(_submissionDirectory) and not os.path.isfile(_submissionDirectory)):
            return None, "Validation Error: Invalid student submission path"

        fileNames: list[str] = [file for file in os.listdir(_submissionDirectory) if file[-3:] == ".py"]

        if len(fileNames) == 0:
            return None, "Validation Error: No .py files were found"
        fileName: str = ""

        if len(fileNames) == 1:
            fileName = _submissionDirectory + fileNames[0]
        else:
            # If using multiple files, must have one called main.py
            filteredFiles: list[str] = [file for file in fileNames if file == "main.py"]
            if len(filteredFiles) == 1:
                fileName = _submissionDirectory + filteredFiles[0]

        if not fileName:
            return None, "Validation Error: Unable to find main file"

        pythonProgramText: str | None = None

        try:
            pythonProgramText = open(fileName, 'r').read()
        except Exception as ex_g:
            return pythonProgramText, f"IO Error: {type(ex_g).__qualname__}"

        parsedPythonProgram: ast.Module | None = None

        try:
            parsedPythonProgram = ast.parse(pythonProgramText)

        except SyntaxError as ex_se:
            return parsedPythonProgram, f"Syntax Error: {ex_se.msg} on line {ex_se.lineno}"

        return parsedPythonProgram, ""

    @staticmethod
    def _generateDisallowedFunctionCalls(_disallowedFunctionSignatures: list[str]) -> list[ast.Call]:
        """
        @brief This function processes a list of strings and converts them into AST function calls.
        It will discard any mismatches.

        @param _disallowedFunctionSignatures: The list of functions calls to convert to AST function calls

        @returns A list of AST function calls
        """

        astCalls: list[ast.Call] = []

        for signature in _disallowedFunctionSignatures:
            try:
                expr: ast.expr = ast.parse(signature, mode="eval").body
                if not isinstance(expr, ast.Call):
                    print(
                        f"Failed to parse function signature: {signature}. Incorrect type: Parsed type is {type(expr)}")
                    continue
                astCalls.append(expr)
            except SyntaxError as ex_se:
                print(f"Failed to parse function signature: {signature}. Syntax error: {ex_se.msg}")
                continue

        return astCalls

    @staticmethod
    def _checkForInvalidFunctionCalls(_parsedPythonProgram: ast.Module, _disallowedFunctions: list[ast.Call]) -> \
            dict[str, int]:
        """
        @brief This function checks to see if any of the functions that a student used are on a 'black list' of disallowedFunctions.
        This function works by taking a parsed python script and walks the AST to see if any of the called functions are disallowed.

        @param _parsedPythonProgram: The parsed python module. Must be an AST module (ast.Module)
        @param _disallowedFunctions: The function 'black list'. But be a list of AST functions calls (ast.Call)

        @returns A dictionary containing the number of times each disallowed function was called
        """

        # validating function calls
        invalidCalls: dict[str, int] = {}
        # This walks through every node in the program and sees if it is invalid
        for node in ast.walk(_parsedPythonProgram):
            if type(node) is not ast.Call:
                continue
            # For now we are ignoring imported functions TODO: fix this
            if type(node.func) is ast.Attribute:
                continue
            for functionCall in _disallowedFunctions:
                # If we are blanket flagging the use of a function ie: flagging all uses of eval
                if node.func.id == functionCall.func.id and len(functionCall.args) == 0:
                    if functionCall.func.id not in invalidCalls.keys():
                        invalidCalls[functionCall.func.id] = 0

                    invalidCalls[functionCall.func.id] += 1
                    continue

                # If the function signature matches. Python is dynamically typed and types are evaluated while its
                #  running rather than at parse time. So just seeing if the id and number of arguments matches.
                #  This is also ignore star arguments.
                if node.func.id == functionCall.func.id and len(node.args) == len(functionCall.args):
                    # Using guilty til proven innocent approach
                    isInvalidCall = True
                    for i, arg in enumerate(functionCall.args):
                        # If the type in an in the argument is a variable and its an exclusive wild card (`_`) then
                        #  we dont care about whats there so skip
                        if type(arg) is ast.Name and arg.id == '_':
                            continue

                        # If there is a constant where there is a variable - then its a mismatch
                        if type(arg) is ast.Name and type(node.args[i]) is not ast.Name:
                            isInvalidCall = False
                            break

                        # If the constant values don't match - then its a mismatch
                        if (type(arg) is ast.Constant and type(node.args[i]) is ast.Constant) and arg.value is not \
                                node.args[i].value:
                            isInvalidCall = False
                            break

                    if isInvalidCall:
                        if functionCall.func.id not in invalidCalls.keys():
                            invalidCalls[functionCall.func.id] = 0

                        invalidCalls[functionCall.func.id] += 1

        return invalidCalls

    @staticmethod
    def _validateStudentSubmission(_studentMainModule: ast.Module, _disallowedFunctions: list[ast.Call]) -> (
            bool, str):

        # validating function calls
        invalidCalls: dict[str, int] = StudentSubmission._checkForInvalidFunctionCalls(_studentMainModule,
                                                                                       _disallowedFunctions)

        # need to roll import statements
        if not invalidCalls:
            return True, ""

        stringedCalls: str = ""
        for key, value in invalidCalls.items():
            stringedCalls += f"{key}: called {value} times\n"

        # TODO need to expand this to include the number of invalid calls
        return False, f"Invalid Function Calls\n{stringedCalls}"

    def validateSubmission(self):
        # If we already ran into a validation error when loading submission

        if not self.isValid:
            return

        validationTuple: (bool, str) = StudentSubmission._validateStudentSubmission(self.studentMainModule,
                                                                                    self.disallowedFunctionCalls)

        self.isValid = validationTuple[0]
        self.validationError = validationTuple[1]

    def isSubmissionValid(self) -> bool:
        return self.isValid

    def getValidationError(self) -> str:
        return self.validationError

    class TimeoutError(Exception):
        pass

    @staticmethod
    def _executeMainModule(_compiledPythonProgram, _stdin: list[str], timeout: int = 10) -> StringIO:
        runner: callable = lambda: exec(_compiledPythonProgram, {'__name__': "__main__"})

        submissionProcess: RunnableStudentSubmission = RunnableStudentSubmission(_stdin, runner, timeout)

        try:
            submissionProcess.run()
            # It shouldn't be possible fot this to throw an exception
        except Exception:
            raise

        if submissionProcess.getTimeoutOccurred():
            raise TimeoutError

        if submissionProcess.getExceptions():
            raise submissionProcess.getExceptions()

        return submissionProcess.getStdOut()

    def runMainModule(self, _stdIn: list[str], timeoutDuration: int = 10) -> (bool, list[str]):
        """
        @brief This function compiles and runs python code from the AST
        """
        if not self.isValid:
            return False, []

        try:
            compiledPythonProgram = compile(self.studentMainModule, "<student_submission>", "exec")
            # TODO explicitly handle some common error types
        except (SyntaxError, ValueError) as g_ex:
            return False, [f"A compile time error occurred. Execution type is {type(g_ex).__qualname__}", str(g_ex)]

        stdOut: list[str] = []

        try:
            capturedOutput = StudentSubmission._executeMainModule(compiledPythonProgram, _stdIn, timeoutDuration)
            capturedOutput.seek(0)
            stdOut = capturedOutput.getvalue().splitlines()
        except TimeoutError as to_ex:
            return False, [f"Submission timed out after {timeoutDuration} seconds."]
        except RuntimeError as rt_ex:
            # TODO need to expand this for EOF, stack overflow, and recursion
            return False, [f"A runtime occurred. {str(rt_ex)}"]
        except Exception as g_ex:
            return False, [f"Submission execution failed due to an {type(g_ex).__qualname__} exception.", str(g_ex)]

        stdOut = StudentSubmission.filterStdOut(stdOut)
        return True, stdOut

    @staticmethod
    def filterStdOut(_stdOut: list[str]) -> list[str]:
        """
        @brief This function takes in a list representing the output from the program. It includes ALL output,
        so lines may appear as 'NUMBER> OUTPUT 3' where we only care about what is right after the OUTPUT statement
        This is adapted from John Henke's implementation
        """

        filteredOutput: list[str] = []
        for line in _stdOut:
            if "output " in line.lower():
                filteredOutput.append(line[line.lower().find("output ") + 7:])

        return filteredOutput
