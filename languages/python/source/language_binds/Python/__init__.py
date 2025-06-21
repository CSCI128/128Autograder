from autograder_platform.Registration.LanguageRegistration import register_language, LanguageRegistrationMetadata
from language_binds.Python.Config import PythonConfigSchema
from language_binds.Python.PythonEnvironment import PythonEnvironment, configMapper

from language_binds.Python.PythonSubmission import PythonSubmission
from language_binds.Python.PythonSubmissionProcess import RunnableStudentSubmission

__version__ = "6.0.0.RC-1"

metadata = LanguageRegistrationMetadata(
    name="python",
    version=__version__,
    on_submission_process_factory_registration= \
        lambda: (PythonSubmission, RunnableStudentSubmission, PythonEnvironment, configMapper),
    on_config_registration=PythonConfigSchema,
)

register_language(metadata)
