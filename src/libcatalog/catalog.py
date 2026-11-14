from abc import ABC, abstractmethod
from collections.abc import Iterator

from libcatalog.errors import DuplicateIdError, InvalidEntityError, ItemNotFoundError
from libcatalog.models import Book


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

    def add(self, item: Book) -> None:
        """Add book to catalog"""
        if not isinstance(item, Book):
            raise InvalidEntityError(f"not a book: {item!r}")
        if item.id in self._items:
            raise DuplicateIdError(item.id)
        self._items[item.id] = item

    def get(self, item_id: str) -> Book:
        """Get book by id"""
        try:
            return self._items[item_id]
        except (KeyError, TypeError):
            raise ItemNotFoundError(str(item_id)) from None

    def remove(self, item_id: str) -> Book:
        """Remove book by id and return it"""
        book = self.get(item_id)
        del self._items[item_id]
        return book

    def find_by_category(self, category: str) -> tuple[Book, ...]:
        """Find books by category, ignore case"""
        key = category.strip().casefold()
        return tuple(b for b in self._items.values() if b.category.casefold() == key)

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
