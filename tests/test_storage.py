import json

import pytest

from libcatalog.catalog import Catalog
from libcatalog.core import FORMAT_VERSION
from libcatalog.errors import CatalogError, CorruptedFileError, UnsupportedVersionError
from tests.helpers import make_book


def write(path, document):
    path.write_text(json.dumps(document), encoding="utf-8")


def good_document():
    return {"format_version": FORMAT_VERSION, "books": [make_book(id="a").to_dict()]}


def test_round_trip_keeps_all_fields_and_order(tmp_path):
    source = Catalog()
    for book in (
        make_book(id="b", title="Война и мир", category="Классика", year=1869),
        make_book(id="a", title="Dune", category="Sci-Fi", year=1965),
        make_book(id="c", title="Emma", category="Romance", year=1815),
    ):
        source.add(book)
    path = tmp_path / "catalog.json"

    source.save(path)
    loaded = Catalog()
    loaded.load(path)

    assert list(loaded) == list(source)
    assert [b.id for b in loaded] == ["b", "a", "c"]
    assert [b.id for b in loaded.find_by_category("sci-fi")] == ["a"]


def test_saved_document_has_format_version_at_root(tmp_path):
    path = tmp_path / "catalog.json"
    Catalog().save(path)

    document = json.loads(path.read_text(encoding="utf-8"))

    assert document["format_version"] == FORMAT_VERSION
    assert document["books"] == []


def test_save_keeps_unicode_readable(tmp_path):
    catalog = Catalog()
    catalog.add(make_book(title="Мастер и Маргарита"))
    path = tmp_path / "catalog.json"

    catalog.save(path)

    assert "Мастер и Маргарита" in path.read_text(encoding="utf-8")


def test_save_leaves_no_temporary_files(tmp_path):
    Catalog().save(tmp_path / "catalog.json")

    assert [p.name for p in tmp_path.iterdir()] == ["catalog.json"]


def test_load_replaces_existing_content(tmp_path):
    path = tmp_path / "catalog.json"
    write(path, good_document())
    catalog = Catalog()
    catalog.add(make_book(id="old"))

    catalog.load(path)

    assert [b.id for b in catalog] == ["a"]
    assert "old" not in catalog


def test_unknown_version_is_rejected(tmp_path):
    path = tmp_path / "catalog.json"
    write(path, {"format_version": 99, "books": []})

    with pytest.raises(UnsupportedVersionError) as info:
        Catalog().load(path)

    assert info.value.version == 99


@pytest.mark.parametrize("version", ["1", None, True, 1.5])
def test_version_of_wrong_type_is_rejected(tmp_path, version):
    path = tmp_path / "catalog.json"
    write(path, {"format_version": version, "books": []})

    with pytest.raises(UnsupportedVersionError):
        Catalog().load(path)


@pytest.mark.parametrize("content", ["", "{", "{'a': 1}", '{"format_version": 1,'])
def test_broken_json_is_corrupted_file(tmp_path, content):
    path = tmp_path / "catalog.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(CorruptedFileError):
        Catalog().load(path)


def test_binary_garbage_is_corrupted_file(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_bytes(b"\xff\xfe\x00\x01")

    with pytest.raises(CorruptedFileError):
        Catalog().load(path)


def test_invalid_book_in_file_is_corrupted_file(tmp_path):
    document = good_document()
    document["books"].append({**make_book(id="z").to_dict(), "year": 5})
    path = tmp_path / "catalog.json"
    write(path, document)

    with pytest.raises(CorruptedFileError, match="book #1"):
        Catalog().load(path)


def test_duplicate_id_in_file_is_corrupted_file(tmp_path):
    document = good_document()
    document["books"].append(make_book(id="a").to_dict())
    path = tmp_path / "catalog.json"
    write(path, document)

    with pytest.raises(CorruptedFileError, match="duplicate"):
        Catalog().load(path)


def test_all_load_errors_are_catalog_errors(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(CatalogError):
        Catalog().load(path)


def test_missing_file_is_os_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        Catalog().load(tmp_path / "nope.json")
