"""
This module provides an interface for running student submissions as processes.

This module utilizes shared memory to share data from the parent and the child. The way it is currently implemented
guarantees that no conflicts will occur with the pattern. This is because the parent waits for the child to complete
before attempting to even connect to the object.

:author: Gregory Bell
:date: 3/7/23
"""

from typing import Any, Dict, Optional, TextIO, Tuple, List, Union
from autograder_platform.Executors.Environment import ExecutionEnvironment, Results

from autograder_platform.StudentSubmission.ISubmissionProcess import ISubmissionProcess

import dill
import multiprocessing
import multiprocessing.shared_memory as shared_memory
import os
import sys
from io import StringIO

from autograder_platform.Executors.common import MissingOutputDataException, detectFileSystemChanges, filterStdOut
from autograder_platform.StudentSubmissionImpl.Python.common import PythonTaskResult
from autograder_platform.Tasks.TaskRunner import TaskRunner
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock
from autograder_platform.StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironment, PythonResults
from autograder_platform.StudentSubmissionImpl.Python.AbstractPythonImportFactory import AbstractModuleFinder

dill.Pickler.dumps, dill.Pickler.loads = dill.dumps, dill.loads  # type: ignore
multiprocessing.reduction.dump = dill.dump  # type: ignore

class StudentSubmissionProcess(multiprocessing.Process):
    """
    This class extends multiprocessing.Process to provide a simple way to run student submissions.
    This class runs the 'runner' that it receives from the parent in a separate process and shares all data collected
    (returns, stdout, and exceptions) with the parent who is able to unpack it. Currently, stderror is ignored.

    Depending on the platform the process will be spawned using either the 'fork' or 'spawn' methods.
    Windows only supports the 'spawn' method and the 'spawn' method is preferred on macOS. This is why we aren't using
    pipes; when a process is created via the 'spawn' method, a new interpreter is started which doesn't share resources
    in the same way that a child process created via the 'fork' method. Thus, pipes fail on non Linux platforms.

    The other option of using multiprocessing.Pipe was also considered, but it ran in to similar issues as the
    traditional pipe method. There is a way to make it work, but it would involve overriding the print function to
    utilize the Pipe.send function, but that was a whole host of edge cases that I did not want to consider and also
    seemed like an easy way to confuse students as to why their print function behaved weird in the autograder, but not
    on their computers.

    Please be aware that the data does not generally persist after the child is started as it is a whole new context on
    some platforms. So data must be shared via some other mechanism. I choose multiprocessing.shared_memory due to the
    limitations listed above.

    This class is designed to a one-size-fits-all type of approach for actually *running* student submissions as I
    wanted to avoid the hodgepodge of unmaintainable that was the original autograder while still affording the
    flexibility required by the classes that will utilize it.
    """

    def __init__(self, runner: TaskRunner, executionDirectory: str, importHandlers: List[AbstractModuleFinder],
                 timeout: int = 10):
        """
        This constructs a new student submission process with the name "Student Submission".

        It sets the default names for shared input and output.
        Those should probably be updated.

        :param runner: The submission runner to be run in a new process. Can be any callable object (lamda, function,
        etc). If there is a return value it will be shared with the parent.


        :param executionDirectory: The directory that this process should be running in. This is to make sure that all
        data is isolated for each run of the autograder.

        :param timeout: The _timeout for join. Basically, it will wait *at most* this amount of time for the child to
        terminate. After this period passes, the child must be killed by the parent.
        """
        super().__init__(name="Student Submission")
        self.runner: TaskRunner = runner
        self.inputDataMemName: str = ""
        self.outputDataMemName: str = ""
        self.executionDirectory: str = executionDirectory
        self.importHandlers: List[AbstractModuleFinder] = importHandlers
        self.timeout: int = timeout

    def setInputDataMemName(self, inputSharedMemName):
        """
        Updates the input data memory name from the default

        :param inputSharedMemName: The shared memory name (see :ref:`multiprocessing.shared_memory`) for stdin.
        The data at this location is stored as a list
        and must be processed into a format understood by ``StringIO``.
        The data must exist before the child is started.
        """
        self.inputDataMemName: str = inputSharedMemName

    def setOutputDataMenName(self, outputDataMemName):
        """
        Updates the output data memory name from the default.

        :param outputDataMemName: The shared memory name (see :ref:`multiprocessing.shared_memory`) for exceptions and
        return values.
        This is created by the child and will be connected to by the parent once the child exits.
        """
        self.outputDataMemName = outputDataMemName

    def _setup(self) -> None:
        """
        Sets up the child input output redirection. The stdin is read from the shared memory object defined in the parent
        with the name ``self.inputDataMemName``. The stdin is formatted with newlines so that ``StringIO`` is able to
        work with it.

        This method also moves the process to the execution directory

        stdout is also redirected here, but because we don't care about its contents, we just overwrite it completely.

        This method also injects whatever import MetaPathFinders
        """
        # This may error? so we are going to catch it and log the error
        try:
            os.chdir(self.executionDirectory)
        except OSError as ex:  # pragma: no coverage
            print(f"ERROR: Failed to change directory to sandbox folder.\n{ex}", file=sys.stderr)  # pragma: no coverage


        sys.path.append(os.getcwd())

        for importHandler in self.importHandlers:
            sys.meta_path.insert(0, importHandler)

            mods = importHandler.getModulesToReload()
            for mod in mods:
                if mod not in sys.modules:
                    continue

                del sys.modules[mod]

        sharedInput = shared_memory.SharedMemory(self.inputDataMemName)
        deserializedData = dill.loads(sharedInput.buf.tobytes())
        # Reformat the stdin so that we
        sys.stdin = StringIO("".join([line + "\n" for line in deserializedData]))

        sys.stdout = StringIO()

    def _teardown(self, stdout: Union[StringIO, TextIO], exception: Optional[Exception],
                  returnValue: object, parameters: Optional[Tuple[object, ...]],
                  mocks: Optional[Dict[str, Optional[SingleFunctionMock]]]) -> None:
        """
        This function takes the results from the child process and serializes them.
        Then is stored in the shared memory object that the parent is able to access.

        :param stdout: The raw io from the stdout.
        :param exception: Any exceptions that were thrown
        :param returnValue: The return value from the function
        :param mocks: The mocks from the submission after they have been hydrated
        """

        if isinstance(stdout, TextIO):
            stdout.seek(0)
            stdout = StringIO(stdout.read())

        # Pickle both the exceptions and the return value
        dataToSerialize: Dict[str, Any] = {
            "stdout": stdout.getvalue().splitlines(),
            "parameters": parameters,
            "return_val": returnValue,
            "exception": exception,
            "impl_results": {
                "mocks": mocks,
            },
        }

        for importHandler in self.importHandlers:
            sys.meta_path.remove(importHandler)

        serializedData = dill.dumps(dataToSerialize, dill.HIGHEST_PROTOCOL)
        sharedOutput = shared_memory.SharedMemory(self.outputDataMemName)

        if sharedOutput.size < sys.getsizeof(serializedData):
            print(f"FATAL ERROR: Submission generated output is LARGER than buffer size of {sharedOutput.size} bytes. Output size is {sys.getsizeof(serializedData)} bytes!", file=sys.stderr)
            sharedOutput.close()
            return

        sharedOutput.buf[:len(serializedData)] = serializedData
        sharedOutput.close()

    def run(self):
        self._setup()

        exception: Optional[Exception] = None

        results: PythonTaskResult = self.runner.run()  # type: ignore

        if not self.runner.wasSuccessful():
            exceptions = self.runner.getAllErrors()
            if exceptions:
                exception = exceptions[0]

        if results is None:
            results = {
                "return_val": None,
                "parameters": None,
                "mocks": {},
            }

        self._teardown(sys.stdout, exception, results["return_val"], results["parameters"], results["mocks"])

    def join(self, *args, **kwargs):
        multiprocessing.Process.join(self, timeout=self.timeout)

    def terminate(self):
        # SigKill - cant be caught
        multiprocessing.Process.kill(self)
        # Checks to see if we are killed and cleans up process
        multiprocessing.Process.terminate(self)
        # Clean up the zombie
        multiprocessing.Process.join(self, timeout=0)


