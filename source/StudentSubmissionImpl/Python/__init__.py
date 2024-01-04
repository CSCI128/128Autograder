from StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory

from StudentSubmissionImpl.Python.PythonSubmission import PythonSubmission
from StudentSubmissionImpl.Python.PythonSubmissionProcess import RunnableStudentSubmission

SubmissionProcessFactory.register(PythonSubmission, RunnableStudentSubmission)
