from types import SimpleNamespace

from syncx import path
from syncx import tag
from syncx import untag


def check_callback(wrapped, callback):
    assert len(callback.calls) == 1
    details = callback.calls[0].args[0]
    assert details.location is wrapped
    assert details.path_to_location == []


def test_dict(mock_simple):
    wrapped = tag(dict(), mock_simple)
    wrapped['key'] = 'value'

    check_callback(wrapped, mock_simple)


def test_list(mock_simple):
    wrapped = tag(list(), mock_simple)
    wrapped.append('value')

    check_callback(wrapped, mock_simple)


def test_set(mock_simple):
    wrapped = tag(set(), mock_simple)
    wrapped.add('value')

    check_callback(wrapped, mock_simple)


def test_custom_object(mock_simple):
    wrapped = tag(SimpleNamespace(test='initial value'), mock_simple)
    wrapped.test = 'value'

    check_callback(wrapped, mock_simple)

    assert wrapped._manager.root_type is SimpleNamespace


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
