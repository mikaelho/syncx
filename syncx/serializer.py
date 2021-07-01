import copy
import importlib
from io import IOBase
from io import StringIO
from typing import Any

import yaml


class Serializer:

    file_extension = ''

    def loads(self, serialialized_content: str) -> Any:
        with StringIO(serialialized_content) as stream:
            return self.load(stream)

    def dumps(self, content: Any) -> str:
        with StringIO() as stream:
            self.dump(content, stream)
            return stream.getvalue()

    def load(self, stream: IOBase) -> Any:
        raise NotImplementedError

    def dump(self, content: Any, to_stream: IOBase):
        raise NotImplementedError


class YamlSerializer(Serializer):

    file_extension = 'yaml'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        globals()['yaml'] = importlib.import_module('yaml')

    def load(self, stream: IOBase) -> Any:
        return yaml.safe_load(stream)

    def dump(self, content: Any, stream: IOBase):
        content_copy = copy.deepcopy(content)
        yaml.safe_dump(
            content_copy,
            stream,
            default_flow_style=False,
            allow_unicode=True,
        )
