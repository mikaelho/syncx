from typing import Any

from syncx.backend import FileBackend
from syncx.serializer import YamlSerializer


class Manager:

    default_serializer = YamlSerializer
    default_backend = FileBackend
    default_name = 'syncx_data'

    def __init__(self, change_callback=None, will_change_callback=None, did_change_callback=None):
        self.change_callback = change_callback
        self.will_change_callback = will_change_callback
        self.did_change_callback = did_change_callback
        self.serializer = None
        self.backend = None

    def did_change(self, obj, path, function_name, args, kwargs):
        self.add_to_history(path)
        self.update_backend(obj, path)

        self.change_callback(obj)

        if self.did_change_callback:
            self.did_change_callback(obj, path(obj), function_name, args, kwargs)

    def update_backend(self, obj: Any, path: list):
        ...

    def add_to_history(self, path):
        ...


def sync(target: Any):
    wrapped = wrap