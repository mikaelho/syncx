import copy
from typing import Any
from typing import TypeVar

from syncx.backend import Backend
from syncx.manager import Manager
from syncx.serializer import Serializer
from syncx.wrappers import is_wrapped
from syncx.wrappers import wrap_target

T = TypeVar('T')


def wrap(target: T, change_callback: callable = None, manager: Manager = None) -> T:
    """
    Wraps target in a proxy that will call the callback whenever tracked object is changed.

    Return value is a proxy type, but type hinted to match the wrapped object for editor convenience.
    """
    return wrap_target(target, [], manager or Manager(change_callback))


def unwrap(tracked):
    """
    Returns the original data structure, with tracking wrappers removed.
    """
    return copy.deepcopy(tracked)


def sync(target: T, name: str = None, serializer: Serializer = None, backend: Backend = None) -> T:
    if not is_wrapped(target):
        target = wrap(target)
    target = target._manager.start_sync(target, name, serializer, backend)

    return target
