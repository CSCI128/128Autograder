import os
from typing import Dict, Iterable, List, Optional


class MissingOutputDataException(Exception):
    def __init__(self, outputFileName):
        super().__init__("Output results are NULL.\n"
                         f"Failed to parse results in output buffer: {outputFileName}.\n"
                         f"Submission possibly crashed or terminated before harness could write to output buffer: {outputFileName}.\n"
                         f"Submission may have overrun buffer memory\n"
                         f"Likely causes: The presence of exit or quit in student's code; extra debugging print statements")

def filterStdOut(stdOut: Optional[List[str]]) -> Optional[List[str]]:
    """
    This function takes in a list representing the output from the program. It includes ALL output,
    so lines may appear as 'NUMBER> OUTPUT 3' where we only care about what is right after the OUTPUT statement
    This is adapted from John Henke's implementation

    :param _stdOut: The raw stdout from the program
    :returns: the same output with the garbage removed
    """

    if stdOut is None:
        return None

    filteredOutput: List[str] = []
    for line in stdOut:
        if "output " in line.lower():
            filteredOutput.append(line[line.lower().find("output ") + 7:])

    return filteredOutput

def detectFileSystemChanges(inFiles: Iterable[str], directoryToCheck: str) -> Dict[str, str]:
    files = [os.path.join(directoryToCheck, file) for file in os.listdir(directoryToCheck)]

    outputFiles: Dict[str, str] = {}

    # This ignores subfolders
    for path in files:
        if os.path.isdir(path):
            continue

        if "__" in os.path.basename(path):
            continue

        # ignore hidden files
        if os.path.basename(path)[0] == ".":
            continue

        if path in inFiles:
            continue

        outputFiles[os.path.basename(path)] = path

    return outputFiles
