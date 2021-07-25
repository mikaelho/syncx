from syncx.utils import flatten


def test_flatten():
    assert flatten([[1], [2]]) == [1, 2]
