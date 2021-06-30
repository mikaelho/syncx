from types import SimpleNamespace

from syncx.wrappers import unwrap
from syncx.wrappers import wrap


def test_dict(mock_simple):
    wrapped = wrap(dict(), mock_simple)
    wrapped['key'] = 'value'

    assert len(mock_simple.calls) == 1
    path, function_name, args, kwargs = mock_simple.calls[0].args
    assert path == []
    assert function_name == '__setitem__'
    assert args == ('key', 'value')


def test_list(mock_simple):
    wrapped = wrap(list(), mock_simple)
    wrapped.append('value')

    assert len(mock_simple.calls) == 1
    path, function_name, args, kwargs = mock_simple.calls[0].args
    assert path == []
    assert function_name == 'append'
    assert args == ('value',)


def test_set(mock_simple):
    wrapped = wrap(set(), mock_simple)
    wrapped.add('value')

    assert len(mock_simple.calls) == 1
    path, function_name, args, kwargs = mock_simple.calls[0].args
    assert path == []
    assert function_name == 'add'
    assert args == ('value',)


def test_custom_object(mock_simple):
    wrapped = wrap(SimpleNamespace(test='value'), mock_simple)
    wrapped.test = 'new value'

    assert len(mock_simple.calls) == 1
    path, function_name, args, kwargs = mock_simple.calls[0].args
    assert path == []
    assert function_name == '__setattr__'
    assert args == ('test', 'new value')


def test_multiple_levels(catcher):
    wrapped = wrap(SimpleNamespace(
        data={
            'key': [
                'value1',
            ]
        }
    ), catcher.changed
    )
    wrapped.data['key'].append(set())
    wrapped.data['key'][1].add('value2')

    assert catcher.paths == [[], ['key'], ['key', 1]]
    assert catcher.function_names == ['__setitem__', 'append', 'add']


def test_same_object_different_paths(catcher):
    root = wrap({'a': {}}, catcher.changed)
    root['b'] = root['a']
    root['a']['aa'] = 1
    root['b']['aa'] = 2
    root['a']['aa'] = 3


    assert catcher.paths == [[], ['a'], ['b'], ['a']]  # Different paths preserved
    assert root['a'] == root['b']  # But same object
    assert root['b']['aa'] == 3  # Same values


def test_revert_to_regular(catcher):
    wrapped = wrap({'a': [{'b'}]}, catcher.changed)
    original = unwrap(wrapped)
    assert type(original) is dict
    assert type(original['a']) is list
    assert type(original['a'][0]) is set
