from typing import Iterable


class MissingNotebookFile(Exception):
    def __init__(self) -> None:
        super().__init__(f"No `.ipynb` files were submitted! Expected exactly 1!")

class TooManyNotebooksError(Exception):
    def __init__(self, files: Iterable[str]) -> None:
        super().__init__(
            f"Expected one `.ipynb` file. Received: {', '.join(file for file in files)}\n"
            "Please delete extra `.ipynb` files"
        )

class MissingDependencyError(Exception):
    def __init__(self, cellId: str, dep: str, availableCells: Iterable[str]):
        super().__init__(
            f"Missing dependency '{dep}' for cell '{cellId}'!\n"
            f"Expected '{dep}' in {', '.join(cell for cell in availableCells)}, but was not present!"
        )

class NoTestableCellsError(Exception):
    def __init__(self):
        super().__init__(
            "Expected at least one cell to be testable!\n"
            "Currently, no cells are testable, please ensure at least one cell in notebook has 'TestableCell' metadata defined!"
        )