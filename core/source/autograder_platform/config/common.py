
class InvalidConfigException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class MissingParsingLibrary(Exception):
    def __init__(self, library, parserName) -> None:
        super().__init__(f"Missing {library}. Required for {parserName}")
