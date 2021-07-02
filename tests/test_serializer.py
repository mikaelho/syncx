import io

from syncx.serializer import YamlSerializer


def test_serialize__yaml(get_test_data_file):
    serializer = YamlSerializer()
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    stream = io.StringIO()
    serializer.dump(my_data, stream)

    assert stream.getvalue() == get_test_data_file('dump.yaml')


def test_deserialize__yaml(get_test_data_file):
    stream = io.StringIO(get_test_data_file('dump.yaml'))
    serializer = YamlSerializer()
    result = serializer.load(stream)

    assert result == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
