from syncx.backend import FileBackend
from syncx.serializer import YamlSerializer


def test_file__put(get_test_data_file, tmp_path):
    expected_contents = get_test_data_file('dump.yaml')
    serializer = YamlSerializer()
    backend = FileBackend(str(tmp_path / 'test'))
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    backend.put(my_data, serializer)

    assert (tmp_path / 'test.yaml').read_text() == expected_contents


def test_file__get(path_to_test_data):
    expected_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    serializer = YamlSerializer()
    backend = FileBackend(str(path_to_test_data / 'dump'))
    data = backend.get(serializer)

    assert data == expected_data
