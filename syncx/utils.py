from typing import Sequence


def flatten(lst: Sequence) -> list:
    """
    Flatten one level in the given list.
    """
    return [item for sublist in lst for item in sublist]