import dictdiffer
from syncx.history import History


def test_history_indexing(mock_func):
    mock_func(dictdiffer, 'patch')

    history = History({})

    history.add_entry(1)
    assert history == [1]

    history.add_entry(2)
    assert history == [2, 1]
    assert history.current_index == 0

    current_index = history.undo()
    assert current_index == 1

    current_index = history.redo()
    assert current_index == 0

    current_index = history.redo()
    assert current_index == 0

    history.undo()
    history.add_entry(3)
    assert history == [3, 1]

    history.undo()
    current_index = history.undo()
    assert current_index == 2

    history.undo()
    assert current_index == 2

    history.add_entry(4)
    assert history == [4]


def test_history_patching():
    data = {'a': 1}
    history = History(data)
    history.add_entry([('add', '', [('a', 1)])])

    history.undo()
    assert data == {}

    history.redo()
    assert data == {'a': 1}