class RunnableStudentSubmission(ISubmissionProcess):

    def __init__(self):
        self.inputSharedMem: Optional[shared_memory.SharedMemory] = None
        self.outputSharedMem: Optional[shared_memory.SharedMemory] = None

        self.runner: Optional[TaskRunner] = None
        self.executionDirectory: str = "."
        self.studentSubmissionProcess: Optional[StudentSubmissionProcess] = None
        self.exception: Optional[Exception] = None
        self.outputData: Dict[str, Any] = {}
        self.timeoutOccurred: bool = False
        self.timeoutTime: int = 0
        self.bufferSize: int = 0

    def setup(self, environment: ExecutionEnvironment[PythonEnvironment, PythonResults], runner: TaskRunner):
        """
        Description
        ---

        This function allocates the shared memory that will be passed to the student's submission

        Setting up the data here then tearing it down in the ref:`RunnableStudentSubmission.cleanup` fixes
        the issue with windows GC cleaning up the memory before we are done with it as there will be at least one
        active hook for each memory resource til ``cleanup`` is called.


        """
        self.studentSubmissionProcess = \
            StudentSubmissionProcess(runner, environment.sandbox_location,
                                     environment.impl_environment.import_loader,
                                     environment.timeout)

        self.bufferSize = environment.impl_environment.buffer_size

        if self.bufferSize <= 0:
            raise AttributeError("INVALID STATE: Buffer size is ZERO. No data can be collected from the student's submission.")

        self.inputSharedMem = shared_memory.SharedMemory(create=True, size=self.bufferSize)
        self.outputSharedMem = shared_memory.SharedMemory(create=True, size=self.bufferSize)

        self.studentSubmissionProcess.setInputDataMemName(self.inputSharedMem.name)
        self.studentSubmissionProcess.setOutputDataMenName(self.outputSharedMem.name)

        serializedStdin = dill.dumps(environment.stdin, dill.HIGHEST_PROTOCOL)

        self.inputSharedMem.buf[:len(serializedStdin)] = serializedStdin

        self.timeoutTime = environment.timeout

    def run(self):
        if self.studentSubmissionProcess is None:
            raise AttributeError("Process has not be initialized!")

        self.studentSubmissionProcess.start()

        self.studentSubmissionProcess.join()

        if self.studentSubmissionProcess.is_alive():
            self.studentSubmissionProcess.terminate()
            self.timeoutOccurred = True

    def _deallocate(self):
        if self.inputSharedMem is None or self.outputSharedMem is None:
            return

        # `close` closes the current hook
        self.inputSharedMem.close()
        # `unlink` tells the gc that it is ok to clean up this resource
        #  On windows, `unlink` is a noop
        self.inputSharedMem.unlink()

        self.outputSharedMem.close()
        self.outputSharedMem.unlink()

    def cleanup(self):
        """
        This function cleans up the shared memory object by closing the parent hook and then unlinking it.

        After it is unlinked, the python garbage collector cleans it up.
        On windows, the GC runs as soon as the last hook is closed and `unlink` is a noop
        """

        if self.inputSharedMem is None or self.outputSharedMem is None:
            return

        if self.timeoutOccurred:
            self.exception = TimeoutError(f"Submission timed out after {self.timeoutTime} seconds")
            self._deallocate()
            return

        # This prolly isn't the best memory wise, but according to some chuckle head on reddit, this is superfast
        outputBytes = self.outputSharedMem.buf.tobytes()

        if outputBytes == bytearray(self.bufferSize):
            self.exception = MissingOutputDataException(self.outputSharedMem.name)
            self._deallocate()
            return

        deserializedData: Dict[str, Any] = dill.loads(outputBytes)

        self.outputData = deserializedData

        self._deallocate()

    def populateResults(self, environment: ExecutionEnvironment):
        if not self.outputData:
            self.outputData = {
                "stdout": None,
                "parameters": None,
                "return_val": None,
                "exception": self.exception,
                "impl_results": {
                    "mocks": None,
                },
            }

        self.outputData["file_out"] = detectFileSystemChanges(environment.files.values(), environment.sandbox_location)
        self.outputData["stdout"] = filterStdOut(self.outputData["stdout"])

        if "impl_results" in self.outputData:
            self.outputData["impl_results"] = PythonResults(**self.outputData["impl_results"])

        environment.resultData = Results(**self.outputData)

    @classmethod
    def processAndRaiseExceptions(cls, environment: ExecutionEnvironment):
        if environment.resultData is None:
            return

        exception = environment.resultData.exception

        if exception is None:
            return

        errorMessage = f"Submission execution failed due to an {type(exception).__qualname__} exception.\n" + str(
            exception)

        if isinstance(exception, EOFError):
            errorMessage += "\n" \
                            "Do you have the correct number of input statements?\n" \
                            "Are your loops terminating correctly?\n" \
                            "Is all your code in the if __name__ == __main__ block if you are using functions?"

        raise AssertionError(errorMessage)
