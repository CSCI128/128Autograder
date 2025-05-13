import ast
import dataclasses
from typing import List, Tuple, Optional


@dataclasses.dataclass
class CellMetadata:
    runnable: bool = False
    id: str = ""
    deps: List[Tuple[int, str]] = dataclasses.field(default=list)


def parseCellId(keywords: List[ast.keyword]) -> str:
    value: Optional[str] = None
    for node in keywords:
        if node.arg != "id":
            continue
        if not isinstance(node.value, ast.Constant):
            raise SyntaxError(f"Invalid value for id! Should be a constant! Was {node.value}")

        if not isinstance(node.value.value, str):
            raise TypeError(f"Invalid type for id! Expected a string! was {node.value.value}")

        value = node.value.value

    if value is None:
        raise SyntaxError(f"Missing required field 'id' in {keywords}")

    return value


def parseCellDeps(keywords: List[ast.keyword]) -> List[Tuple[int, str]]:
    deps: List[Tuple[int, str]] = []
    for node in keywords:
        if node.arg != "deps":
            continue

        if not isinstance(node.value, ast.List):
            raise SyntaxError(f"Invalid value for deps! Should be a list! Was {node.value}")

        listToProcess: ast.List = node.value

        for dep in listToProcess.elts:
            if not isinstance(dep, ast.Tuple):
                raise SyntaxError(f"Invalid value for deps! Expected a tuple with ordering and id! Was {dep}")

            if len(dep.elts) != 2:
                raise SyntaxError(
                    f"Invalid value for deps! Expected a tuple with EXACTLY ordering and id! Was {dep.elts}")

            ordering = dep.elts[0]
            id = dep.elts[1]

            if not isinstance(ordering, ast.Constant):
                raise SyntaxError(f"Invalid value for ordering! Expected a constant! Was {ordering}")

            if not isinstance(id, ast.Constant):
                raise SyntaxError(f"Invalid value for id! Expected a constant! Was {id}")

            if not isinstance(ordering.value, int):
                raise TypeError(f"Invalid type for ordering! Expected an int! Was {ordering.value}")

            if not isinstance(id.value, str):
                raise TypeError(f"Invalid type for ordering! Expected a str! Was {id.value}")

            deps.append((ordering.value, id.value))

        break

    return deps


def parseCellMetadata(syntaxTree: ast.Module) -> Optional[CellMetadata]:
    metadata: Optional[CellMetadata] = None

    for node in ast.walk(syntaxTree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Name):
            continue

        funcDef: ast.Name = node.func

        if funcDef.id != "TestableCell" and funcDef.id != "Cell":
            continue

        # then we know its something that we care about

        metadata = CellMetadata()
        metadata.runnable = funcDef.id == "TestableCell"
        metadata.id = parseCellId(node.keywords)
        metadata.deps = parseCellDeps(node.keywords)

        # We are only allowing one cell metadata definition per cell
        break

    return metadata
