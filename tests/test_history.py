import pytest

import dictdiffer
from syncx import redo
from syncx import tag
from syncx import undo
from syncx.exceptions import HistoryError


def test_history_indexing(mock_func):
    mock_func(dictdiffer, 'patch')

    manager = tag({}, history=True)._manager

    assert manager.add_history_entry(1) == 1
    assert manager.history.entries == [1]

    assert manager.add_history_entry(2) == 2
    assert manager.history.entries == [1, 2]

    assert manager.undo() == 1

    assert manager.redo() == 2

    assert manager.redo() == 2

    assert manager.undo() == 1
    assert manager.add_history_entry(3) == 2
    assert manager.history.entries == [1, 3]

    manager.undo()
    assert manager.undo() == 0
    assert manager.undo() == 0

    assert manager.add_history_entry(4) == 1
    assert manager.history.entries == [4]


def test_history_used_before_activated():
    tagged = tag({})
    with pytest.raises(HistoryError):
        undo(tagged)


def test_history_patching():
    data = {'a': 1}
    manager = tag(data, history=True)._manager
    manager.add_history_entry([('add', '', [('a', 1)])])

    manager.undo()
    assert data == {}

    manager.redo()
    assert data == {'a': 1}


def test_history_capacity(mock_func):
    mock_func(dictdiffer, 'patch')
    manager = tag({})._manager
    manager.set_history()._capacity = 4

    [manager.add_history_entry(entry) for entry in range(4)]
    assert manager.history.entries == [0, 1, 2, 3]

    manager.add_history_entry(4)
    assert manager.history.entries == [1, 2, 3, 4]

    manager.undo()
    manager.add_history_entry(5)
    manager.add_history_entry(6)
    assert manager.history.entries == [2, 3, 5, 6]


def test_undo_redo():
    my_data = tag({'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}, history=True)

    my_data['e'].add(2)
    assert 2 in my_data['e']

    undo(my_data)
    assert my_data == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}

    my_data['a'][1]['c'] = 3
    assert my_data['a'][1]['c'] == 3

    undo(my_data)
    assert my_data['a'][1]['c'] == 0

    redo(my_data)
    assert my_data['a'][1]['c'] == 3

    my_data['a'][1]['c'] = {'f': 3}
    assert my_data['a'][1]['c'] == {'f': 3}

    my_data['a'][1]['c']['f'] = 4
    undo(my_data)
    assert my_data['a'][1]['c']['f'] == 3
