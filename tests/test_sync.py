from dataclasses import astuple

import pytest

from dictdiffer import diff
from syncx.sync_logic import Content
from syncx.sync_logic import DeltaSignature
from syncx.sync_logic import DeltaWithSignature
from syncx.sync_logic import MultiClientIncremental
from syncx.sync_logic import get_signature


def test_get_signature():
    assert astuple(get_signature(None, 'foobar')) == (0, '5f6f3065208dde5f4624d7dfafc36a296a526590')
    assert astuple(get_signature(DeltaSignature(1, 'aaa'), 'foobar')) == (2, '5f6f3065208dde5f4624d7dfafc36a296a526590')


@pytest.mark.parametrize('remote_object, should_be_ok', (
    ({'a': 1}, True),
    ({'b': 1}, False),
    ({'b': 2}, True),
))
def test_ok_to_apply__no_unapplied_deltas(remote_object, should_be_ok):
    baseline = {}
    local_object = {'b': 2}

    content = Content(
        latest_signature=get_signature(None, list(diff(baseline, remote_object))),
        full_object=remote_object,
    )
    local_delta = list(diff(baseline, local_object))
    local_latest_signature = get_signature(None, local_delta)

    assert MultiClientIncremental(None, None).ok_to_apply(
        content,
        local_latest_signature,
        local_delta,
        local_object,
    ) == should_be_ok

@pytest.mark.parametrize('remote_object, should_be_ok', (
    ({'a': 1, 'b': 1}, True),
    ({'a': 1, 'c': 2}, False),
    ({'a': 1, 'c': 1}, True),
))
def test_ok_to_apply__with_unapplied_deltas(remote_object, should_be_ok):
    baseline = {}
    shared_changed_baseline = {'a': 1}
    shared_delta = list(diff(baseline, shared_changed_baseline))
    shared_signature = get_signature(None, shared_delta)
    local_object = {'a': 1, 'c': 1}

    diverging_delta = list(diff(shared_changed_baseline, remote_object))
    diverging_signature = get_signature(shared_signature, diverging_delta)
    content = Content(
        latest_signature=diverging_signature,
        full_object=baseline,
        unapplied_changes=[DeltaWithSignature(signature, delta) for signature, delta in (
            (shared_signature, shared_delta),
            (diverging_signature, diverging_delta),
        )]
    )
    local_delta = list(diff(shared_changed_baseline, local_object))
    local_latest_signature = get_signature(shared_signature, local_delta)

    assert MultiClientIncremental(None, None).ok_to_apply(
        content,
        local_latest_signature,
        local_delta,
        local_object,
    ) == should_be_ok