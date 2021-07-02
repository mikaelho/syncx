import io
from io import IOBase
from io import StringIO
from pathlib import Path
from typing import Any
from typing import Protocol

from syncx.serializer import Serializer


def streamify(value: Any) -> io.IOBase:
    if isinstance(value, io.IOBase):
        return value
    elif type(value) is str:
        return io.StringIO(value)
    elif type(value) is bytes:
        return io.BytesIO(value)
    else:
        raise TypeError(f'Cannot turn value of type {type(value)} into a stream', value)


class Backend(Protocol):

    def __init__(self, name: str, *args, **kwargs):
        """
        Initialize the backend with a name.
        """

    def put(self, root: Any, serializer: Serializer, change_location: Any = None, key: str = None):
        """
        Write/send value to the backend provider, with an optional key.
        """

    def get(self, serializer: Serializer, key: str = None) -> Any:
        """
        Read/get value from the backend provider, with an optional key.
        """


class FileBackend:

    def __init__(self, name: str):
        self.filename = name

    def _get_file(self, serializer: Serializer) -> Path:
        return Path(f'{self.filename}.{serializer.file_extension}')

    def put(self, root: Any, serializer: Serializer, change_location: Any = None, key: str = None):
        file = self._get_file(serializer)
        stream = io.StringIO()
        serializer.dump(root, stream)
        file.write_text(stream.getvalue())

    def get(self, serializer: Serializer, key: str = None) -> Any:
        """
        Returns the file contents as de-serialized data, or None if file does not exist or is empty.
        """
        file = self._get_file(serializer)
        try:
            stream = io.StringIO(file.read_text())
            return serializer.load(stream)
        except (EOFError, FileNotFoundError):
            return None
