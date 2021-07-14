from types import SimpleNamespace

import dictdiffer


class History:

    def __init__(self, capacity=None):
        self._capacity = capacity
        self._ignore_changes = False

        self.current_index = 0
        self.entries = []

    @property
    def on(self) -> bool:
        return not self._ignore_changes

    @on.setter
    def on(self, value: bool):
        self._ignore_changes = not value