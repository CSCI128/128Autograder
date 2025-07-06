from typing import Dict, Generic, TypeVar
from abc import ABC, abstractmethod

T = TypeVar("T")

BaseSchemaType = TypeVar('BaseSchemaType', bound='BaseSchema[Any]')

class BaseSchema(Generic[T], ABC):
    _registered_sub_schemas: Dict[str, BaseSchemaType] = {}

    @classmethod
    def register_sub_schema(cls, language_name: str, sub_schema: BaseSchemaType):
        cls._registered_sub_schemas[language_name] = sub_schema

    @classmethod
    def deregister_sub_schema(cls, language_name: str):
        del cls._registered_sub_schemas[language_name]

    @abstractmethod
    def validate(self, data: Dict) -> Dict:
        raise NotImplementedError()

    @abstractmethod
    def build(self, data: Dict) -> T:
        raise NotImplementedError()

