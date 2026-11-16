import pytest

from libcatalog.catalog import Catalog
from libcatalog.errors import CatalogError, NothingToUndoError
from tests.helpers import make_book


def ids(catalog: Catalog) -> list[str]:
    return [b.id for b in catalog]


def test_undo_add_removes_the_book():
    catalog = Catalog()
    catalog.add(make_book(id="a"))
    catalog.add(make_book(id="b"))

    catalog.undo()

    assert ids(catalog) == ["a"]
    assert "b" not in catalog


def test_undo_remove_restores_book_at_original_position():
    catalog = Catalog()
    for i in "abcd":
        catalog.add(make_book(id=i))

    catalog.remove("b")
    catalog.undo()

    assert ids(catalog) == ["a", "b", "c", "d"]


def test_undo_remove_restores_category_index_in_order():
    catalog = Catalog()
    for i in "abc":
        catalog.add(make_book(id=i, category="Fantasy"))
    catalog.add(make_book(id="x", category="History"))

    catalog.remove("a")
    catalog.undo()

    assert [b.id for b in catalog.find_by_category("fantasy")] == ["a", "b", "c"]
    assert [b.id for b in catalog.find_by_category("history")] == ["x"]


def test_undo_add_updates_category_index():
    catalog = Catalog()
    catalog.add(make_book(id="a", category="Poetry"))

    catalog.undo()

    assert catalog.find_by_category("Poetry") == ()
    assert catalog._by_category == {}


def test_undo_goes_back_step_by_step_to_empty():
    catalog = Catalog()
    catalog.add(make_book(id="a"))
    catalog.add(make_book(id="b"))
    catalog.remove("a")

    catalog.undo()
    assert ids(catalog) == ["a", "b"]
    catalog.undo()
    assert ids(catalog) == ["a"]
    catalog.undo()
    assert ids(catalog) == []


def test_failed_operations_are_not_journaled():
    catalog = Catalog()
    catalog.add(make_book(id="a"))
    with pytest.raises(CatalogError):
        catalog.add(make_book(id="a"))
    with pytest.raises(CatalogError):
        catalog.remove("nope")

    catalog.undo()

    assert ids(catalog) == []
    with pytest.raises(NothingToUndoError):
        catalog.undo()


def test_undo_does_not_undo_itself():
    catalog = Catalog()
    catalog.add(make_book(id="a"))
    catalog.undo()

    with pytest.raises(NothingToUndoError):
        catalog.undo()


def test_load_clears_history(tmp_path):
    path = tmp_path / "c.json"
    source = Catalog()
    source.add(make_book(id="a"))
    source.save(path)
    catalog = Catalog()
    catalog.add(make_book(id="x"))

    catalog.load(path)

    with pytest.raises(NothingToUndoError):
        catalog.undo()
    assert ids(catalog) == ["a"]


def test_added_after_undo_goes_to_the_end():
    catalog = Catalog()
    for i in "abc":
        catalog.add(make_book(id=i))
    catalog.remove("a")
    catalog.undo()

    catalog.add(make_book(id="d"))

    assert ids(catalog) == ["a", "b", "c", "d"]
