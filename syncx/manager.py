import copy
import threading
from dataclasses import dataclass
from typing import Any
from typing import Optional

import dictdiffer
from syncx.backend import Backend
from syncx.backend import FileBackend
from syncx.exceptions import HistoryError
from syncx.exceptions import Rollback
from syncx.history import History
from syncx.serializer import Serializer
from syncx.serializer import YamlSerializer
from syncx.wrappers import CustomObjectWrapper
from syncx.wrappers import is_wrapped


@dataclass
class ChangeDetails:
    root: Any
    location: Any
    path_to_location: list
    delta: Optional[list]
    function_name: str
    args: list
    kwargs: dict


class Manager:

    default_serializer = YamlSerializer
    default_backend = FileBackend
    default_name = 'syncx_data'

    def __init__(self, did_change_callback=None, will_change_callback=None):
        self.lock = threading.RLock()
        self.instantiate_root_with_keywords = False

        self.will_change_callback = will_change_callback
        self.did_change_callback = did_change_callback

        self.serializer = None
        self.backend = None
        self.root = None
        self.root_type = None

        self.all_changes = []  # All changes within context, raw appended list
        self.history = None  # Optional history that can be manipulated with undo and redo
        self.transactions = []

        self.change_tracking_active = True

    def execute_change(self, path, original_function, args, kwargs):

        if not self.change_tracking_active:
            return original_function(*args, **kwargs)

        need_all_changes = bool(len(self.transactions))
        need_history = self.history and self.history.on
        need_delta = any((need_all_changes, need_history))

        diff_location = dictdiffer.dot_lookup(self.root, path)
        before_change = need_delta and copy.deepcopy(diff_location)

        return_value = original_function(*args, **kwargs)

        after_change = need_delta and copy.deepcopy(diff_location)

        delta = need_delta and list(dictdiffer.diff(before_change, after_change, node=path))

        if need_all_changes:
            self.all_changes.append(delta)

        if need_history:
            self.add_history_entry(delta)

        change_details = ChangeDetails(
            root=self.root,
            location=diff_location,
            path_to_location=path,
            delta=delta,
            function_name=original_function.__name__,
            args=args,
            kwargs=kwargs,
        )

        if self.did_change_callback:
            self.did_change_callback(change_details)

        if self.backend and not self.transactions:
            self.sync(change_details)

        return return_value

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
            if self.instantiate_root_with_keywords:
                existing_content = self.root_type(**existing_content)
            else:
                existing_content = self.root_type(existing_content)
            from syncx import tag
            wrapped = tag(existing_content)
            self.set_as_manager_for(wrapped)
        else:
            self.backend.put(wrapped, self.serializer)

        return wrapped

    def sync(self, change_details: ChangeDetails):
        self.backend.put(self.root, self.serializer, change_location=change_details.location)

    def set_history(self):
        if self.history is None:
            from syncx import tag
            self.history = tag(History())
        return self.history

    def add_history_entry(self, delta):
        if not self.history:
            raise HistoryError('History not active when trying to add an entry')
        history = self.history
        if not history.on:
            return
        if history.current_index < len(history.entries):
            del history.entries[history.current_index:]
        history.entries.append(delta)
        if history._capacity and len(history.entries) > history._capacity:
            del history.entries[:-history._capacity]
        history.current_index = len(history.entries)
        return history.current_index

    def undo(self):
        history = self.check_history()
        if history.current_index == 0:
            return history.current_index
        history.current_index -= 1
        delta = history.entries[history.current_index]
        history.on = False
        dictdiffer.revert(delta, self.root, in_place=True)
        history.on = True
        return history.current_index

    def redo(self):
        history = self.check_history()
        if history.current_index == len(history.entries):
            return history.current_index
        delta = history.entries[history.current_index]
        history.current_index += 1
        history.on = False
        dictdiffer.patch(delta, self.root, in_place=True)
        history.on = True
        return history.current_index

    def check_history(self):
        history = self.history
        if not history or not history.on:
            raise HistoryError('History not active when trying to undo or redo')
        return history

    def start_transaction(self):
        self.lock.acquire()
        self.transactions.append(len(self.all_changes))

        if self.history is not None:
            self.history._manager.start_transaction()

    def end_transaction(self, do_rollback):
        if self.history is not None:
            self.history._manager.end_transaction(do_rollback)

        if do_rollback:
            starting_change_index = self.transactions.pop()
            self.change_tracking_active = False
            for delta in reversed(self.all_changes[starting_change_index:]):
                dictdiffer.revert(delta, self.root, in_place=True)
            self.all_changes = self.all_changes[:starting_change_index]
            self.change_tracking_active = True

        self.lock.release()


class ManagerInterface:

    def __init__(self, manager):
        self._manager = manager

    @property
    def history(self) -> bool:
        history = self._manager.set_history()
        return history.on

    @history.setter
    def history(self, value: bool):
        history = self._manager.set_history()
        history.on = value

    def undo(self):
        return self._manager.undo()

    def redo(self):
        return self._manager.redo()
