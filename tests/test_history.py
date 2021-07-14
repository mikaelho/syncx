import dictdiffer
import syncx.exceptions
from syncx import tag
from syncx.history import History
from syncx.wrappers import CustomObjectWrapper


def test_history_indexing(mock_func):
    mock_func(dictdiffer, 'patch')

    history = History({})

    assert history.add_entry(1) == 1
    assert history.data.entries == [1]

    assert history.add_entry(2) == 2
    assert history.data.entries == [1, 2]

    assert history.undo() == 1

    assert history.redo() == 2

    assert history.redo() == 2

    assert history.undo() == 1
    assert history.add_entry(3) == 2
    assert history.data.entries == [1, 3]

    history.undo()
    assert history.undo() == 0
    assert history.undo() == 0

    assert history.add_entry(4) == 1
    assert history.data.entries == [4]


def test_history_patching():
    data = {'a': 1}
    history = History(data)
    history.add_entry([('add', '', [('a', 1)])])

    history.undo()
    assert data == {}

    history.redo()
    assert data == {'a': 1}


def test_history_capacity(mock_func):
    mock_func(dictdiffer, 'patch')

    history = History({}, capacity=4)

    [history.add_entry(entry) for entry in range(4)]
    assert history.data.entries == [0, 1, 2, 3]

    history.add_entry(4)
    assert history.data.entries == [1, 2, 3, 4]

    history.undo()
    history.add_entry(5)
    history.add_entry(6)
    assert history.data.entries == [2, 3, 5, 6]


def test_history_wrapping_and_rollback(mock_func):
    mock_func(dictdiffer, 'patch')

    history = tag(History({}))
    assert type(history) is CustomObjectWrapper

    history.add_entry('first entry')
    assert history._manager.all_changes == []

    with history:
        history.add_entry('second entry')
        assert history._manager.all_changes == [
            [('add', '__dict__.data.__dict__.entries', [(1, 'second entry')])],
            [('change', '__dict__.data.__dict__.current_index', (1, 2))],
        ]
        raise syncx.exceptions.Rollback()

    assert history._manager.all_changes == []
    assert history.data.current_index == 1

    # assert history._manager.all_changes == [
    #     [('add', '__dict__.data.__dict__.entries', [(0, 'dummy entry')])],
    #     [('change', '__dict__.data.__dict__.current_index', (0, 1))],
    #     [('change', '__dict__.data.__dict__.__dict__.current_index', (1, 0))]
    # ]
