from typing import Iterable


class MissingNotebookFile(Exception):
    def __init__(self) -> None:
        super().__init__(f"No .ipynb files were submitted! Expected exactly 1!")

class TooManyNotebooksError(Exception):
    def __init__(self, files: Iterable[str]) -> None:
        super().__init__(
            f"Expected one `.ipynb` file. Received: {', '.join(file for file in files)}\n"
            "Please delete extra `.ipynb` files"
        )
