import copy
from typing import Any
from typing import Type
from typing import TypeVar
from typing import Union

from syncx.backend import Backend
from syncx.exceptions import Rollback
from syncx.manager import Manager
from syncx.manager import ManagerInterface
from syncx.serializer import Serializer
from syncx.wrappers import is_wrapped
from syncx.wrappers import wrap_target

T = TypeVar('T')


def tag(
    target: T,
    change_callback: callable = None,
    history: bool = False,
    manager: Manager = None
) -> T:
    """
    Tag target data structure to get notified of any changes.

    Return value is a proxy type, but type hinted to match the tagged object for editor convenience.
    """
    tagged = wrap_target(target, [], manager or Manager(change_callback))
    if history:
        tagged._manager.set_history()
    return tagged


def untag(tagged: Any):
    """
    Returns an untagged copy of the data structure.
    """
    return copy.deepcopy(tagged)


def undo(tagged: Any):
    if not is_wrapped(tagged):
        raise ValueError(f'Call tag() or sync() with history=True before using undo()')
    tagged._manager.undo()


def redo(tagged: Any):
    if not is_wrapped(tagged):
        raise ValueError(f'Call tag() or sync() with history=True before using redo()')
    tagged._manager.redo()


def manage(tagged: Any):
    if not is_wrapped(tagged):
        raise ValueError(f'Call tag() or sync() on {tagged} before using manage()')
    return ManagerInterface(tagged._manager)


def sync(
    target: T,
    name: str,
    serializer: Union[Serializer, Type[Serializer]] = None,
    backend: Backend = None,
    history: bool = False,
) -> T:
    if not is_wrapped(target):
        target = tag(target)
    tagged = target._manager.start_sync(target, name, serializer, backend)
    if history:
        tagged._manager.set_history()
    return tagged


def rollback():
    raise Rollback()