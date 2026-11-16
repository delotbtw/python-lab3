from enum import Enum

MIN_YEAR = 1450
ISBN_LENGTH = 13
FORMAT_VERSION = 1


class ChangeKind(Enum):
    ADD = "add"
    REMOVE = "remove"
