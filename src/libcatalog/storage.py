import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

from libcatalog.core import FORMAT_VERSION
from libcatalog.errors import (
    CorruptedFileError,
    DuplicateIdError,
    InvalidEntityError,
    UnsupportedVersionError,
)
from libcatalog.models import Book


def save_books(books: Iterable[Book], path: str | Path) -> None:
    """Write books to json file"""
    document = {
        "format_version": FORMAT_VERSION,
        "books": [book.to_dict() for book in books],
    }
    target = Path(path)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(document, tmp, ensure_ascii=False, indent=2)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def read_books(path: str | Path) -> list[Book]:
    """Read and check json file"""
    try:
        with open(path, encoding="utf-8") as f:
            document = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise CorruptedFileError(f"not a valid JSON: {e}") from e
    return parse_document(document)


def parse_document(document: object) -> list[Book]:
    """Check structure of document"""
    if not isinstance(document, dict):
        raise CorruptedFileError("root must be an object")
    if "format_version" not in document:
        raise CorruptedFileError("format_version is missing")
    version = document["format_version"]
    if version != FORMAT_VERSION or isinstance(version, bool):
        raise UnsupportedVersionError(version)
    raw_books = document.get("books")
    if not isinstance(raw_books, list):
        raise CorruptedFileError("books must be a list")

    books: list[Book] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_books):
        try:
            book = Book.from_dict(raw)
            if book.id in seen:
                raise DuplicateIdError(book.id)
        except (InvalidEntityError, DuplicateIdError) as e:
            raise CorruptedFileError(f"book #{index}: {e}") from e
        seen.add(book.id)
        books.append(book)
    return books
