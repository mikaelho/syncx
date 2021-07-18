import time
from threading import Thread
from types import SimpleNamespace

import pytest

from syncx import rollback
from syncx import tag
from syncx import undo
from syncx.wrappers import CustomObjectWrapper


def test_no_rollback():
    wrapped = tag({'a': 1})

    with wrapped:
        wrapped['a'] = 2

    assert wrapped['a'] == 2


def test_exception():
    wrapped = tag({'a': 1})

    with pytest.raises(RuntimeError):
        with wrapped:
            wrapped['a'] = 2
            raise RuntimeError('Boom')

    assert wrapped['a'] == 1


def test_rollback():
    wrapped = tag({'a': 1})

    with wrapped:
        wrapped['a'] = 2
        wrapped['a'] = 3
        rollback()

    assert wrapped['a'] == 1


def test_rollback_with_object():
    wrapped = tag(SimpleNamespace(a=1))

    with wrapped:
        wrapped.a = 2
        wrapped.a = 3
        rollback()

    assert wrapped.a == 1


def test_history_wrapping_and_rollback(mock_func):
    manager = tag({})._manager
    history = manager.set_history()
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


def test_with_history():
    wrapped = tag({'a': 1}, history=True)

    wrapped['a'] = 2

    with wrapped:
        wrapped['a'] = 3
        undo(wrapped)
        undo(wrapped)
        assert wrapped['a'] == 1
        rollback()

    assert wrapped['a'] == 2
    undo(wrapped)
    assert wrapped['a'] == 1


def test_multiple():
    a = tag([1])
    b = tag([2])

    with pytest.raises(RuntimeError):
        with a, b:
            a[0] = 3
            b[0] = 4
            raise RuntimeError('Something went wrong')

    assert a == [1]
    assert b == [2]


def test_thread_safety():
    def unsafe(counter):
        previous_value = counter['value']
        time.sleep(0)
        counter['value'] = previous_value + 1

    def safe(counter):
        with counter:
            previous_value = counter['value']
            time.sleep(0)
            counter['value'] = previous_value + 1

    def run_workers(worker):
        counter = tag({'value': 0})
        threads = [
            Thread(target=worker, args=(counter,))
            for _ in range(100)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return counter['value']

    assert run_workers(unsafe) != 100
    assert run_workers(safe) == 100
