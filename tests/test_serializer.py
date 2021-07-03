import dataclasses
import io
from types import SimpleNamespace

import pydantic

from syncx.serializer import JsonSerializer
from syncx.serializer import YamlSerializer


def test_to_yaml(get_test_data_file):
    serializer = YamlSerializer()
    my_data = {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}
    stream = io.StringIO()

    serializer.dump(my_data, stream)

    assert stream.getvalue() == get_test_data_file('dump.yaml')


def test_from_yaml(get_test_data_file):
    stream = io.StringIO(get_test_data_file('dump.yaml'))
    serializer = YamlSerializer()

    result = serializer.load(stream)

    assert result == {'a': ['b', {'c': 0, 'd': 1}], 'e': {1}}


def test_object_to_yaml(get_test_data_file):
    serializer = YamlSerializer()
    my_data = SimpleNamespace(value='initial')
    stream = io.StringIO()

    serializer.dump(my_data, stream)

    assert stream.getvalue().strip() == 'value: initial'


def test_dataclasses_to_yaml():
    serializer = YamlSerializer()

    class Model(pydantic.BaseModel):
        a: int
    stream = io.StringIO()
    serializer.dump(Model(a=1), stream)

    assert stream.getvalue().strip() == 'a: 1'


def test_pydantic_to_yaml():
    serializer = YamlSerializer()

    class Model(pydantic.BaseModel):
        a: int
    stream = io.StringIO()
    serializer.dump(Model(a=1), stream)

    assert stream.getvalue().strip() == 'a: 1'


def test_to_json(get_test_data_file):
    serializer = JsonSerializer()
    my_data = {'a': ['b', {'c': 0, 'd': 1}]}
    stream = io.StringIO()

    serializer.dump(my_data, stream)

    assert stream.getvalue() == get_test_data_file('dump.json')


def test_from_json(get_test_data_file):
    stream = io.StringIO(get_test_data_file('dump.json'))
    serializer = JsonSerializer()

    result = serializer.load(stream)

    assert result == {'a': ['b', {'c': 0, 'd': 1}]}


def test_object_to_json():
    serializer = JsonSerializer()
    my_data = SimpleNamespace(value='initial')
    stream = io.StringIO()

    serializer.dump(my_data, stream)

    assert stream.getvalue().strip() == '{"value":"initial"}'


def test_pydantic_to_json():
    serializer = JsonSerializer()

    class Model(pydantic.BaseModel):
        a: int
    stream = io.StringIO()
    serializer.dump(Model(a=1), stream)

    assert stream.getvalue().strip() == '{"a":1}'
