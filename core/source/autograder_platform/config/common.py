from typing import Dict, Generic, List, TypeVar
from abc import ABC, abstractmethod, abstractproperty

T = TypeVar("T")

class BaseSchema(Generic[T], ABC):

    @abstractmethod
    def validate(self, data: Dict) -> Dict:
        raise NotImplementedError()

    @abstractmethod
    def build(self, data: Dict) -> T:
        raise NotImplementedError()

class InvalidConfigException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class MissingParsingLibrary(Exception):
    def __init__(self, library, parserName) -> None:
        super().__init__(f"Missing {library}. Required for {parserName}")
