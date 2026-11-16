import pytest

from libcatalog.catalog import Catalog, CatalogView, ReadOnlyCatalog
from libcatalog.errors import ItemNotFoundError
from tests.helpers import make_book


def filled() -> Catalog:
    catalog = Catalog()
    catalog.add(make_book(id="a", title="Dune", category="Sci-Fi"))
    catalog.add(make_book(id="b", title="Emma", category="Romance"))
    return catalog


def test_view_reads_like_the_catalog():
    catalog = filled()
    view = catalog.view()

    assert isinstance(view, CatalogView)
    assert isinstance(view, ReadOnlyCatalog)
    assert view.get("a") is catalog.get("a")
    assert len(view) == 2
    assert "b" in view
    assert [b.id for b in view] == ["a", "b"]
    assert [b.id for b in view.find_by_category("sci-fi")] == ["a"]
    assert [b.id for b in view.find_by_name("EMMA")] == ["b"]


@pytest.mark.parametrize(
    "name", ["add", "remove", "undo", "load", "save", "transaction", "view"]
)
def test_view_has_no_mutating_methods(name):
    assert not hasattr(filled().view(), name)


def test_view_is_live():
    catalog = filled()
    view = catalog.view()

    catalog.add(make_book(id="c"))
    catalog.remove("a")

    assert [b.id for b in view] == ["b", "c"]


def test_view_does_not_expose_internal_dict():
    view = filled().view()

    assert not hasattr(view, "_items")
    assert not hasattr(view, "_catalog")
    assert isinstance(view.find_by_name("e"), tuple)


def test_view_missing_id_raises_domain_error():
    with pytest.raises(ItemNotFoundError):
        filled().view().get("nope")
