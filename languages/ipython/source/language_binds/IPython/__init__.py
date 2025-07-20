from autograder_platform.Registration.LanguageRegistration import LanguageRegistrationMetadata, register_language
from language_binds.Python import PythonConfigSchema
from language_binds.Python.PythonEnvironment import PythonEnvironment, configMapper

from language_binds.IPython.IPythonSubmission import IPythonSubmission
from language_binds.Python.PythonSubmissionProcess import RunnableStudentSubmission

__version__ = "1.0.0.RC-2"

metadata = LanguageRegistrationMetadata(
    name="ipython",
    version=__version__,
    on_submission_process_factory_registration= \
        lambda: (IPythonSubmission, RunnableStudentSubmission, PythonEnvironment, configMapper),
    on_config_registration=PythonConfigSchema,
)

register_language(metadata)

