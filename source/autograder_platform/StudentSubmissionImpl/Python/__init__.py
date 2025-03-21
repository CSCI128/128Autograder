from autograder_platform.StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory
from autograder_platform.StudentSubmissionImpl.Python.PythonEnvironment import PythonEnvironment, configMapper

from autograder_platform.StudentSubmissionImpl.Python.PythonSubmission import PythonSubmission
from autograder_platform.StudentSubmissionImpl.Python.PythonSubmissionProcess import RunnableStudentSubmission

SubmissionProcessFactory.register(PythonSubmission, RunnableStudentSubmission, PythonEnvironment, configMapper)
