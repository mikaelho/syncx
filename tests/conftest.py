import json
import logging
from collections import namedtuple
from pathlib import Path
from textwrap import dedent
from typing import Sequence
from typing import Union

import pytest

from syncx import path


@pytest.fixture
def any():
    """
    Can be used to match any value.
    """
    class Any:
        def __eq__(self, other):
            return True
    return Any()


Call = namedtuple('Call', 'args kwargs')

class MockFunc:

    def __init__(self):
        self.args = self.kwargs = None
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.calls.append(Call(args or None, kwargs or None))

        if hasattr(self, 'return_value'):
            return self.return_value


@pytest.fixture
def mock_simple():
    return MockFunc()


@pytest.fixture
def mock_func(monkeypatch):
    """Call fixture with the target, key and an optional return_value. Returns a mocked function."""

    def get_mock(obj, key, return_value=None):
        monkey_func = MockFunc()
        monkey_func.return_value = return_value
        monkeypatch.setattr(obj, key, monkey_func)
        return monkey_func
    return get_mock


@pytest.fixture
def mock_logger_info(mock_func):
    return mock_func(logging.Logger, 'info')


@pytest.fixture
def mock_logger_error(mock_func):
    return mock_func(logging.Logger, 'error')


@pytest.fixture
def mock_logger_exception(mock_func):
    return mock_func(logging.Logger, 'exception')


@pytest.fixture
def path_to_test_data() -> Path:
    return Path(__file__).parent / 'test_data'


@pytest.fixture
def get_test_file(path_to_test_data):
    return lambda filename: (path_to_test_data / filename).read_text()


@pytest.fixture
def get_test_data(path_to_test_data):
    return lambda filename: json.loads((path_to_test_data / filename).read_text())


@pytest.fixture
def catcher():
    class Catcher:
        def __init__(self):
            self.paths = []

        def changed(self, obj):
            self.paths.append(path(obj))

    return Catcher()


@pytest.fixture
def multiline_cleaner():
    def cleaner(text: str) -> str:
        text = ''.join(line for line in text.splitlines(keepends=True) if line.strip() != '')
        return dedent(text)
    return cleaner