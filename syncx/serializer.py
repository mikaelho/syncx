import copy
import importlib
from io import IOBase
from typing import Any
from typing import Protocol

import yaml


class Serializer(Protocol):

    file_extension: str

    def dump(self, content: Any, stream: IOBase):
        ...

    def load(self, stream: IOBase) -> Any:
        ...


class YamlSerializer:

    file_extension = 'yaml'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        globals()['yaml'] = importlib.import_module('yaml')

    def dump(self, content: Any, stream: IOBase):
        content_copy = copy.deepcopy(content)
        yaml.safe_dump(
            content_copy,
            stream,
            default_flow_style=False,
            allow_unicode=True,
        )

    def load(self, stream: IOBase) -> Any:
        return yaml.safe_load(stream)
