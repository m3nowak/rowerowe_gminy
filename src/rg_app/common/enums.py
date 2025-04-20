from enum import IntEnum


class DescUpdateOptions(IntEnum):
    """Enum for description update options."""

    NONE = 0
    NEW_ONLY = 10
    ALL = 20
