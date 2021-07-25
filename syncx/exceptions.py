class LockingRaceCondition(Exception):
    """
    Raised when not able to lock data access within Manager.LOCK_TIMOUT seconds.
    """
    pass


class Rollback(Exception):
    """
    Trigger rollback without raising a visible exception.

    Not usable within nested transaction contexts like `with a, b:`.
    """
    pass


class HistoryError(Exception):
    """
    Raised when trying to use `undo` or `redo` with data that does not have history enabled or active.
    """
    pass


class UnresolvableConflict(Exception): pass
