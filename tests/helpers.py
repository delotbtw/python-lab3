from itertools import count

from libcatalog.models import Book

_ids = count(1)


def make_isbn(seed: int) -> str:
    """
    Build a valid ISBN-13 from a number
    :param seed: any non-negative number
    :return: ISBN-13 with correct control digit
    """
    body = f"978{seed:09d}"
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body))
    return body + str((10 - total % 10) % 10)


def make_book(**overrides: object) -> Book:
    """
    Build a valid book, any field can be overridden
    :param overrides: fields to replace
    :return: book
    """
    n = next(_ids)
    data: dict[str, object] = {
        "id": f"b{n}",
        "title": f"Title {n}",
        "category": "Fantasy",
        "year": 2000,
        "author": "Author",
        "isbn": make_isbn(n),
    }
    data.update(overrides)
    return Book(**data)  # type: ignore[arg-type]
