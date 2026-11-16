# libcatalog

Каталог библиотечных книг: сущность `Book` (dataclass), `Catalog` с поиском,
индексом по категории, undo и транзакциями, сохранение в JSON.

Лабораторная работа 3 по Python. Предметная область: библиотечные книги.

## Установка и запуск

Нужен Python 3.12+ и [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run pytest
uv run python scripts/demo.py
```

## Быстрый старт

```python
from libcatalog import Book, Catalog

catalog = Catalog()
catalog.add(Book("b1", "Dune", "Sci-Fi", 1965, "Frank Herbert", "978-0-441-17271-9"))

catalog.get("b1")
catalog.find_by_name("dUnE")
catalog.find_by_category("sci-fi")
catalog.save("catalog.json")
catalog.load("catalog.json")
```

## Структура

```
src/libcatalog/
  core.py      константы и enum ChangeKind
  errors.py    исключения
  models.py    Book
  catalog.py   Catalog и CatalogView
  storage.py   чтение и запись JSON
tests/
scripts/demo.py
```

## Книга

`Book` — неизменяемый dataclass. Инварианты проверяются при создании, поэтому
неверная книга не может попасть в каталог.

| Поле | Проверка |
|---|---|
| `id` | непустая строка |
| `title` | непустая строка |
| `category` | непустая строка |
| `year` | `int` от 1450 до текущего года |
| `author` | непустая строка |
| `isbn` | корректный ISBN-13 |

## Каталог

| Метод | Сложность |
|---|---|
| `add(item)` | O(1) |
| `get(item_id)` | O(1), поиск через словарь |
| `remove(item_id)` | O(1) |
| `find_by_category(category)` | O(k), индекс по категории |
| `find_by_name(query)` | O(n·L), перебор названий |
| `len(c)`, `id in c` | O(1) |
| `for book in c` | O(n) |

- **Порядок итерации:** порядок добавления, при каждом проходе один и тот же.
  Удаление не меняет порядок остальных книг.
- Поиск не учитывает регистр и возвращает новый `tuple`, а не внутренний список.
- Повторный `id` — `DuplicateIdError`, неизвестный `id` — `ItemNotFoundError`.

## Исключения

```
CatalogError
├── InvalidEntityError
├── DuplicateIdError
├── ItemNotFoundError
├── UnsupportedVersionError
├── CorruptedFileError
├── NothingToUndoError
└── TransactionError
```

## JSON

```json
{
  "format_version": 1,
  "books": [
    {"id": "b1", "title": "Dune", "category": "Sci-Fi", "year": 1965,
     "author": "Frank Herbert", "isbn": "978-0-441-17271-9"}
  ]
}
```

- Другая версия формата — `UnsupportedVersionError`.
- Не JSON, неверная структура, невалидная книга или дубликат id — `CorruptedFileError`.
- `load` сначала читает и проверяет весь файл, и только потом заменяет содержимое
  каталога. Если ошибка в любом месте файла, каталог остаётся прежним.

## Дополнительные задания

- **Индекс по категории.** Работает сам: `find_by_category` ищет по индексу, он
  обновляется при `add`, `remove`, `undo` и откате транзакции.
- **Undo.** `catalog.undo()` отменяет последний `add` или `remove`.
- **Read-only view.** `catalog.view()` возвращает представление, через которое
  каталог можно только читать.
- **Транзакции.**

  ```python
  with catalog.transaction():
      catalog.add(book1)
      catalog.remove("x")
  ```

  Если внутри блока ошибка, все изменения из блока откатываются.

## Тесты

```bash
uv run pytest
uv run pytest --cov=libcatalog --cov-branch --cov-report=term-missing
```

Вторая команда показывает покрытие тестами вместе со строками, которые не покрыты.

Тесты лежат в `tests/`: инварианты книги, операции каталога, поиск и протоколы,
индекс, JSON и версии, атомарность загрузки, undo, транзакции, view.

## Проверки кода

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

- `ruff check` — линтер, `ruff format --check` — проверка форматирования.
- `mypy src` — проверка типов в strict-режиме.

## Защита

### 1. Добавить новое проверяемое поле

Например, `pages: int` (положительное число страниц). В `models.py` добавить
поле и проверку:

```python
pages: int = 1

# в __post_init__
if isinstance(self.pages, bool) or not isinstance(self.pages, int) or self.pages <= 0:
    raise InvalidEntityError(f"invalid pages: {self.pages!r}")
```

`to_dict` и `from_dict` менять не надо, они работают по `dataclasses.fields`.
Значение по умолчанию позволяет читать старые файлы. Потом добавить тест в
`test_models.py`.

### 2. Сложность `get` и `find_by_name`

- `get` — O(1): `dict` это хеш-таблица, по `id` сразу находится книга.
- `find_by_name` — O(n·L): нужно проверить подстроку в названии каждой из `n`
  книг, индекс по словарю тут не помогает.

### 3. Тест частично повреждённого документа

Шаблон лежит в `tests/test_atomic_load.py`:

```python
def test_partially_corrupted_document(tmp_path):
    books = [make_book(id=f"n{i}").to_dict() for i in range(5)]
    books.insert(3, {"id": "broken"})
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"format_version": 1, "books": books}))
    catalog = prepared()
    before = list(catalog)

    with pytest.raises(CorruptedFileError):
        catalog.load(path)

    assert list(catalog) == before
```

`load` собирает результат отдельно и подменяет состояние каталога только после
полного успеха.
