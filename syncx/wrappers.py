#coding: utf-8

import copy
import functools
from types import SimpleNamespace
from typing import Any
from typing import MutableMapping
from typing import MutableSequence
from typing import MutableSet

import dictdiffer

from syncx.vendored.proxies import ObjectWrapper

def synchronized(func):
    """ Decorator for making wrapper functions, i.e.
    all access and updates, thread safe. """
    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        handler = self._tracker.handler
        if handler.lock:
            with self._tracker.handler.lock:
                return func(self, *args, **kwargs)
        else:
            return func(self, *args, **kwargs)
    return _wrapper


class TrackerWrapper(ObjectWrapper):

    _tracker = None

    def __init__(self, obj, path, callback, osa=object.__setattr__):
        ObjectWrapper.__init__(self, obj)

        osa(self, '_callback', functools.partial(callback, path))

    def __deepcopy__(self, memo):
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

    def __repr__(self):
        return self.__subject__.__repr__()


def is_tracked(obj):
    return isinstance(obj, TrackerWrapper)


class DictWrapper(TrackerWrapper):
    pass


class DictWrapper_Dot(DictWrapper):

    @synchronized
    def __getitem__(self, key):
        value = self.__subject__[key]
        # if isinstance(value, LazyLoadMarker):
        #     value = self._tracker.handler.load(key, self._tracker.path)
        #     self.__subject__[key] = value
        return value

    @synchronized
    def __getattr__(self, key):
        if key in self:
            return self[key]
        if hasattr(self, '__subject__'):
            return getattr(self.__subject__, key)
        raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, key))

    @synchronized
    def __setattr__(self, key, value):
        self[key] = value

    @synchronized
    def __delattr__(self, key):
        if key in self:
            del self[key]
            return
        if hasattr(self, '__subject__'):
            delattr(self.__subject__, key)
            return
        raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, key))


class ListWrapper(TrackerWrapper): pass


class SetWrapper(TrackerWrapper): pass


class CustomObjectWrapper(TrackerWrapper):
    """ If an object has a __dict__ attribute, we track attribute changes. """
    pass

trackable_types = {
  MutableSequence: ListWrapper,
  MutableMapping: DictWrapper,
  MutableSet: SetWrapper,
}

mutating_methods = {
  CustomObjectWrapper: [ '__setattr__'],
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
            return_value = getattr(self.__subject__, tracker_function_name)(*args, **kwargs)
            wrap_members(self)
            self._callback(function_name=tracker_function_name, args=args, kwargs=kwargs)
            return return_value
        setattr(wrapper_type, func_name, func)
        getattr(wrapper_type, func_name).__name__ = func_name


def wrap_target(target: Any, callback: callable, path: list = None) -> TrackerWrapper:
    """
    Wrap target in a proxy that will call the callback whenever tracked object is changed.
    """
    tracked = None
    path = path or []

    for abc, wrapper in trackable_types.items():
        if isinstance(target, abc):
            tracked = wrapper(target, path, callback)

    if tracked is None and hasattr(target, "__dict__"):
        tracked = CustomObjectWrapper(target, path, callback)

    if tracked is not None:
        wrap_members(tracked)
        return tracked

    raise TypeError(f"'{target}' does not have a trackable type: {type(target)}")


def wrap_members(tracked: TrackerWrapper):
    """
    Checks to see if some of the changed node's contents now need to be tracked.
    """
    to_wrap = []
    callback_func = tracked._callback.func
    for key, value in get_iterable(tracked.__subject__):
        if should_wrap(value):
            to_wrap.append((key, value))
        elif is_tracked(value):
            value_callback = value._callback
            value_callback.args = (value_callback.args[0] + [key],)
    for key, value in to_wrap:
        set_value(
            tracked.__subject__,
            key,
            value,
            wrap_target(value, callback_func, tracked._callback.args[0] + [key]),
        )


def get_iterable(obj):
    """ Attempts to return a (key, value) iterator regardless of object type. """
    if isinstance(obj, MutableSequence):
        return list(enumerate(obj))
    elif isinstance(obj, MutableMapping):
        return list(obj.items())
    elif isinstance(obj, MutableSet):
        return [(value, value) for value in obj]
    elif hasattr(obj, "__dict__"):
        return list(obj.__dict__.items())
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
        object.setattr(target, key, new_value)
    else:
        raise TypeError(f'Cannot set value for type {type(target)}')
