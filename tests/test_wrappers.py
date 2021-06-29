import pytest

from syncx.wrappers import wrap_target


def test_wrappers__dict(mock_simple):
    wrapped = wrap_target(dict(), mock_simple)
    wrapped['key'] = 'value'
    assert len(mock_simple.calls) == 1
    keys, mutation = mock_simple.calls[0]
    assert keys == ([],)
    assert mutation['function_name'] == '__setitem__'
    assert mutation['args'] == ('key', 'value')


def test_wrappers__list(mock_simple):
    wrapped = wrap_target(list(), mock_simple)
    wrapped.append('value')
    assert len(mock_simple.calls) == 1
    keys, mutation = mock_simple.calls[0]
    assert keys == ([],)
    assert mutation['function_name'] == 'append'
    assert mutation['args'] == ('value',)


def test_wrappers__set(mock_simple):
    wrapped = wrap_target(set(), mock_simple)
    wrapped.add('value')
    assert len(mock_simple.calls) == 1
    keys, mutation = mock_simple.calls[0]
    assert keys == ([],)
    assert mutation['function_name'] == 'add'
    assert mutation['args'] == ('value',)


def test_wrappers__multiple_levels(catcher):
    wrapped = wrap_target(dict(), catcher.changed)
    wrapped['key'] = ['value1']
    wrapped['key'].append(set())
    wrapped['key'][1].add('value2')

    assert catcher.paths == [[], ['key'], ['key', 1]]
    assert catcher.function_names == ['__setitem__', 'append', 'add']
