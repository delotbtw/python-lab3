import random

import pytest

from libcatalog.catalog import Catalog
from libcatalog.errors import DuplicateIdError
from tests.helpers import make_book

CATEGORIES = ["Fantasy", "fantasy", "Sci-Fi", "History", "Poetry"]


def naive(catalog: Catalog, category: str) -> tuple:
    return tuple(
        b
        for b in catalog
        if b.category.strip().casefold() == category.strip().casefold()
    )


def test_index_follows_add():
    catalog = Catalog()
    catalog.add(make_book(id="1", category="Fantasy"))
    catalog.add(make_book(id="2", category="FANTASY"))

    assert [b.id for b in catalog.find_by_category("fantasy")] == ["1", "2"]


def test_remove_updates_index():
    catalog = Catalog()
    catalog.add(make_book(id="1", category="Fantasy"))
    catalog.add(make_book(id="2", category="Fantasy"))

    catalog.remove("1")

    assert [b.id for b in catalog.find_by_category("Fantasy")] == ["2"]


def test_removing_last_book_of_category_drops_the_category():
    catalog = Catalog()
    catalog.add(make_book(id="1", category="Poetry"))

    catalog.remove("1")

    assert catalog.find_by_category("Poetry") == ()
    assert catalog._by_category == {}


def test_failed_add_does_not_touch_index():
    catalog = Catalog()
    catalog.add(make_book(id="1", category="Fantasy"))

    with pytest.raises(DuplicateIdError):
        catalog.add(make_book(id="1", category="History"))

    assert catalog.find_by_category("History") == ()
    assert len(catalog.find_by_category("Fantasy")) == 1


def test_index_matches_linear_scan_after_random_operations():
    rng = random.Random(7)
    catalog = Catalog()
    for step in range(300):
        if rng.random() < 0.6 or not len(catalog):
            catalog.add(make_book(id=f"s{step}", category=rng.choice(CATEGORIES)))
        else:
            catalog.remove(rng.choice([b.id for b in catalog]))
        for category in CATEGORIES:
            assert catalog.find_by_category(category) == naive(catalog, category)
    assert sum(len(ids) for ids in catalog._by_category.values()) == len(catalog)
