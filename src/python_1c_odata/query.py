"""Fluent builder on top of EntitySet.query / iterate / count."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any

from python_1c_odata.filter import Filter
from python_1c_odata.page import Page
from python_1c_odata.presentation import SelectFields

if TYPE_CHECKING:
    from python_1c_odata.entity import EntitySet


class Query:
    def __init__(self, entity_set: EntitySet) -> None:
        self._entity_set = entity_set
        self._top: int | None = None
        self._skip: int | None = None
        self._select: SelectFields | None = None
        self._odata_filter: str | Filter | None = None
        self._expand: str | None = None
        self._orderby: str | None = None
        self._extra: Mapping[str, str] | None = None
        self._allowed_only = False
        self._inlinecount = False
        self._presentations = False

    def where(self, expr: str | Filter) -> Query:
        self._odata_filter = expr
        return self

    def top(self, n: int) -> Query:
        self._top = n
        return self

    def skip(self, n: int) -> Query:
        self._skip = n
        return self

    def select(self, fields: SelectFields) -> Query:
        self._select = fields
        return self

    def expand(self, fields: str) -> Query:
        self._expand = fields
        return self

    def orderby(self, expr: str) -> Query:
        self._orderby = expr
        return self

    def extra(self, extra: Mapping[str, str]) -> Query:
        self._extra = extra
        return self

    def allowed_only(self, enabled: bool = True) -> Query:
        self._allowed_only = enabled
        return self

    def inlinecount(self, enabled: bool = True) -> Query:
        self._inlinecount = enabled
        return self

    def presentations(self, enabled: bool = True) -> Query:
        self._presentations = enabled
        return self

    async def execute(self) -> Page:
        return await self._entity_set.query(**self._kwargs())

    async def count(self) -> int:
        return await self._entity_set.count(
            odata_filter=self._odata_filter,
            extra=self._extra,
            allowed_only=self._allowed_only,
        )

    def iterate(self, *, page_size: int = 100) -> AsyncIterator[Any]:
        size = self._top if self._top is not None else page_size
        return self._entity_set.iterate(
            page_size=size,
            skip=self._skip or 0,
            select=self._select,
            odata_filter=self._odata_filter,
            expand=self._expand,
            orderby=self._orderby,
            extra=self._extra,
            allowed_only=self._allowed_only,
            presentations=self._presentations,
        )

    def _kwargs(self) -> dict[str, Any]:
        return {
            "top": self._top,
            "skip": self._skip,
            "select": self._select,
            "odata_filter": self._odata_filter,
            "expand": self._expand,
            "orderby": self._orderby,
            "extra": self._extra,
            "allowed_only": self._allowed_only,
            "inlinecount": self._inlinecount,
            "presentations": self._presentations,
        }
