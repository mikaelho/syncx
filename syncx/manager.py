from typing import Any

from syncx.backend import Backend
from syncx.backend import FileBackend
from syncx.serializer import Serializer
from syncx.serializer import YamlSerializer
from syncx.wrappers import NotifyWrapper


class Manager:

    default_serializer = YamlSerializer
    default_backend = FileBackend
    default_name = 'syncx_data'

    def __init__(self, did_change_callback=None, will_change_callback=None):
        self.will_change_callback = will_change_callback
        self.did_change_callback = did_change_callback
        self.serializer = None
        self.backend = None

    def did_change(self, obj, path, function_name, args, kwargs):
        if self.did_change_callback:
            self.did_change_callback(obj)

        if self.backend:
            self.sync(obj)

    def set_as_manager_for(self, root):
        self.root = root
        object.__setattr__(root, '_manager', self)

    def start_sync(
        self,
        wrapped: NotifyWrapper,
        name: str = None,
        serializer: Serializer = None,
        backend: Backend = None
    ):
        self.name = name or self.default_name
        self.serializer = serializer or self.default_serializer
        self.backend = backend or self.default_backend
        if type(self.serializer) is type:
            self.serializer = self.serializer()
        if type(self.backend) is type:
            self.backend = self.backend(self.name)

        existing_content = self.backend.get(self.serializer)

        if existing_content:
            from syncx import wrap
            wrapped = wrap(existing_content)
            self.set_as_manager_for(wrapped)
        else:
            self.backend.put(wrapped, self.serializer)

        return wrapped

    def sync(self, obj: NotifyWrapper):
        self.backend.put(self.root, self.serializer, change_location=obj)
