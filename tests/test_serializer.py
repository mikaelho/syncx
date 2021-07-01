from syncx.serializer import YamlSerializer


def test_yaml_serializer(get_test_file):
    serializer = YamlSerializer()
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}

    serialized = serializer.dumps(my_data)

    assert serialized == get_test_file('dump.yaml')
