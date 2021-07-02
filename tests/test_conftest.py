class SampleClass:
    def sample_method(self, arg, kwarg=None):
        return f"Values: {arg} {kwarg}"


def test_mock_function(mock_func):
    mock_initiate = mock_func(SampleClass, 'sample_method', return_value='sample value')

    return_value = SampleClass().sample_method(kwarg='123')

    assert return_value == 'sample value'
    assert mock_initiate.kwargs == {'kwarg': '123'}


def test_many_calls(mock_func):
    mock = mock_func(SampleClass, 'sample_method')

    SampleClass().sample_method('000', kwarg='123')
    SampleClass().sample_method('000')

    assert (('000',), {'kwarg': '123'}) in mock.calls

    assert mock.calls == [
        (('000',), {'kwarg': '123'}),
        (('000',), None),
    ]


def test_any(mock_func, any):
    mock = mock_func(SampleClass, 'sample_method')

    SampleClass().sample_method('000', kwarg='123')

    assert mock.calls == [((any,), {'kwarg': '123'})]


def test_multiline_cleaner(multiline_cleaner):
    assert multiline_cleaner('''
        abracadabra
    ''') == 'abracadabra\n'
