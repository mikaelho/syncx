from syncx import wrap
from syncx.manager import Manager


def test_start_sync__defaults(get_test_data_file, tmp_path):
    expected_contents = get_test_data_file('dump.yaml')
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    manager = Manager()
    already_wrapped = wrap(my_data)
    wrapped = manager.start_sync(already_wrapped, str(tmp_path / 'test'))

    assert wrapped == already_wrapped
    assert (tmp_path / 'test.yaml').read_text() == expected_contents


def test_start_sync__file_exists(path_to_test_data):
    manager = Manager()
    initial_data = wrap({})
    name = str(path_to_test_data / 'dump')
    wrapped = manager.start_sync(initial_data, name)

    assert wrapped == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
