from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from libcatalog.core import ChangeKind
from libcatalog.errors import (
    DuplicateIdError,
    InvalidEntityError,
    ItemNotFoundError,
    NothingToUndoError,
    TransactionError,
)
from libcatalog.models import Book
from libcatalog.storage import read_books, save_books


class ReadOnlyCatalog(ABC):
    """Methods for reading catalog"""

    @abstractmethod
    def get(self, item_id: str) -> Book:
        """Get book by id"""

    @abstractmethod
    def find_by_category(self, category: str) -> tuple[Book, ...]:
        """Find books by category"""

    @abstractmethod
    def find_by_name(self, query: str) -> tuple[Book, ...]:
        """Find books by part of title"""

    @abstractmethod
    def __len__(self) -> int:
        """Count of books"""

    @abstractmethod
    def __iter__(self) -> Iterator[Book]:
        """Iterate books in order of adding"""

    @abstractmethod
    def __contains__(self, item_id: object) -> bool:
        """Check id in catalog"""


@dataclass(frozen=True)
class Change:
    """Record of operation for undo"""

    kind: ChangeKind
    book: Book
    seq: int


class Catalog(ReadOnlyCatalog):
    """Catalog of books. Iteration go in order of adding."""

    def __init__(self) -> None:
        self._items: dict[str, Book] = {}
        self._by_category: dict[str, dict[str, None]] = {}
        self._seq: dict[str, int] = {}
        self._next_seq = 0
        self._journal: list[Change] = []
        self._tx_depth = 0

    @staticmethod
    def _category_key(category: str) -> str:
        return category.strip().casefold()

    def _put(self, book: Book, seq: int | None = None) -> None:
        if seq is None:
            seq = self._next_seq
            self._next_seq += 1
        self._items[book.id] = book
        self._seq[book.id] = seq
        key = self._category_key(book.category)
        self._by_category.setdefault(key, {})[book.id] = None

    def _drop(self, item_id: str) -> Book:
        book = self._items.pop(item_id)
        del self._seq[item_id]
        key = self._category_key(book.category)
        ids = self._by_category[key]
        del ids[item_id]
        if not ids:
            del self._by_category[key]
        return book

    def add(self, item: Book) -> None:
        """Add book to catalog"""
        if not isinstance(item, Book):
            raise InvalidEntityError(f"not a book: {item!r}")
        if item.id in self._items:
            raise DuplicateIdError(item.id)

        self._put(item)
        self._journal.append(Change(ChangeKind.ADD, item, self._seq[item.id]))

    def get(self, item_id: str) -> Book:
        """Get book by id"""
        try:
            return self._items[item_id]
        except (KeyError, TypeError):
            raise ItemNotFoundError(str(item_id)) from None

    def remove(self, item_id: str) -> Book:
        """Remove book by id and return it"""
        self.get(item_id)

        seq = self._seq[item_id]
        book = self._drop(item_id)
        self._journal.append(Change(ChangeKind.REMOVE, book, seq))
        return book

    def undo(self) -> None:
        """Undo last add or remove"""
        if self._tx_depth:
            raise TransactionError("undo is not allowed inside a transaction")
        if not self._journal:
            raise NothingToUndoError
        self._revert(self._journal.pop())

    @contextmanager
    def transaction(self) -> Iterator[Self]:
        """Rollback all changes in block if error"""
        mark = len(self._journal)
        self._tx_depth += 1
        try:
            yield self
        except BaseException:
            while len(self._journal) > mark:
                self._revert(self._journal.pop())
            raise
        finally:
            self._tx_depth -= 1

    def _revert(self, change: Change) -> None:
        if change.kind == ChangeKind.ADD:
            self._drop(change.book.id)
            return

        self._put(change.book, change.seq)
        self._items = dict(sorted(self._items.items(), key=lambda kv: self._seq[kv[0]]))

        self._by_category = {}
        for book in self._items.values():
            key = self._category_key(book.category)
            self._by_category.setdefault(key, {})[book.id] = None

    def save(self, path: str | Path) -> None:
        """Save catalog in json file"""
        save_books(self, path)

    def load(self, path: str | Path) -> None:
        """Load catalog from json, if error catalog not change"""
        if self._tx_depth:
            raise TransactionError("load is not allowed inside a transaction")
        fresh = Catalog()
        for book in read_books(path):
            fresh.add(book)
        self._items = fresh._items
        self._by_category = fresh._by_category
        self._seq = fresh._seq
        self._next_seq = fresh._next_seq
        self._journal = []

    def find_by_category(self, category: str) -> tuple[Book, ...]:
        """Find books by category, ignore case"""
        ids = self._by_category.get(self._category_key(category), {})
        return tuple(self._items[i] for i in ids)

    def find_by_name(self, query: str) -> tuple[Book, ...]:
        """Find books with query in title, ignore case"""
        key = query.strip().casefold()
        if not key:
            return ()

        return tuple(b for b in self._items.values() if key in b.title.casefold())

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Book]:
        return iter(tuple(self._items.values()))

    def __contains__(self, item_id: object) -> bool:
        return isinstance(item_id, str) and item_id in self._items
