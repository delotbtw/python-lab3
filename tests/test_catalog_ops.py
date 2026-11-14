import pytest

from libcatalog.catalog import Catalog
from libcatalog.errors import (
    CatalogError,
    DuplicateIdError,
    ItemNotFoundError,
)
from tests.helpers import make_book


def test_add_and_get():
    catalog = Catalog()
    book = make_book(id="x")

    catalog.add(book)

    assert catalog.get("x") is book
    assert len(catalog) == 1


def test_add_returns_none():
    assert Catalog().add(make_book()) is None


def test_duplicate_id_is_rejected_and_catalog_unchanged():
    catalog = Catalog()
    first = make_book(id="x", title="First")
    catalog.add(first)

    with pytest.raises(DuplicateIdError) as info:
        catalog.add(make_book(id="x", title="Second"))

    assert info.value.item_id == "x"
    assert len(catalog) == 1
    assert catalog.get("x") is first


def test_get_missing_raises_domain_error():
    with pytest.raises(ItemNotFoundError):
        Catalog().get("nope")


def test_get_with_unhashable_id_raises_domain_error():
    with pytest.raises(ItemNotFoundError):
        Catalog().get(["x"])  # type: ignore[arg-type]


def test_remove_returns_book_and_deletes_it():
    catalog = Catalog()
    book = make_book(id="x")
    catalog.add(book)

    assert catalog.remove("x") is book

    assert "x" not in catalog
    assert len(catalog) == 0
    with pytest.raises(ItemNotFoundError):
        catalog.get("x")


def test_remove_missing_raises_domain_error():
    with pytest.raises(ItemNotFoundError) as info:
        Catalog().remove("nope")

    assert isinstance(info.value, CatalogError)


def test_removed_id_can_be_added_again():
    catalog = Catalog()
    catalog.add(make_book(id="x"))
    catalog.remove("x")

    catalog.add(make_book(id="x", title="New"))

    assert catalog.get("x").title == "New"
