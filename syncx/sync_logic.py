import hashlib
import json
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Optional

import dictdiffer
from syncx.exceptions import UnresolvableConflict
from syncx.utils import flatten


@dataclass
class DeltaSignature:
    counter: int
    hash: str


@dataclass
class DeltaWithSignature:
    signature: DeltaSignature
    delta: Any


@dataclass
class Content:
    latest_signature: DeltaSignature
    full_object: Any
    unapplied_changes: List[DeltaWithSignature] = field(default_factory=list)


def get_signature(latest_signature: Optional[DeltaSignature], delta: Any):
    counter = latest_signature and latest_signature.counter + 1 or 0
    delta_as_string = json.dumps(delta, sort_keys=True)
    delta_hash = hashlib.sha1(delta_as_string.encode()).hexdigest()

    return DeltaSignature(counter, delta_hash)


class MultiClientIncremental:

    def __init__(self, frontend, backend):
        self.frontend = frontend
        self.backend = backend
        self.latest_signature = None

    def get_initial(self):
        content: Content
        with self.backend.get_content() as content:
            signature = None

            for change in content.unapplied_changes:
                dictdiffer.patch(change.delta, content, in_place=True)
                signature = change.signature

            self.latest_signature = signature
            self.backend.set_content(content, signature)

        return content

    def put(self, delta, local_object):
        signature = get_signature(self.latest_signature, delta)

        content: Content
        with self.backend.get_content() as content:
            in_sync = content.latest_signature == self.latest_signature

            try:
                unconflicting_remote_change = not in_sync and self.ok_to_apply(content, signature, delta, local_object)
            except Exception:
                unconflicting_remote_change = False

            if in_sync or unconflicting_remote_change:
                self.backend.add_to_deltas(signature, delta)

            if not in_sync:
                # TODO: Override local with remote
                ...

    def ok_to_apply(self, content: Content, signature: DeltaSignature, local_delta: Any, local_object: Any):
        pre_change = dictdiffer.revert(local_delta, local_object)

        # Check if there has just been some additional deltas recorded elsewhere
        for i, change in enumerate(content.unapplied_changes):
            if change.signature == signature:
                remote_delta = flatten([change.delta for change in content.unapplied_changes[i:]])
                remote_object = dictdiffer.patch(
                    flatten([change.delta for change in content.unapplied_changes[:i]]),
                    content.full_object,
                )
                break
        else: # Otherwise, do a full diff
            deltas = flatten([change.delta for change in content.unapplied_changes])
            remote_object = dictdiffer.patch(deltas, content.full_object)
            remote_delta = list(dictdiffer.diff(pre_change, remote_object))

        # Check if there is no actual conflict, i.e. it does not matter in which order the changes are applied
        # try:
        one_way = dictdiffer.patch(local_delta, pre_change)
        one_way = dictdiffer.patch(remote_delta, one_way, in_place=True)
        other_way = dictdiffer.patch(remote_delta, pre_change)
        other_way = dictdiffer.patch(local_delta, other_way, in_place=True)

        return one_way == other_way
