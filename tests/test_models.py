from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from libcatalog.errors import CatalogError, InvalidEntityError
from libcatalog.models import Book
from tests.helpers import make_book, make_isbn


def test_valid_book_is_created():
    book = make_book(id="a1", title="Dune", year=1965)

    assert book.id == "a1"
    assert book.title == "Dune"
    assert book.year == 1965


def test_isbn_with_hyphens_is_accepted():
    isbn = make_isbn(5)
    hyphenated = f"{isbn[:3]}-{isbn[3:4]}-{isbn[4:]}"

    assert make_book(isbn=hyphenated).isbn == hyphenated


@pytest.mark.parametrize("field", ["id", "title", "category", "author"])
@pytest.mark.parametrize("value", ["", "   ", None, 5])
def test_text_fields_must_be_non_empty_strings(field, value):
    with pytest.raises(InvalidEntityError):
        make_book(**{field: value})


@pytest.mark.parametrize(
    "year", [1449, date.today().year + 1, -1, "2000", 2000.0, True, None]
)
def test_year_must_be_int_in_range(year):
    with pytest.raises(InvalidEntityError):
        make_book(year=year)


@pytest.mark.parametrize(
    "isbn", ["", "123", "9780000000000", "abcdefghijklm", None, 9780000000002]
)
def test_isbn_must_be_valid(isbn):
    with pytest.raises(InvalidEntityError):
        make_book(isbn=isbn)


def test_invalid_entity_error_is_catalog_error():
    with pytest.raises(CatalogError):
        make_book(title="")


def test_book_is_immutable():
    book = make_book()

    with pytest.raises(FrozenInstanceError):
        book.title = "other"  # type: ignore[misc]


def test_dict_round_trip_keeps_all_fields():
    book = make_book()

    assert Book.from_dict(book.to_dict()) == book


def test_from_dict_validates_invariants():
    data = make_book().to_dict()

    with pytest.raises(InvalidEntityError):
        Book.from_dict({**data, "year": 100})
