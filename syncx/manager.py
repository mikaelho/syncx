from types import SimpleNamespace
from typing import Any

from syncx.backend import Backend
from syncx.backend import FileBackend
from syncx.serializer import Serializer
from syncx.serializer import YamlSerializer


class ChangeDetails(SimpleNamespace):
    root: Any
    location: Any
    path_to_location: list
    function_name: str
    args: list
    kwargs: dict


class Manager:

    default_serializer = YamlSerializer
    default_backend = FileBackend
    default_name = 'syncx_data'

    def __init__(self, did_change_callback=None, will_change_callback=None):
        self.will_change_callback = will_change_callback
        self.did_change_callback = did_change_callback
        self.serializer = None
        self.backend = None
        self.root = None
        self.root_type = None

    def did_change(self, obj, path, function_name, args, kwargs):
        change_details = ChangeDetails(
            root=self.root,
            location=obj,
            path_to_location=path,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
        )
        if self.did_change_callback:
            self.did_change_callback(change_details)

        if self.backend:
            self.sync(change_details)

    def set_as_manager_for(self, root):
        self.root = root
        object.__setattr__(root, '_manager', self)

    def start_sync(
        self,
        wrapped: Any,
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
            if self.root_type:
                existing_content = self.root_type(**existing_content)
            from syncx import tag
            wrapped = tag(existing_content)
            self.set_as_manager_for(wrapped)
        else:
            self.backend.put(wrapped, self.serializer)

        return wrapped

    def sync(self, change_details: ChangeDetails):
        self.backend.put(self.root, self.serializer, change_location=change_details.location)
