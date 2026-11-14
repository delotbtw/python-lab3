from libcatalog.catalog import Catalog, ReadOnlyCatalog
from tests.helpers import make_book


def fill() -> Catalog:
    catalog = Catalog()
    catalog.add(make_book(id="1", title="The Hobbit", category="Fantasy"))
    catalog.add(make_book(id="2", title="Dune", category="Sci-Fi"))
    catalog.add(make_book(id="3", title="The Silmarillion", category="fantasy"))
    return catalog


def test_find_by_category_ignores_case():
    catalog = fill()

    assert [b.id for b in catalog.find_by_category("FANTASY")] == ["1", "3"]
    assert [b.id for b in catalog.find_by_category(" sci-fi ")] == ["2"]


def test_find_by_category_unknown_is_empty():
    assert fill().find_by_category("Poetry") == ()


def test_find_by_name_ignores_case_and_matches_substring():
    catalog = fill()

    assert [b.id for b in catalog.find_by_name("THE")] == ["1", "3"]
    assert [b.id for b in catalog.find_by_name("dUnE")] == ["2"]


def test_find_by_name_empty_or_missing_query_finds_nothing():
    catalog = fill()

    assert catalog.find_by_name("") == ()
    assert catalog.find_by_name("   ") == ()
    assert catalog.find_by_name("zzz") == ()


def test_search_result_is_a_copy_not_internal_state():
    catalog = fill()

    result = catalog.find_by_name("the")

    assert isinstance(result, tuple)
    assert not hasattr(result, "append")
    assert len(catalog) == 3
    assert catalog.find_by_name("the") == result


def test_iteration_order_is_insertion_order_and_stable():
    catalog = fill()

    first = [b.id for b in catalog]
    second = [b.id for b in catalog]

    assert first == second == ["1", "2", "3"]


def test_removal_keeps_order_of_the_rest():
    catalog = fill()
    catalog.remove("2")
    catalog.add(make_book(id="4"))

    assert [b.id for b in catalog] == ["1", "3", "4"]


def test_modifying_catalog_during_iteration_is_safe():
    catalog = fill()

    for book in catalog:
        catalog.remove(book.id)

    assert len(catalog) == 0


def test_len_and_contains():
    catalog = fill()

    assert len(catalog) == 3
    assert "1" in catalog
    assert "99" not in catalog
    assert 1 not in catalog
    assert ["1"] not in catalog


def test_empty_catalog_is_falsy_and_iterates_nothing():
    catalog = Catalog()

    assert not catalog
    assert list(catalog) == []


def test_catalog_is_a_read_only_catalog():
    assert isinstance(Catalog(), ReadOnlyCatalog)
