"""
Proxy wrappers for different data types to detect any changes.
"""

import copy
from typing import MutableMapping
from typing import MutableSequence
from typing import MutableSet
from typing import TypeVar

from peak.util.proxies import ObjectWrapper

from syncx.exceptions import Rollback

T = TypeVar('T')


class NotifyWrapper(ObjectWrapper):

    def __init__(self, obj, path, manager, osa=object.__setattr__):
        super().__init__(obj)

        osa(self, '_path',  path)  # noqa
        osa(self, '_manager', manager)  # noqa

    def __repr__(self):
        return self.__subject__.__repr__()

    def __deepcopy__(self, memo):
        """
        Deepcopy mechanism is used to unwrap the wrapped data structure.
        """
        return copy.deepcopy(self.__subject__, memo)  # noqa

    def __enter__(self):
        self._manager.start_transaction()

    def __exit__(self, exc_type, exc_value, traceback):
        self._manager.end_transaction(do_rollback=bool(exc_type))

        if exc_type is Rollback:
            return True


def is_wrapped(obj):
    return isinstance(obj, NotifyWrapper)


class DictWrapper(NotifyWrapper):
    """
    Wrapper for MutableMappings.
    """


class ListWrapper(NotifyWrapper):
    """
    Wrapper for MutableSequences.
    """


class SetWrapper(NotifyWrapper):
    """
    Wrapper for MutableSets.
    """


class CustomObjectWrapper(NotifyWrapper):
    """ If an object has a __dict__ attribute, we track attribute changes. """


trackable_types = {
  MutableSequence: ListWrapper,
  MutableMapping: DictWrapper,
  MutableSet: SetWrapper,
}

mutating_methods = {
  CustomObjectWrapper: [
      '__setattr__', '__delattr__', #'__iadd__', '__isub__', '__imul__', '__imatmul__', '__itruediv__',
      #'__ifloordiv__', '__imod__', '__ipow__', '__ilshift__', '__irshift__', '__iand__', '__ixor__', '__ior__',
  ],
  DictWrapper: [
      '__setitem__', '__delitem__', 'pop', 'popitem', 'clear', 'update', 'setdefault',
  ],
  ListWrapper: [
      '__setitem__', '__delitem__', 'insert', 'append', 'reverse', 'extend', 'pop', 'remove', 'clear', '__iadd__',
  ],
  SetWrapper: [
      'add', 'discard', 'clear', 'pop', 'remove', '__ior__', '__iand__', '__ixor__', '__isub__',
  ],
}

# Add tracking wrappers to all mutating functions.

for wrapper_type in mutating_methods:
    for func_name in mutating_methods[wrapper_type]:
        def func(self, *args, tracker_function_name=func_name, **kwargs):
            if tracker_function_name == '__setattr__' and args[0] == '__subject__':
                return ObjectWrapper.__setattr__(self, *args, **kwargs)

            original_function = getattr(self.__subject__, tracker_function_name)

            with self._manager.lock:
                result = self._manager.execute_change(
                    self._path,
                    original_function,
                    args,
                    kwargs,
                )
                wrap_members(self)
            return result

        setattr(wrapper_type, func_name, func)
        getattr(wrapper_type, func_name).__name__ = func_name


def wrap_target(target: T, path: list, manager: 'Manager') -> T:
    tracked = None
    is_object = False

    for abc, wrapper in trackable_types.items():
        if isinstance(target, abc):
            tracked = wrapper(target, path, manager)
            break
    else:
        if type(target) is type:
            target = target()
        if hasattr(target, '__dict__'):
            tracked = CustomObjectWrapper(target, path + ['__dict__'], manager)
            is_object = True

    if tracked is None:
        raise TypeError(f"'{target}' does not have a trackable type: {type(target)}")

    if not path:  # i.e. root
        manager.root = tracked
        manager.root_type = type(target)
        manager.instantiate_root_with_keywords = is_object

    wrap_members(tracked)

    return tracked


def wrap_members(tracked: NotifyWrapper):
    """
    Checks to see if some of the changed node's contents now need to be tracked.
    """
    to_wrap = []
    path = tracked._path

    # if type(tracked) is CustomObjectWrapper:
    #    path.append('__dict__')

    for key, value in get_iterable(tracked.__subject__):
        if is_wrapped(value):
            updated_path = path + [key]
            if value._path != updated_path:
                to_wrap.append((key, value.__subject__))
        elif should_wrap(value):
            to_wrap.append((key, value))
    for key, value in to_wrap:
        set_value(
            tracked.__subject__,
            key,
            value,
            wrap_target(value, path + [key], tracked._manager),
        )


def get_iterable(obj):
    """
    Attempts to return a (key, value) iterator regardless of object type.

    For class instances, only returns attributes that do not start with '_' (public attributes).
    """
    if isinstance(obj, MutableSequence):
        return enumerate(obj)
    elif isinstance(obj, MutableMapping):
        return obj.items()
    elif isinstance(obj, MutableSet):
        return ((value, value) for value in obj)
    elif hasattr(obj, '__dict__'):
        return ((key, value) for key, value in obj.__dict__.items() if not key.startswith('_'))
    else:
        raise TypeError(f'Cannot return an iterator for type {type(obj)}')


def should_wrap(contained):
    if isinstance(contained, NotifyWrapper):
        return False

    if isinstance(contained, tuple(trackable_types.keys())):
        return True
    if hasattr(contained, "__dict__"):
        return True
    if hasattr(contained, "__hash__"):
        return False

    raise TypeError(f'Not a trackable or hashable type: {contained}')


def set_value(target, key, old_value, new_value):
    if isinstance(target, (MutableSequence, MutableMapping)):
        target[key] = new_value
    elif isinstance(target, MutableSet):
        target.remove(old_value)
        target.add(new_value)
    elif hasattr(target, "__dict__"):
        object.__setattr__(target, key, new_value)
    else:
        raise TypeError(f'Cannot set value for type {type(target)}')
