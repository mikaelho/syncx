import json
import logging
from pathlib import Path
from typing import Sequence
from typing import Union

import pytest


@pytest.fixture
def any():
    """
    Can be used to match any value.
    """
    class Any:
        def __eq__(self, other):
            return True
    return Any()


class MockFunc:

    def __init__(self):
        self.args = self.kwargs = None
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.calls.append((args or None, kwargs or None))

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
def get_test_data(path_to_test_data):
    return lambda filename: json.loads((path_to_test_data / filename).read_text())


@pytest.fixture
def catcher():
    class Catcher:
        def __init__(self):
            self.paths = []
            self.function_names = []
            self.args_list = []
            self.kwargs_list = []

        def changed(self, path, function_name, args, kwargs):
            self.paths.append(path)
            self.function_names.append(function_name)
            self.args_list.append(args)
            self.kwargs_list.append(kwargs)

    return Catcher()
