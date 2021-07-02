import copy
import importlib
from io import IOBase
from io import StringIO
from typing import Any
from typing import Protocol

try:
    import yaml
except ImportError:
    pass

try:
    import ujson as json
except ImportError:
    import json


class Serializer(Protocol):

    file_extension: str

    def dump(self, content: Any, stream: IOBase):
        ...

    def load(self, stream: IOBase) -> Any:
        ...


class YamlSerializer:

    file_extension = 'yaml'

    def __init__(self):
        assert yaml.dump, 'pyyaml is not installed'

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


class JsonSerializer:

    file_extension = 'json'
    json = None

    def dump(self, content: Any, stream: StringIO):
        #content_copy = copy.deepcopy(content)
        json.dump(
            content,
            stream,
            separators=(',', ':'),
            allow_nan=True,
            ensure_ascii=False,
        )

    def load(self, stream: StringIO) -> Any:
        return json.load(stream)
