import io
from pathlib import Path
from typing import Any
from typing import Protocol

from syncx.serializer import Serializer


class Backend(Protocol):

    def __init__(self, name: str, *args, **kwargs):
        """
        Initialize the backend with a name.
        """

    def put(self, root: Any, serializer: Serializer, delta: Any = None):
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
        return Path(self.filename)

    def put(self, root: Any, serializer: Serializer, delta: Any = None):
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
