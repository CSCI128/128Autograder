import re

from autograder_platform.StudentSubmission.ITransformer import ITransformer

class MagicCommandTransformer(ITransformer):
    MAGIC_COMMAND_PREFIXES: re.Pattern = re.compile(r"^[!%].*$")

    def transform(self, string: str) -> str:
        transformed = []

        for line in string.splitlines():
            if self.MAGIC_COMMAND_PREFIXES.match(line.strip()):
                continue

            transformed.append(line)

        return "\n".join(transformed)


class MatplotLibFigTransformer(ITransformer):
    FIG_SHOW_PATTERN: re.Pattern = re.compile(r"^(matplotlib\.pyplot\.show\(\)|plt\.show\(\))$")

    def transform(self, string: str) -> str:
        curFigNumber = 1
        transformed = []
        for line in string.splitlines():
            if self.FIG_SHOW_PATTERN.match(line.strip()):
                line = line.replace("show()", f"savefig('fig_{curFigNumber}.png')")
                curFigNumber += 1

            transformed.append(line)

        return "\n".join(transformed)
