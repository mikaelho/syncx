import copy
from contextlib import contextmanager
from typing import Any
from typing import TypeVar

from syncx.backend import Backend
from syncx.exceptions import Rollback
from syncx.manager import Manager
from syncx.manager import ManagerInterface
from syncx.serializer import Serializer
from syncx.wrappers import NotifyWrapper
from syncx.wrappers import is_wrapped
from syncx.wrappers import wrap_target

T = TypeVar('T')


def tag(target: T, change_callback: callable = None, manager: Manager = None) -> T:
    """
    Tag target data structure to get notified of any changes.

    Return value is a proxy type, but type hinted to match the tagged object for editor convenience.
    """
    return wrap_target(target, [], manager or Manager(change_callback))


def untag(tagged: Any):
    """
    Returns an untagged copy of the data structure.
    """
    return copy.deepcopy(tagged)


def manage(tagged: Any):
    if not is_wrapped(tagged):
        raise ValueError(f'Call tag() or sync() on {tagged} before using manage()')
    return ManagerInterface(tagged._manager)


def sync(target: T, name: str = None, serializer: Serializer = None, backend: Backend = None) -> T:
    if not is_wrapped(target):
        target = tag(target)
    target = target._manager.start_sync(target, name, serializer, backend)

    return target


def rollback():
    raise Rollback()