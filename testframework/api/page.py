#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from typing import Any, Final

__all__ = ["DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "Page", "PageMeta", "Pageable"]

DEFAULT_PAGE_SIZE: Final = 20
MAX_PAGE_SIZE: Final = 100
DEFAULT_PAGE_NUMBER: Final = 0


@dataclass(eq=False, slots=True, kw_only=True)
class Pageable:
    """Parsed `?page=&size=` query parameters."""

    size: int
    number: int

    @staticmethod
    def create(number: str | None = None, size: str | None = None) -> "Pageable":
        number_int: Final = (
            DEFAULT_PAGE_NUMBER if number is None or not number.isdigit() else int(number)
        )
        size_int: Final = (
            DEFAULT_PAGE_SIZE
            if size is None or not size.isdigit() or not (1 <= int(size) <= MAX_PAGE_SIZE)
            else int(size)
        )
        return Pageable(size=size_int, number=number_int)


@dataclass(eq=False, slots=True, kw_only=True)
class PageMeta:
    size: int
    number: int
    total_elements: int
    total_pages: int


@dataclass(eq=False, slots=True, kw_only=True)
class Page:
    """A page of already-serialized (dict) results, plus pagination metadata."""

    content: Sequence[dict[str, Any]]
    page: PageMeta

    @staticmethod
    def create(
        content: Sequence[dict[str, Any]], pageable: Pageable, total_elements: int
    ) -> "Page":
        total_pages: Final = ceil(total_elements / pageable.size) if total_elements else 0
        return Page(
            content=content,
            page=PageMeta(
                size=pageable.size,
                number=pageable.number,
                total_elements=total_elements,
                total_pages=total_pages,
            ),
        )
