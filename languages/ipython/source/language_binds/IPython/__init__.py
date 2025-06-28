from autograder_platform.StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory
from language_binds.Python.PythonEnvironment import PythonEnvironment, configMapper

from language_binds.IPython.IPythonSubmission import IPythonSubmission
from language_binds.Python.PythonSubmissionProcess import RunnableStudentSubmission

SubmissionProcessFactory.register(IPythonSubmission, RunnableStudentSubmission, PythonEnvironment, configMapper)

__version__ = "1.0.1.RC-1"
