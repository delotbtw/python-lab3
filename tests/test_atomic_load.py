import json

import pytest

from libcatalog.catalog import Catalog
from libcatalog.core import FORMAT_VERSION
from libcatalog.errors import CatalogError
from tests.helpers import make_book


def prepared() -> Catalog:
    catalog = Catalog()
    catalog.add(make_book(id="keep1", category="Fantasy"))
    catalog.add(make_book(id="keep2", category="History"))
    return catalog


def snapshot(catalog: Catalog):
    return (
        list(catalog),
        {
            c: [b.id for b in catalog.find_by_category(c)]
            for c in ("Fantasy", "History", "New")
        },
    )


def broken_in_the_middle(path, bad_book):
    books = [make_book(id=f"new{i}", category="New").to_dict() for i in range(5)]
    books.insert(3, bad_book)
    path.write_text(
        json.dumps({"format_version": FORMAT_VERSION, "books": books}), encoding="utf-8"
    )


@pytest.mark.parametrize(
    "bad_book",
    [
        {"id": "x"},
        "string instead of object",
        {**make_book(id="x").to_dict(), "year": "1999"},
        make_book(id="new1").to_dict(),
    ],
)
def test_error_in_the_middle_keeps_catalog_unchanged(tmp_path, bad_book):
    path = tmp_path / "catalog.json"
    broken_in_the_middle(path, bad_book)
    catalog = prepared()
    before = snapshot(catalog)

    with pytest.raises(CatalogError):
        catalog.load(path)

    assert snapshot(catalog) == before
    assert len(catalog) == 2
    assert "new0" not in catalog


def test_truncated_json_keeps_catalog_unchanged(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text('{"format_version": 1, "books": [{"id": "n"', encoding="utf-8")
    catalog = prepared()
    before = snapshot(catalog)

    with pytest.raises(CatalogError):
        catalog.load(path)

    assert snapshot(catalog) == before


def test_unknown_version_keeps_catalog_unchanged(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text('{"format_version": 2, "books": []}', encoding="utf-8")
    catalog = prepared()
    before = snapshot(catalog)

    with pytest.raises(CatalogError):
        catalog.load(path)

    assert snapshot(catalog) == before


def test_catalog_still_works_after_failed_load(tmp_path):
    path = tmp_path / "catalog.json"
    broken_in_the_middle(path, {"id": "x"})
    catalog = prepared()
    with pytest.raises(CatalogError):
        catalog.load(path)

    catalog.add(make_book(id="after", category="Fantasy"))
    catalog.remove("keep1")

    assert [b.id for b in catalog.find_by_category("Fantasy")] == ["after"]


def test_successful_load_replaces_indexes_too(tmp_path):
    path = tmp_path / "catalog.json"
    broken_in_the_middle(path, make_book(id="ok", category="New").to_dict())
    catalog = prepared()

    catalog.load(path)

    assert catalog.find_by_category("Fantasy") == ()
    assert len(catalog.find_by_category("New")) == 6
