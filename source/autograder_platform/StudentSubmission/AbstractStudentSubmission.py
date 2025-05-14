import abc
from typing import Generic, List, Set, TypeVar, Dict, Type

from build import BuildSystemTableValidationError

from autograder_platform.StudentSubmission.ITransformer import ITransformer
from autograder_platform.StudentSubmission.common import ValidationError, ValidationHook

from autograder_platform.StudentSubmission.AbstractValidator import AbstractValidator
from autograder_platform.StudentSubmission.GenericValidators import SubmissionPathValidator

T = TypeVar("T")

# for some reason this has to be TBuilder??
Builder = TypeVar("TBuilder", bound="AbstractStudentSubmission[Any]")


class AbstractStudentSubmission(abc.ABC, Generic[T]):
    """
    Description
    ===========

    This class contains the abstract student submission.
    Basically, this enables more of a plug and play architecture for different submission models.

    This model also allows a cleaner and more consistent way to implement validation of the submission.

    You can implement: ref:`AbstractValidator` for your purpose and assign it a hook.
    Then, when we reach that phase of the submission, that hook will be validated.

    Subclasses must implement ``doLoad`` and ``doBuild``.
    Subclasses must also implement ``getExecutableSubmission`` which should return the submission in a state that can be executed 
    by whatever runner is implemented.

    For example, take a look at the Python (or coming soon, the C / C++) implementation.
    """
    def __init__(self):
        self.submissionRoot: str = "."
        self.validators: Dict[ValidationHook, Set[AbstractValidator]] = {}
        self.validationErrors: List[Exception] = []
        self.submissionTransformers: List[ITransformer] = []

        # default validators
        self.addValidator(SubmissionPathValidator())


    def setSubmissionRoot(self: Builder, submissionRoot: str) -> Builder:
        """
        Description
        ---
        
        Defines the root of the submission. 

        Should be a path to the ``student_work``

        :param submissionRoot: The root of the submission.
        :returns: self
        """
        self.submissionRoot = submissionRoot
        return self

    def addValidator(self: Builder, validator: AbstractValidator) -> Builder:
        """
        Description
        ---

        Adds a validator to run at the hook defined in the validator.

        Validators are provided a reference to the submission at setup time to gather 
        information that they need to know about the student's submission.
        
        The hook to use is determined by the abstract static method ``AbstractValidator.getValidationHook()``.

        Only one validator of each type is allowed, ie: If we pass two validators of type ValidateAST, 
        only the last one added will be run.
        This enforces the single responsibility principal.

        :param validator: the validator to add subject to the above information.
        :returns: self
        """
        hook = validator.getValidationHook()

        if hook not in self.validators.keys():
            self.validators[hook] = set()

        self.validators[hook].add(validator)
        return self

    def addTransformer(self: Builder, transformer: ITransformer) -> Builder:
        self.submissionTransformers.append(transformer)

        return self

    def runManualValidationHook(self, validatorType: Type[AbstractValidator]):
        if ValidationHook.MANUAL not in self.validators.keys():
            raise RuntimeError("Request to run manual hook, but no manual hooks have been defined!")

        ran = False
        for validator in self.validators[ValidationHook.MANUAL]:
            if isinstance(validator, validatorType):
                validator.setup(self)
                validator.run()
                self.validationErrors.extend(validator.collectErrors())
                # we are only allowed to have one of each type, so once we execute, we should break
                ran = True
                break

        if not ran:
            raise RuntimeError(f"Request to run manual hook {validatorType}, but that manual hook has not been defined!")

        if self.validationErrors:
            raise ValidationError(self.validationErrors)

    def runTransformers(self, submissionText: str) -> str:
        """
        Description
        ---

        Runs all transformers in the order added.
        This functionality allows the user to mutate student submissions, BUT should be used sparely.

        This is used with the iPython bindings to remove all the magic commands so that cells can be parsed into their
        AST representation.

        Transformers operate on the entire submission text, so keep that in mind when writing.

        :param submissionText: The student's entire submission text.
        Generally, should only be one file but is dependent on the implementation.
        :returns: The transformed submission.
        """

        for transformer in self.submissionTransformers:
            submissionText = transformer.transform(submissionText)

        return submissionText

    def _validate(self, validationHook: ValidationHook):
        if validationHook not in self.validators.keys():
            return

        for validator in self.validators[validationHook]:
            validator.setup(self)
            validator.run()
            self.validationErrors.extend(validator.collectErrors())

        if self.validationErrors:
            raise ValidationError(self.validationErrors)


    @abc.abstractmethod
    def doLoad(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def doBuild(self):
        raise NotImplementedError()
    
    def load(self: Builder) -> Builder:
        """
        Description
        ---

        Runs all validators attached to the ``LOAD`` hooks.

        This method calls the overriden ``doLoad`` method.

        This is step 1 in the submission pipeline.
        With the python version, this discovers submitted files and identifies the main module.

        The flow is:
        1. Run ``PRE_LOAD`` validation hook
        2. Run overriden ``doLoad``
        3. Run ``POST_LOAD`` validation hook

        :returns: self
        """
        self._validate(ValidationHook.PRE_LOAD)

        self.doLoad()

        self._validate(ValidationHook.POST_LOAD)
        return self

    def build(self: Builder) -> Builder:
        """
        Description
        ---
        
        Runs all validators attached to the ``BUILD`` hooks.

        This method calls the overriden ``doBuild`` method.

        This is step 2 in the submission pipeline.
        With the python version, this builds all the discovered files to the AST representation.

        The flow is:
        1. Run ``PRE_BUILD`` validation hook
        2. Run overriden ``doBuild``
        3. Run ``POST_BUILD`` validation hook

        :returns: self
        """
        self._validate(ValidationHook.PRE_BUILD)

        self.doBuild()

        self._validate(ValidationHook.POST_BUILD)
        return self

    def validate(self: Builder) -> Builder:
        """
        Description
        ---

        Runs all validators attached to the ``VALIDATION`` hook.

        This method should be overriden to perform any final validation that is needed prior to getting the executable version of the submission.

        :returns: self
        """
        self._validate(ValidationHook.VALIDATION)

        return self

    @abc.abstractmethod
    def getExecutableSubmission(self) -> T:
        pass

    def getSubmissionRoot(self) -> str:
        return self.submissionRoot

