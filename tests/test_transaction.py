import pytest

from libcatalog.catalog import Catalog
from libcatalog.errors import (
    DuplicateIdError,
    ItemNotFoundError,
    NothingToUndoError,
)
from tests.helpers import make_book


def filled() -> Catalog:
    catalog = Catalog()
    for i in "abc":
        catalog.add(make_book(id=i, category="Fantasy"))
    return catalog


def state(catalog: Catalog):
    return (
        list(catalog),
        catalog.find_by_category("Fantasy"),
        catalog.find_by_category("New"),
    )


def test_successful_transaction_keeps_changes():
    catalog = filled()

    with catalog.transaction():
        catalog.add(make_book(id="d"))
        catalog.remove("a")

    assert [b.id for b in catalog] == ["b", "c", "d"]


def test_error_rolls_back_everything_including_indexes():
    catalog = filled()
    before = state(catalog)

    with pytest.raises(ItemNotFoundError), catalog.transaction():
        catalog.add(make_book(id="n1", category="New"))
        catalog.remove("a")
        catalog.add(make_book(id="n2", category="New"))
        catalog.remove("nope")

    assert state(catalog) == before
    assert [b.id for b in catalog] == ["a", "b", "c"]


def test_duplicate_inside_transaction_rolls_back_earlier_adds():
    catalog = filled()

    with pytest.raises(DuplicateIdError), catalog.transaction():
        catalog.add(make_book(id="n1"))
        catalog.add(make_book(id="a"))

    assert "n1" not in catalog
    assert len(catalog) == 3


def test_any_exception_triggers_rollback_and_is_reraised():
    catalog = filled()

    with pytest.raises(ZeroDivisionError), catalog.transaction():
        catalog.remove("b")
        raise ZeroDivisionError

    assert [b.id for b in catalog] == ["a", "b", "c"]


def test_rollback_does_not_touch_earlier_history():
    catalog = filled()

    with pytest.raises(RuntimeError), catalog.transaction():
        catalog.add(make_book(id="n1"))
        raise RuntimeError

    catalog.undo()
    assert [b.id for b in catalog] == ["a", "b"]


def test_committed_changes_can_be_undone_one_by_one():
    catalog = Catalog()
    with catalog.transaction():
        catalog.add(make_book(id="a"))
        catalog.add(make_book(id="b"))

    catalog.undo()
    catalog.undo()

    assert len(catalog) == 0
    with pytest.raises(NothingToUndoError):
        catalog.undo()


def test_inner_rollback_reverts_only_its_own_part():
    catalog = filled()

    with catalog.transaction():
        catalog.add(make_book(id="outer"))
        with pytest.raises(ValueError), catalog.transaction():
            catalog.add(make_book(id="inner"))
            raise ValueError
        catalog.add(make_book(id="after"))

    assert [b.id for b in catalog] == ["a", "b", "c", "outer", "after"]


def test_outer_rollback_reverts_committed_inner_part():
    catalog = filled()

    with pytest.raises(ValueError), catalog.transaction():
        with catalog.transaction():
            catalog.add(make_book(id="inner"))
        raise ValueError

    assert [b.id for b in catalog] == ["a", "b", "c"]


def test_catalog_works_after_rolled_back_transaction():
    catalog = filled()
    with pytest.raises(RuntimeError), catalog.transaction():
        catalog.remove("a")
        raise RuntimeError

    catalog.undo()
    catalog.add(make_book(id="z"))

    assert [b.id for b in catalog] == ["a", "b", "z"]


def test_transaction_yields_the_catalog():
    catalog = Catalog()

    with catalog.transaction() as tx:
        assert tx is catalog
