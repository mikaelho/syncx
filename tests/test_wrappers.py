from types import SimpleNamespace

import pytest

from syncx import rollback
from syncx import tag
from syncx import untag
from syncx.exceptions import Rollback
from syncx.manager import Manager
from syncx.wrappers import CustomObjectWrapper
from syncx.wrappers import DictWrapper
from syncx.wrappers import ListWrapper
from syncx.wrappers import SetWrapper


def check_callback(wrapped, callback):
    assert len(callback.calls) == 1
    details = callback.calls[0].args[0]
    assert details.location is wrapped
    assert details.path_to_location == []


def test_dict(mock_simple):
    wrapped = tag(dict(), mock_simple)
    assert type(wrapped) is DictWrapper
    wrapped['key'] = 'value'

    check_callback(wrapped, mock_simple)


def test_list(mock_simple):
    wrapped = tag(list(), mock_simple)
    assert type(wrapped) is ListWrapper
    wrapped.append('value')

    check_callback(wrapped, mock_simple)


def test_set(mock_simple):
    wrapped = tag(set(), mock_simple)
    assert type(wrapped) is SetWrapper
    wrapped.add('value')

    check_callback(wrapped, mock_simple)


def test_custom_object(mock_simple):
    wrapped = tag(SimpleNamespace(test='initial value'), mock_simple)
    assert type(wrapped) is CustomObjectWrapper
    wrapped.test = 'value'

    check_callback(wrapped, mock_simple)

    assert wrapped._manager.root_type is SimpleNamespace


def test_inherited_from_list(mock_simple):
    class CustomList(list):
        pass

    custom_list = CustomList()
    assert hasattr(custom_list, '__dict__')

    wrapped = tag(custom_list, mock_simple)
    assert type(wrapped) is ListWrapper
    wrapped.append('value')

    check_callback(wrapped, mock_simple)

    assert wrapped._manager.root_type is CustomList


def test_type(mock_simple):
    wrapped = tag(SimpleNamespace, mock_simple)
    wrapped.test = 'value'

    check_callback(wrapped, mock_simple)

    assert wrapped._manager.root_type is SimpleNamespace


def test_multiple_levels(catcher):
    wrapped = tag(SimpleNamespace(data={'key': ['value1']}), catcher.changed)
    wrapped.data['key'].append(set())
    wrapped.data['key'][1].add('value2')

    assert catcher.paths == [[], ['key'], ['key', 1]]
    assert catcher.function_names == ['__setitem__', 'append', 'add']


def test_same_object_different_paths(catcher):
    root = tag({'a': {}}, catcher.changed)
    root['b'] = root['a']
    root['a']['aa'] = 1
    root['b']['aa'] = 2
    root['a']['aa'] = 3

    assert catcher.paths == [[], ['a'], ['b'], ['a']]  # Different paths preserved
    assert root['a'] == root['b']  # But same object
    assert root['b']['aa'] == 3  # Same values


def test_revert_to_regular(catcher):
    wrapped = tag({'a': [{'b'}]}, catcher.changed)
    original = untag(wrapped)
    assert type(original) is dict
    assert type(original['a']) is list
    assert type(original['a'][0]) is set


@pytest.mark.parametrize('should_rollback', (False, True))
def test_context_manager(mock_func, should_rollback):
    mock_start = mock_func(Manager, 'start_transaction')
    mock_end = mock_func(Manager, 'end_transaction')
    wrapped = tag([])

    with wrapped:
        if should_rollback:
            rollback()

    assert len(mock_start.calls) == 1
    assert len(mock_end.calls) == 1
    assert mock_end.kwargs == {'do_rollback': should_rollback}
