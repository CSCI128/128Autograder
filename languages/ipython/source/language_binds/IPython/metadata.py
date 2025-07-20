import dataclasses
from typing import List

@dataclasses.dataclass
class CellMetadata:
    runnable: bool = False
    id: str = ""
    deps: List[str] = dataclasses.field(default=list)
