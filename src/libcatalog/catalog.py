from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from libcatalog.errors import DuplicateIdError, InvalidEntityError, ItemNotFoundError
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


class Catalog(ReadOnlyCatalog):
    """Catalog of books. Iteration go in order of adding."""

    def __init__(self) -> None:
        self._items: dict[str, Book] = {}
        self._by_category: dict[str, dict[str, None]] = {}

    @staticmethod
    def _category_key(category: str) -> str:
        return category.strip().casefold()

    def _put(self, book: Book) -> None:
        self._items[book.id] = book
        key = self._category_key(book.category)
        self._by_category.setdefault(key, {})[book.id] = None

    def _drop(self, item_id: str) -> Book:
        book = self._items.pop(item_id)
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

    def get(self, item_id: str) -> Book:
        """Get book by id"""
        try:
            return self._items[item_id]
        except (KeyError, TypeError):
            raise ItemNotFoundError(str(item_id)) from None

    def remove(self, item_id: str) -> Book:
        """Remove book by id and return it"""
        self.get(item_id)

        return self._drop(item_id)

    def save(self, path: str | Path) -> None:
        """Save catalog in json file"""
        save_books(self, path)

    def load(self, path: str | Path) -> None:
        """Load catalog from json, if error catalog not change"""
        fresh = Catalog()
        for book in read_books(path):
            fresh.add(book)
        self._items = fresh._items
        self._by_category = fresh._by_category

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
