import io
import tempfile
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

    def put(self, root: Any, serializer: Serializer, delta: Any = None):
        """
        Writes contents first to a temporary file to avoid empty/corrupted contents in case of an error.
        """
        stream = io.StringIO()
        serializer.dump(root, stream)

        _, temporary_file_path = tempfile.mkstemp(text=True)
        temporary_file = Path(temporary_file_path)
        try:
            temporary_file.write_text(stream.getvalue())
        except:
            temporary_file.unlink()
            raise
        temporary_file.replace(self.filename)


    def get(self, serializer: Serializer, key: str = None) -> Any:
        """
        Returns the file contents as de-serialized data, or None if file does not exist or is empty.
        """
        file = Path(self.filename)
        try:
            stream = io.StringIO(file.read_text())
            return serializer.load(stream)
        except (FileNotFoundError, EOFError):
            return None
