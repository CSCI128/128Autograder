import dataclasses
from typing import Generic, TypeVar, Optional, Tuple, Any, Type
from collections.abc import Callable

from autograder_platform.Executors.Environment import ImplEnvironment
from autograder_platform.StudentSubmission.AbstractStudentSubmission import AbstractStudentSubmission
from autograder_platform.StudentSubmission.ISubmissionProcess import ISubmissionProcess
from autograder_platform.StudentSubmission.SubmissionProcessFactory import SubmissionProcessFactory
from autograder_platform.config import Config
from autograder_platform.config.Config import AutograderConfiguration, AutograderConfigurationSchema
from autograder_platform.config.BaseSchema import BaseSchema

LanguageConfigType = TypeVar('LanguageConfigType')


@dataclasses.dataclass
class LanguageRegistrationMetadata(Generic[LanguageConfigType]):
    name: str
    version: str

    on_submission_process_factory_registration: Callable[
        [],
        Tuple[
            Type[AbstractStudentSubmission[Any]],
            Type[ISubmissionProcess],
            Optional[Type[ImplEnvironment]],
            Optional[Callable[[ImplEnvironment, AutograderConfiguration], None]]
        ],
    ]

    on_config_registration: Optional[Callable[[], BaseSchema[LanguageConfigType]]] = None

def register_language(metadata: LanguageRegistrationMetadata):
    if metadata.on_config_registration is not None:
        AutograderConfigurationSchema.register_sub_schema(metadata.name, metadata.on_config_registration())

    SubmissionProcessFactory.register(*metadata.on_submission_process_factory_registration())

