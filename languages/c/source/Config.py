from dataclasses import dataclass


@dataclass(frozen=True)
class CConfiguration:
    """
    C/C++/C-Like Configuration
    ==========================

    This defines the extra parameters for when the autograder is running for c like languages
    """
    use_makefile: bool
    """
    If a makefile should be used for building
    """
    clean_target: str
    """
    The target that should be used to clean. Invoked as `make {clean_target}`
    """
    submission_name: str
    """
    The file name that should be executed
    """

    # Optional("c", default=None): Or({
    #     "use_makefile": bool,
    #     "clean_target": str,
    #     "submission_name": And(str, lambda x: len(x) >= 1)
    # }, None),
