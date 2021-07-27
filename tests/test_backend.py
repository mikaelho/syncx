from pathlib import Path

import pytest

from syncx.backend import FileBackend
from syncx.serializer import YamlSerializer


def test_file__put(get_test_data_file, tmp_path):
    expected_contents = get_test_data_file('dump.yaml')
    serializer = YamlSerializer()
    backend = FileBackend(str(tmp_path / 'test.yaml'))
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    backend.put(my_data, serializer)

    assert (tmp_path / 'test.yaml').read_text() == expected_contents


def test_file__put__no_change_if_error(tmp_path, mock_func):
    serializer = YamlSerializer()
    backend = FileBackend(str(tmp_path / 'test.yaml'))
    my_data = {'value': 'initial'}
    backend.put(my_data, serializer)

    my_changed_data = {'value': 'changed'}

    mock_func(Path, 'write_text', exception=NotADirectoryError())
    with pytest.raises(NotADirectoryError):
        backend.put(my_changed_data, serializer)

    assert (tmp_path / 'test.yaml').read_text().strip() == 'value: initial'


def test_file__get(path_to_test_data):
    expected_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    serializer = YamlSerializer()
    backend = FileBackend(str(path_to_test_data / 'dump.yaml'))
    data = backend.get(serializer)

    assert data == expected_data
