import copy
import dataclasses
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

try:
    import pydantic
    use_pydantic = True
except ImportError:
    use_pydantic = False


def make_serializable(data):
    if use_pydantic and isinstance(data, pydantic.BaseModel):
        return json.loads(data.json())

    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        return dataclasses.asdict(data)

    if hasattr(data, '__dict__'):
        return data.__dict__

    return None


class Serializer(Protocol):

    file_extension: str

    def dump(self, content: Any, stream: StringIO):
        ...

    def load(self, stream: StringIO) -> Any:
        ...


class YamlSerializer:

    file_extension = 'yaml'

    class SyncDumper(yaml.SafeDumper):
      def represent_data(self, data):
        serializable_data = make_serializable(data)
        if serializable_data:
            data = serializable_data
        return super().represent_data(data)

    def __init__(self):
        assert yaml.dump, 'pyyaml is not installed'

    def dump(self, content: Any, stream: StringIO):
        content_copy = copy.deepcopy(content)
        # if use_pydantic and isinstance(content_copy, pydantic.BaseModel):
        #     content_copy = json.loads(content_copy.json())
        yaml.dump(
            content_copy,
            stream,
            Dumper=YamlSerializer.SyncDumper,
            default_flow_style=False,
            allow_unicode=True,
        )

    def load(self, stream: StringIO) -> Any:
        return yaml.safe_load(stream)


class JsonSerializer:

    file_extension = 'json'

    class SyncDumper(json.JSONEncoder):
        def default(self, obj):
            serializable_obj = make_serializable(obj)
            if serializable_obj:
                return serializable_obj
            return json.JSONEncoder.default(self, obj)

    def dump(self, content: Any, stream: StringIO):
        content_copy = copy.deepcopy(content)
        # if use_pydantic and isinstance(content_copy, pydantic.BaseModel):
        #     stream.write(content_copy.json())
        # else:
        json.dump(
            content_copy,
            stream,
            cls=JsonSerializer.SyncDumper,
            separators=(',', ':'),
            allow_nan=True,
            ensure_ascii=False,
        )

    def load(self, stream: StringIO) -> Any:
        return json.load(stream)
