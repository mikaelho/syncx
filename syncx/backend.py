from pathlib import Path
from typing import Any

from syncx.serializer import Serializer


class Backend:

    def put(self, value: Any, serializer: Serializer, key: str = None):
        """
        Write/send value to the backend provider, with an optional key.
        """

    def get(self, serializer: Serializer, key: str = None) -> Any:
        """
        Read/get value from the backend provider, with an optional key.
        """


class FileBackend(Backend):

    def __init__(self, filename):
        self.filename = filename

    def _get_filename(self, serializer):
        return f'{self.filename}.{serializer.file_extension}'

    def put(self, value: Any, serializer: Serializer, key: str = None):
        filename = self._get_filename(serializer)
        Path(filename).write_text(serializer.dumps(value))

    def get(self, serializer: Serializer, key: str = None) -> Any:
        """
        Returns the file contents as de-serialized data, or None if file does not exist or is empty.
        """
        filename = self._get_filename(serializer)
        try:
            contents = Path(filename).read_text()
            return serializer.loads(contents)
        except (EOFError, FileNotFoundError):
            return None
