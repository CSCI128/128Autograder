from typing import Dict, List, Optional, Any

from nbformat import read, NotebookNode, write
from rich.console import Console
from rich.syntax import Syntax

from autograder_platform.cli import AutograderCLITool
from autograder_platform.config.Config import AutograderConfigurationBuilder, AutograderConfiguration
from language_binds.IPython.metadata import CellMetadata


class IPythonSubmissionManager(AutograderCLITool):
    def __init__(self):
        super().__init__(f"IPython Submission Manager v{AutograderCLITool.get_version()}")


    def configure_options(self):
        self.parser.add_argument("--edit", default=False, action="store_true",
                                 help="Run the tool in edit mode")
        self.parser.add_argument("--new-from-template", default=False, action="store_true",
                                 help="Run the tool in 'new-from-template' mode which allows injecting headers and stripping out solution code")
        self.parser.add_argument("--header-file", default="./header.md",
                                 help="The header that should be included in the outputted ipython file")
        self.parser.add_argument("--in-file", default="./submission.ipynb",
                                 help="ipython file that should be used.")
        self.parser.add_argument("--output", default="./bin/submission.ipynb",
                                 help="Where the outputted file should be")


    def set_config_arguments(self, configBuilder: AutograderConfigurationBuilder[AutograderConfiguration]):
        pass


    def print_cell_src(self, src: List[str]):
        joined = "".join(src)

        syntax = Syntax(joined, "python", line_numbers=True)
        console = Console()

        console.print(syntax)

    @staticmethod
    def edit_cell_metadata(cell_metadata: Dict[str, Dict[str, Any]]):
        if "autograder" in cell_metadata:
            metadata = CellMetadata(**cell_metadata["autograder"])
        else:
            metadata = CellMetadata()

        print(f"Current Metadata: {metadata}")

        print(f"Enter field name to edit, 'done' when you are done, or 'ignore' if no metadata should be written for this cell.")
        user_in = ""

        while user_in != "done":
            user_in = input("> ").lower()

            if user_in == "done":
                break

            if user_in == "ignore":
                return

            if user_in not in metadata.__dict__:
                print(f"{user_in} not in {metadata.__dict__.keys()}")
                continue
            if user_in == "deps":
                print("Enter the cell dependencies in order and 'done' once you are finished")
                deps = []
                dep = ""
                while dep.lower() != "done":
                    dep = input("deps > ")
                    if dep.lower() == "done":
                        break
                    deps.append(dep)
                to_set = deps

            else:
                to_set = input(f"{user_in} > ")

            if user_in == "runnable":
                to_set = bool(to_set)

            metadata.__dict__[user_in] = to_set

        cell_metadata["autograder"] = metadata.__dict__

    def edit(self, inputFile: str) -> NotebookNode:
        self.print_info_message(f"Editing '{inputFile}'")
        with open(inputFile, 'r', encoding="UTF-8") as r:
            notebook = read(r, as_version=4)

        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            if "metadata" not in cell:
                cell["metadata"] = {}

            self.print_info_message("Editing metadata for cell: ")
            self.print_cell_src(cell["source"])
            self.edit_cell_metadata(cell["metadata"])

        return notebook


    def run(self) -> bool:
        self.configure_options()

        self.arguments = self.parser.parse_args()

        if self.arguments.version:
            self.print_info_message(f"Autograder Platform Version: {self.get_version()}")
            self.print_info_message(f"IPython Language Bind Version: TODO - a beta or something")
            return False

        notebook: Optional[NotebookNode] = None
        if self.arguments.edit:
            notebook = self.edit(self.arguments.in_file)
        elif self.arguments.new_from_template:
            self.print_error_message("NotImplemented", "Creating a new submission from a template has not yet been implemented.")

        if notebook is None:
            return False

        self.print_info_message(f"Writing '{self.arguments.output}'")
        with open(self.arguments.output, 'w') as w:
            write(notebook, w)

        return False


tool = IPythonSubmissionManager().run

if __name__ == "__main__":
    res = tool()

    exit(res)
