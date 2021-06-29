from types import SimpleNamespace

import pytest

from syncx.track import is_trackable


@pytest.mark.parametrize('factory', (dict, list, set, SimpleNamespace))
def test_is_trackable(factory):
    assert is_trackable(factory())


