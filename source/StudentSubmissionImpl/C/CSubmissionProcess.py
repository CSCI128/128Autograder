from pathlib import Path
import shutil
import os
from typing import List, Optional
import subprocess
from StudentSubmission.ISubmissionProcess import ISubmissionProcess
from StudentSubmissionImpl.C.CRunners import MainRunner
from Executors.Environment import ExecutionEnvironment, PossibleResults
from Executors.common import detectFileSystemChanges

class CSubmissionProcess(ISubmissionProcess):
    @staticmethod
    def stdinToBytes(stdin: List[str]) -> bytes:
        stringifiedStdin = "\n".join(stdin)

        return stringifiedStdin.encode()


    def setup(self, environment: ExecutionEnvironment, runner: MainRunner): # pyright: ignore[reportIncompatibleMethodOverride]
        self.absWorkingDirectory: str = str(Path(environment.SANDBOX_LOCATION).resolve())
        self.stdout: bytes = b""
        self.stdIn: bytes = self.stdinToBytes(environment.stdin)
        self.exception: Optional[Exception] = None
        self.exPath = os.path.join(self.absWorkingDirectory, os.path.basename(runner.getSubmission()))
        self.timeoutTime = environment.timeout
        self.timeoutOccurred: bool = False

        # move submission into sandbox
        shutil.copy(runner.getSubmission(), self.exPath)
        # currently only stdOut is only supported
        
    def run(self):
        try:
            process = subprocess.Popen(self.exPath, cwd=self.absWorkingDirectory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            try:
                self.stdout, _ = process.communicate(self.stdIn, timeout=self.timeoutTime)

            except subprocess.TimeoutExpired:
                process.kill()
                self.timeoutOccurred = True
            except Exception as e:
                self.exception = RuntimeError(f"An error occured while running student submission! {str(e)}")
        except OSError as e:
            self.exception = Exception(f"Failed to start student submission! Error is:\n{str(e)}")

    def cleanup(self):
        if self.timeoutOccurred:
            self.exception = TimeoutError(f"Submission timed out after {self.timeoutTime} seconds")
            return


    def populateResults(self, environment: ExecutionEnvironment):
        environment.resultData[PossibleResults.EXCEPTION] = self.exception

        environment.resultData[PossibleResults.STDOUT] = self.stdout.decode().splitlines()

        environment.resultData[PossibleResults.FILE_OUT] =\
                detectFileSystemChanges(environment.files.values(), environment.SANDBOX_LOCATION)

        environment.resultData[PossibleResults.RETURN_VAL] = None

        environment.resultData[PossibleResults.MOCK_SIDE_EFFECTS] = {}



    @classmethod
    def processAndRaiseExceptions(cls, environment: ExecutionEnvironment):
        exception = environment.resultData[PossibleResults.EXCEPTION]
        if exception is None:
            return

        errorMessage = f"Submission execution failed due to an {type(exception).__qualname__} exception.\n" + str(exception)

        if isinstance(exception, EOFError):
            errorMessage += "\n" \
                            "Do you have the correct number of input statements?"

        raise AssertionError(errorMessage)
