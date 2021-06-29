from syncx.vendored.proxies import ObjectProxy


def test_object_proxy():
    proxy = ObjectProxy({'a': 1})

    assert proxy['a'] == 1
    assert type(proxy) is ObjectProxy
    assert type(proxy.__subject__) is dict
