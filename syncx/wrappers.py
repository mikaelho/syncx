#coding: utf-8
"""
Proxy wrappers for different data types to detect any changes.
"""

import copy
import functools
from typing import Any
from typing import MutableMapping
from typing import MutableSequence
from typing import MutableSet

from peak.util.proxies import ObjectWrapper


class TrackerWrapper(ObjectWrapper):

    _tracker = None

    def __init__(self, obj, path, callback, osa=object.__setattr__):
        super().__init__(obj)

        osa(self, '_callback', functools.partial(callback, path))

    def __repr__(self):
        return self.__subject__.__repr__()

    def __deepcopy__(self, memo):
        """
        Deepcopy mechanism is used to unwrap the wrapped data structure.
        """
        return copy.deepcopy(self.__subject__, memo)

    # def __enter__(self):
    #     handler = self._tracker.handler
    #     if handler.lock:
    #         handler.lock.acquire()
    #
    # def __exit__(self, *exc):
    #     handler = self._tracker.handler
    #     if handler.lock:
    #         handler.lock.release()


def is_tracked(obj):
    return isinstance(obj, TrackerWrapper)


class DictWrapper(TrackerWrapper):
    """
    Wrapper for MutableMappings.
    """


class ListWrapper(TrackerWrapper):
    """
    Wrapper for MutableSequences.
    """


class SetWrapper(TrackerWrapper):
    """
    Wrapper for MutableSets.
    """


class CustomObjectWrapper(TrackerWrapper):
    """ If an object has a __dict__ attribute, we track attribute changes. """


trackable_types = {
  MutableSequence: ListWrapper,
  MutableMapping: DictWrapper,
  MutableSet: SetWrapper,
}

mutating_methods = {
  CustomObjectWrapper: ['__setattr__', '__delattr__'],
  DictWrapper:
    ['__setitem__', '__delitem__', 'pop', 'popitem', 'clear', 'update', 'setdefault'],
  ListWrapper:
    ['__setitem__', '__delitem__', 'insert', 'append', 'reverse', 'extend', 'pop', 'remove', 'clear', '__iadd__'],
  SetWrapper:
    ['add', 'discard', 'clear', 'pop', 'remove', '__ior__', '__iand__', '__ixor__', '__isub__']
}

# Add tracking wrappers to all mutating functions.

for wrapper_type in mutating_methods:
    for func_name in mutating_methods[wrapper_type]:
        def func(self, *args, tracker_function_name=func_name, **kwargs):
            if tracker_function_name == '__setattr__' and args[0] == '__subject__':
                return ObjectWrapper.__setattr__(self, *args, **kwargs)
            return_value = getattr(self.__subject__, tracker_function_name)(*args, **kwargs)
            if tracker_function_name not in ('__setattr__', '__delattr__') or not args[0].startswith('_'):
                wrap_members(self)
                self._callback(function_name=tracker_function_name, args=args, kwargs=kwargs)
            return return_value
        setattr(wrapper_type, func_name, func)
        getattr(wrapper_type, func_name).__name__ = func_name


def wrap(target: Any, callback: callable, path: list = None) -> TrackerWrapper:
    """
    Wrap target in a proxy that will call the callback whenever tracked object is changed.
    """
    tracked = None
    path = path or []

    for abc, wrapper in trackable_types.items():
        if isinstance(target, abc):
            tracked = wrapper(target, path, callback)
    else:
        if hasattr(target, "__dict__"):
            tracked = CustomObjectWrapper(target, path, callback)

    if tracked is None:
        raise TypeError(f"'{target}' does not have a trackable type: {type(target)}")

    wrap_members(tracked)

    return tracked



def unwrap(tracked):
    """
    Returns the original data structure, with tracking wrappers removed.
    """
    return copy.deepcopy(tracked)


def wrap_members(tracked: TrackerWrapper):
    """
    Checks to see if some of the changed node's contents now need to be tracked.
    """
    to_wrap = []
    callback = tracked._callback
    for key, value in get_iterable(tracked.__subject__):
        if is_tracked(value):
            existing_callback = value._callback
            if existing_callback.func != callback.func or existing_callback.args[0] != callback.args[0] + [key]:
                to_wrap.append((key, value.__subject__))
        elif should_wrap(value):
            to_wrap.append((key, value))
    for key, value in to_wrap:
        set_value(
            tracked.__subject__,
            key,
            value,
            wrap(value, callback.func, callback.args[0] + [key]),
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
    elif hasattr(obj, "__dict__"):
        return ((key, value) for key, value in obj.__dict__.items() if not key.startswith('_'))
    else:
        raise TypeError(f'Cannot return an iterator for type {type(obj)}')


def should_wrap(contained):
    if isinstance(contained, TrackerWrapper):
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
