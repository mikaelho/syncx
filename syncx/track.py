from typing import Any
from typing import MutableMapping
from typing import MutableSequence
from typing import MutableSet

try:
    import pydantic
except ImportError:
    is_pydantic_available = False
else:
    is_pydantic_available = True

from syncx.wrappers import TrackerWrapper


def track(target: Any, change_callback: callable):
    ...


def is_tracked(obj: Any) -> bool:
    return issubclass(type(obj), TrackerWrapper)


def is_trackable(target: Any) -> bool:
    return any((
        is_tracked(target),
        isinstance(target, (MutableSequence, MutableMapping, MutableSet)),
        is_pydantic_available and isinstance((target, pydantic.BaseModel)),
        hasattr(target, '__dict__'),
    ))


class TrackingManager:

    def __init__(self, target: Any, change_callback: callable):
        self.change_callback = change_callback
        self.root = self.start_to_track(target)

    def start_to_track(self, target: Any):
        ...