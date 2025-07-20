import os.path
from typing import TypeVar, List

import nbformat
import nbformat as nb
from nbformat import NotebookNode

from language_binds.IPython.metadata import CellMetadata

Builder = TypeVar("Builder", bound="NotebookBuilder")

class NotebookBuilder:
    def __init__(self, filename, baseDirectory: str = "."):
        self._filename = os.path.join(baseDirectory, filename)
        self._notebook: NotebookNode = nb.v4.new_notebook()
        self._cells: List[NotebookNode] = []

    def addCodeCell(self: Builder, id: str, src: str, runnable=True, deps: List = None) -> Builder:
        if deps is None:
            deps = []

        cell = nb.v4.new_code_cell(src)
        cell["metadata"] = {}
        cell["metadata"]["autograder"] = CellMetadata(runnable=runnable, id=id, deps=deps).__dict__

        self._cells.append(cell)

        return self

    def addMarkdownCell(self: Builder, src: str) -> Builder:
        self._cells.append(nb.v4.new_markdown_cell(src))

        return self

    def toFile(self) -> str:
        self._notebook['cells'] = self._cells
        nb.validate(self._notebook)

        with open(self._filename, "w") as w:
            nb.write(self._notebook, w)

        return self._filename

    def toNotebook(self) -> NotebookNode:
        self._notebook['cells'] = self._cells
        nb.validate(self._notebook)

        return self._notebook
