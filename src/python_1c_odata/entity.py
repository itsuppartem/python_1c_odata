"""CRUD against one 1C OData entity set (Catalog_*, Document_*, ...)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from python_1c_odata.client import Infobase
from python_1c_odata.errors import ODataError
from python_1c_odata.filter import Filter, as_filter_text
from python_1c_odata.page import Page
from python_1c_odata.presentation import SelectFields
from python_1c_odata.query import Query


class EntitySet:
    kind: str = ""

    def __init__(self, infobase: Infobase, name: str) -> None:
        self.infobase = infobase
        self.name = name

    @property
    def entity(self) -> str:
        return f"{self.kind}_{self.name}"

    def url(
        self,
        *,
        key: str | Mapping[str, str] | None = None,
        action: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        select: SelectFields | None = None,
        odata_filter: str | Filter | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        extra: Mapping[str, str] | None = None,
        allowed_only: bool = False,
        inlinecount: bool = False,
        presentations: bool = False,
    ) -> str:
        """Collection or entity URL (same options as ``query`` / ``get``). Does not send."""
        return self.infobase.url(
            self.entity,
            key=key,
            action=action,
            top=top,
            skip=skip,
            select=select,
            odata_filter=as_filter_text(odata_filter),
            expand=expand,
            orderby=orderby,
            extra=extra,
            allowed_only=allowed_only,
            inlinecount=inlinecount,
            presentations=presentations,
        )

    def where(self, expr: str | Filter) -> Query:
        return Query(self).where(expr)

    def build(self) -> Query:
        return Query(self)

    async def query(
        self,
        *,
        top: int | None = None,
        skip: int | None = None,
        select: SelectFields | None = None,
        odata_filter: str | Filter | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        extra: Mapping[str, str] | None = None,
        allowed_only: bool = False,
        inlinecount: bool = False,
        presentations: bool = False,
        timeout: float | None = None,
    ) -> Page:
        payload = await self.infobase.get(
            self.entity,
            top=top,
            skip=skip,
            select=select,
            odata_filter=as_filter_text(odata_filter),
            expand=expand,
            orderby=orderby,
            extra=extra,
            allowed_only=allowed_only,
            inlinecount=inlinecount,
            presentations=presentations,
            timeout=timeout,
        )
        if not isinstance(payload, dict):
            payload = {"value": [] if payload is None else payload}
        return Page(payload)

    async def iterate(
        self,
        *,
        page_size: int = 100,
        skip: int = 0,
        select: SelectFields | None = None,
        odata_filter: str | Filter | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        extra: Mapping[str, str] | None = None,
        allowed_only: bool = False,
        presentations: bool = False,
        timeout: float | None = None,
    ) -> AsyncIterator[Any]:
        offset = skip
        while True:
            page = await self.query(
                top=page_size,
                skip=offset,
                select=select,
                odata_filter=odata_filter,
                expand=expand,
                orderby=orderby,
                extra=extra,
                allowed_only=allowed_only,
                presentations=presentations,
                timeout=timeout,
            )
            if not page.value:
                break
            for row in page.value:
                yield row
            if len(page.value) < page_size:
                break
            offset += page_size

    async def count(
        self,
        *,
        odata_filter: str | Filter | None = None,
        extra: Mapping[str, str] | None = None,
        allowed_only: bool = False,
        timeout: float | None = None,
    ) -> int:
        page = await self.query(
            top=0,
            inlinecount=True,
            odata_filter=odata_filter,
            extra=extra,
            allowed_only=allowed_only,
            timeout=timeout,
        )
        if page.count is None:
            raise ODataError(200, "server did not return $inlinecount")
        return page.count

    async def get(
        self,
        key: str | Mapping[str, str],
        *,
        select: SelectFields | None = None,
        presentations: bool = False,
        timeout: float | None = None,
    ) -> Any:
        return await self.infobase.get(
            self.entity,
            key=key,
            select=select,
            presentations=presentations,
            timeout=timeout,
        )

    async def create(
        self,
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.infobase.post(
            self.entity, json=data, timeout=timeout, data_load_mode=data_load_mode
        )

    async def edit(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.infobase.patch(
            self.entity,
            key=key,
            json=data,
            timeout=timeout,
            if_match=if_match,
            data_load_mode=data_load_mode,
        )

    async def replace(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.infobase.put(
            self.entity,
            key=key,
            json=data,
            timeout=timeout,
            if_match=if_match,
            data_load_mode=data_load_mode,
        )

    async def delete(
        self,
        key: str | Mapping[str, str],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.infobase.delete(
            self.entity,
            key=key,
            timeout=timeout,
            if_match=if_match,
            data_load_mode=data_load_mode,
        )


class ReadOnlyEntitySet(EntitySet):
    """Journals and enumerations: query / get / iterate / count only."""

    def _read_only_error(self) -> TypeError:
        return TypeError(f"{type(self).__name__} is read-only over OData")

    async def create(
        self,
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        raise self._read_only_error()

    async def edit(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        raise self._read_only_error()

    async def replace(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        raise self._read_only_error()

    async def delete(
        self,
        key: str | Mapping[str, str],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        raise self._read_only_error()
