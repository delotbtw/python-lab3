import json
import tempfile
from pathlib import Path

from libcatalog import (
    Book,
    Catalog,
    CatalogError,
    DuplicateIdError,
    InvalidEntityError,
    ItemNotFoundError,
    NothingToUndoError,
    TransactionError,
)


def main() -> None:
    print("1. Добавляем книги")
    catalog = Catalog()
    catalog.add(
        Book("b1", "Dune", "Sci-Fi", 1965, "Frank Herbert", "978-0-441-17271-9")
    )
    catalog.add(
        Book(
            "b2", "The Hobbit", "Fantasy", 1937, "J. R. R. Tolkien", "978-0-261-10221-7"
        )
    )
    catalog.add(Book("b3", "Emma", "Romance", 1815, "Jane Austen", "978-0-14-143958-7"))
    print("количество:", len(catalog))
    print("порядок:", [b.id for b in catalog])
    print("b1 в каталоге:", "b1" in catalog)
    input("\n[Enter] ")

    print("2. Проверки Book")
    # неверные книги не создаются, поэтому в каталог попасть не могут
    try:
        Book("b9", "", "Poetry", 2000, "Author", "978-0-14-143958-7")
    except InvalidEntityError as e:
        print("пустое название:", e)
    try:
        Book("b9", "X", "Poetry", 3000, "Author", "978-0-14-143958-7")
    except InvalidEntityError as e:
        print("неверный год:", e)
    try:
        Book("b9", "X", "Poetry", 2000, "Author", "978-0-14-143958-0")
    except InvalidEntityError as e:
        print("неверный ISBN:", e)
    input("\n[Enter] ")

    print("3. get, дубликат, неизвестный id")
    print(catalog.get("b1"))
    try:
        catalog.add(catalog.get("b1"))
    except DuplicateIdError as e:
        print("дубликат:", e)
    try:
        catalog.get("missing")
    except ItemNotFoundError as e:
        print("не найдено:", e)
    input("\n[Enter] ")

    print("4. Поиск, регистр не важен")
    print("по названию 'tHe':", [b.title for b in catalog.find_by_name("tHe")])
    print(
        "по категории 'FANTASY':",
        [b.title for b in catalog.find_by_category("FANTASY")],
    )
    print("неизвестная категория:", catalog.find_by_category("nothing"))
    input("\n[Enter] ")

    print("5. Undo и индекс по категории")
    catalog.remove("b2")
    print("после remove:", [b.id for b in catalog])
    print("fantasy:", catalog.find_by_category("fantasy"))
    # undo возвращает книгу на прежнее место и обновляет индекс
    catalog.undo()
    print("после undo:", [b.id for b in catalog])
    print("fantasy:", [b.title for b in catalog.find_by_category("fantasy")])
    try:
        Catalog().undo()
    except NothingToUndoError as e:
        print("пустой каталог:", e)
    input("\n[Enter] ")

    print("6. Транзакция")
    before = [b.id for b in catalog]
    # ошибка внутри блока откатывает все изменения из блока
    try:
        with catalog.transaction():
            catalog.remove("b1")
            catalog.add(
                Book("b5", "Tmp", "Poetry", 2000, "Author", "978-0-14-143958-7")
            )
            catalog.remove("missing")
    except CatalogError as e:
        print("ошибка в блоке:", e)
    print("откатилось:", [b.id for b in catalog] == before)
    # без ошибки изменения остаются
    with catalog.transaction():
        catalog.add(Book("b7", "Ok", "Poetry", 2000, "Author", "978-0-14-143958-7"))
    print("без ошибки изменения остались:", "b7" in catalog)
    catalog.undo()
    try:
        with catalog.transaction():
            catalog.undo()
    except TransactionError as e:
        print("undo внутри транзакции:", e)
    input("\n[Enter] ")

    print("7. Read-only view")
    view = catalog.view()
    print("длина view:", len(view))
    print("поиск через view:", [b.title for b in view.find_by_name("dune")])
    print("есть add:", hasattr(view, "add"))
    print("есть remove:", hasattr(view, "remove"))
    # view живой: он не копирует данные, а смотрит в каталог
    catalog.add(
        Book("b6", "Ulysses", "Novel", 1922, "James Joyce", "978-0-14-143958-7")
    )
    print("длина view после add в каталог:", len(view))
    catalog.undo()
    input("\n[Enter] ")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "catalog.json"

        print("8. Сохранение и загрузка")
        catalog.save(path)
        print(path.read_text(encoding="utf-8"))
        other = Catalog()
        other.load(path)
        print("загружено:", [b.id for b in other])
        input("\n[Enter] ")

        print("9. Битые файлы, каталог не меняется")
        bad_files = {
            "неверная версия": json.dumps({"format_version": 2, "books": []}),
            "не JSON": "not a json",
            "битая книга": json.dumps({"format_version": 1, "books": [{"id": "x"}]}),
        }
        for name, text in bad_files.items():
            path.write_text(text, encoding="utf-8")
            try:
                catalog.load(path)
            except CatalogError as e:
                print(f"{name}: {type(e).__name__}: {e}")
        print("каталог:", [b.id for b in catalog])

    print("\nГотово")


if __name__ == "__main__":
    main()
