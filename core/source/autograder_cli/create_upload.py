import getpass
import os
import sys
from zipfile import ZipFile


def buildZipName() -> str:
    """
    This function generates the zip file name and sets a fallback if the user's name can't be determined
    :return: the generated zip file name
    """
    DEFAULT_NAME: str = "csci_128_student"
    zipName: str = ""

    try:
        # Get user can throw an exception if it fails to look up the username in the password database
        userName = getpass.getuser().lower()
        # replace spaces with underscore bc spaces make me sad
        userName = userName.replace(" ", "_")

        zipName += userName

    except KeyError:
        print(f"Can't automatically determine user name. Defaulting to {DEFAULT_NAME}")
        zipName += DEFAULT_NAME

    zipName += "-submission"
    zipName += ".zip"

    return zipName


def addFolderToZip(_currentZipBuffer: ZipFile, _directoryToAdd: str) -> None:
    """
    This function allows us to recursively descend through the directory structure to
    collect all of a student's submitted files
    :param _currentZipBuffer: the zip file that is currently being written.
    :param _directoryToAdd: the directory that needs to be added
    """

    # Ignore hidden directories
    if _directoryToAdd[0] == ".":
        return

    # Ignore directories python directories
    if "__" in _directoryToAdd:
        return

    print(f"\tEntering {_directoryToAdd}...")

    for file in os.listdir(_directoryToAdd):
        if os.path.isfile(_directoryToAdd + file) and file[-3:] == ".py":
            print(f"\tAdding {_directoryToAdd + file}...")
            _currentZipBuffer.write(_directoryToAdd + file)
        elif os.path.isfile(_directoryToAdd + file):
            print(f"\tIgnoring {_directoryToAdd + file}...")
        else:
            addFolderToZip(_currentZipBuffer, _directoryToAdd + file + "/")


def generateZipFile(_submissionDirectory: str) -> None:
    """
    This function generates the zip file needed for gradescope.
    :param _submissionDirectory: the directory that the students work is in
    """
    GREEN_COLOR: str = u"\u001b[32m"
    RESET_COLOR: str = u"\u001b[0m"

    print("Generating gradescope upload...")

    zipName: str = buildZipName()

    with ZipFile(zipName, 'w') as submissionZip:
        os.chdir(_submissionDirectory)
        for file in os.listdir("."):
            if os.path.isfile(file) and file[-3:] == ".py":
                print(f"\tAdding {_submissionDirectory + file} to zip...")
                submissionZip.write(file)
            elif os.path.isfile(file):
                print(f"\tIgnoring {_submissionDirectory + file}...")
            else:
                addFolderToZip(submissionZip, file + "/")

    print("...Done.")
    print(f"\n\n{GREEN_COLOR}Submit {zipName} to Gradescope under the corresponding assignment.{RESET_COLOR}")



def tool():  # pragma: no cover
    submissionDirectory = "student_work"

    if len(sys.argv) == 2:
        submissionDirectory = sys.argv[1]

    # need to make sure to that we have a / at the end of the path
    if submissionDirectory[-1:] != '/':
        submissionDirectory += "/"

    generateZipFile(submissionDirectory)


if __name__ == "__main__":
    tool()
