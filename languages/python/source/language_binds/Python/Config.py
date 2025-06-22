from dataclasses import dataclass
from typing import Dict, List, Any, Optional as OptionalType
from schema import Schema, Optional, And

from autograder_platform.config.BaseSchema import BaseSchema

@dataclass(frozen=True)
class PythonConfiguration:
    """
    Python Configuration
    ====================

    This class defines extra parameters for when the autograder is running in Python
    """
    extra_packages: List[Dict[str, str]]
    """
    The extra packages that should be added to the autograder on build.
    Must be stored in 'package_name': 'version'. Similar to requirements.txt 
    """
    buffer_size: int
    """
    The size of the output buffer when the autograder runs
    """

class PythonConfigSchema(BaseSchema[OptionalType[PythonConfiguration]]):
    def __init__(self):
        self.schema: Schema = Schema({
            "python": {
                Optional("extra_packages", default=lambda: []): [{
                    "name": str,
                    "version": str,
                }],
                Optional("buffer_size", default=2 ** 20): And(int, lambda x: x >= 2 ** 20)
            }
        }, ignore_extra_keys=True, name="PythonConfigSchema")

    def register_sub_schema(self, language_name, sub_schema: BaseSchema[Any]):
        raise NotImplementedError("Unable to register a sub schema for a language!")

    def validate(self, data: Dict) -> Dict:
        # for now, we are saying that if the language config is not defined, that we are fine with it
        if 'python' not in data:
            return data

        data['python'] = self.schema.validate(data)['python']

        return data

    def build(self, data: Dict) -> OptionalType[PythonConfiguration]:
        """
        This expects the entire schema again but returns just the subsection that we know how to parse.
        None otherwise.
        """
        if 'python' not in data or not data['python']:
            return None

        return PythonConfiguration(**data['python'])
