from types import SimpleNamespace

import pytest

import dictdiffer
import syncx
from syncx import manage
from syncx import rollback
from syncx import tag
from syncx.history import History
from syncx.manager import Manager
from syncx.manager import ManagerInterface
from syncx.wrappers import CustomObjectWrapper


def test_interface():
    my_data = {'value': 'initial'}
    my_data = tag(my_data)

    manager_interface = manage(my_data)
    assert type(manager_interface) == ManagerInterface

    manager_interface_2 = manage(my_data)
    assert manager_interface.history == manager_interface_2.history


def test_history_indexing(mock_func):
    mock_func(dictdiffer, 'patch')

    manager = tag({})._manager

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


def test_history_patching():
    data = {'a': 1}
    manager = tag(data)._manager
    manager.add_history_entry([('add', '', [('a', 1)])])

    manager.undo()
    assert data == {}

    manager.redo()
    assert data == {'a': 1}


def test_history_capacity(mock_func):
    mock_func(dictdiffer, 'patch')
    manager = tag({})._manager
    manager.get_history()._capacity = 4

    [manager.add_history_entry(entry) for entry in range(4)]
    assert manager.history.entries == [0, 1, 2, 3]

    manager.add_history_entry(4)
    assert manager.history.entries == [1, 2, 3, 4]

    manager.undo()
    manager.add_history_entry(5)
    manager.add_history_entry(6)
    assert manager.history.entries == [2, 3, 5, 6]


def test_undo_redo():
    my_data = tag({'a': ['b', {'c': 0, 'd': 1}], 'e': {1}})
    manager = manage(my_data)

    my_data['e'].add(2)
    assert 2 in my_data['e']

    manager.undo()
    assert my_data == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}

    my_data['a'][1]['c'] = 3
    assert my_data['a'][1]['c'] == 3

    manager.undo()
    assert my_data['a'][1]['c'] == 0

    manager.redo()
    assert my_data['a'][1]['c'] == 3

    my_data['a'][1]['c'] = {'f': 3}
    assert my_data['a'][1]['c'] == {'f': 3}

    my_data['a'][1]['c']['f'] = 4
    manager.undo()
    assert my_data['a'][1]['c']['f'] == 3


def test_context_manager__no_rollback():
    wrapped = tag({'a': 1})

    with wrapped:
        wrapped['a'] = 2

    assert wrapped['a'] == 2


def test_context_manager__exception():
    wrapped = tag({'a': 1})

    with pytest.raises(RuntimeError):
        with wrapped:
            wrapped['a'] = 2
            raise RuntimeError('Boom')

    assert wrapped['a'] == 1


def test_context_manager__rollback():
    wrapped = tag({'a': 1})

    with wrapped:
        wrapped['a'] = 2
        wrapped['a'] = 3
        rollback()

    assert wrapped['a'] == 1


def test_context_manager__rollback_with_object():
    wrapped = tag(SimpleNamespace(a=1))

    with wrapped:
        wrapped.a = 2
        wrapped.a = 3
        rollback()

    assert wrapped.a == 1


def test_history_wrapping_and_rollback(mock_func):
    manager = tag({})._manager
    history = manager.get_history()
    assert type(history) is CustomObjectWrapper

    manager.add_history_entry('first entry')
    assert history._manager.all_changes == []
    assert history.current_index == 1

    with history:
        manager.add_history_entry('second entry')
        assert history._manager.all_changes == [
            [('add', '__dict__.entries', [(1, 'second entry')])],
            [('change', '__dict__.current_index', (1, 2))],
        ]
        rollback()

    assert history._manager.all_changes == []
    assert history.current_index == 1


def test_context_manager__with_history():
    wrapped = tag({'a': 1})
    manager = manage(wrapped)
    manager.history_on = True

    wrapped['a'] = 2

    with wrapped:
        wrapped['a'] = 3
        manager.undo()
        manager.undo()
        assert wrapped['a'] == 1
        rollback()

    assert wrapped['a'] == 2
    manager.undo()
    assert wrapped['a'] == 1


def test_start_sync__defaults(get_test_data_file, tmp_path):
    expected_contents = get_test_data_file('dump.yaml')
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    manager = Manager()
    already_wrapped = tag(my_data)
    wrapped = manager.start_sync(already_wrapped, str(tmp_path / 'test'))

    assert wrapped == already_wrapped
    assert (tmp_path / 'test.yaml').read_text() == expected_contents


def test_start_sync__file_exists(path_to_test_data):
    initial_data = tag({})
    name = str(path_to_test_data / 'dump')
    wrapped = initial_data._manager.start_sync(initial_data, name)

    assert wrapped == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}


def test_start_sync__file_exists__custom_type(path_to_test_data):
    initial_data = tag(SimpleNamespace)

    name = str(path_to_test_data / 'dump')
    wrapped = initial_data._manager.start_sync(initial_data, name)

    assert wrapped.a == ['b', {'c': 0, 'd': 1}]
    assert wrapped.e == {1}
