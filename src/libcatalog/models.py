from dataclasses import MISSING, asdict, dataclass, fields
from datetime import date
from typing import Any, Self

from libcatalog.core import ISBN_LENGTH, MIN_YEAR
from libcatalog.errors import InvalidEntityError


def _isbn13_is_valid(digits: str) -> bool:
    """Check isbn-13 control digit"""
    if len(digits) != ISBN_LENGTH or not digits.isdigit():
        return False
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits))
    return total % 10 == 0


@dataclass(frozen=True)
class Book:
    """Library book, can not change after create"""

    id: str
    title: str
    category: str
    year: int
    author: str
    isbn: str

    def __post_init__(self) -> None:
        """Check book fields"""
        for name in ("id", "title", "category", "author"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidEntityError(f"empty or invalid {name}")
        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise InvalidEntityError(f"year must be int: {self.year!r}")
        if not MIN_YEAR <= self.year <= date.today().year:
            raise InvalidEntityError(f"year out of range: {self.year}")
        if not isinstance(self.isbn, str) or not _isbn13_is_valid(
            self.isbn.replace("-", "")
        ):
            raise InvalidEntityError(f"invalid isbn: {self.isbn!r}")

    def to_dict(self) -> dict[str, Any]:
        """Book to dict"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: object) -> Self:
        """Make book from dict"""
        if not isinstance(data, dict):
            raise InvalidEntityError("book must be an object")
        known = {f.name: f for f in fields(cls)}

        unknown = sorted(set(data) - set(known))
        if unknown:
            raise InvalidEntityError(f"unknown fields: {', '.join(unknown)}")

        missing = [
            name
            for name, f in known.items()
            if name not in data
            and f.default is MISSING
            and f.default_factory is MISSING
        ]
        if missing:
            raise InvalidEntityError(f"missing fields: {', '.join(missing)}")
        return cls(**data)
