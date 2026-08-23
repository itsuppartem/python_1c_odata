"""CRUD against one 1C OData entity set (Catalog_*, Document_*, ...)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from python_1c_odata.client import Infobase


class EntitySet:
    kind: str = ""

    def __init__(self, infobase: Infobase, name: str) -> None:
        self.infobase = infobase
        self.name = name

    @property
    def entity(self) -> str:
        return f"{self.kind}_{self.name}"

    async def query(
        self,
        *,
        top: int | None = None,
        skip: int | None = None,
        select: str | None = None,
        odata_filter: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        extra: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self.infobase.get(
            self.entity,
            top=top,
            skip=skip,
            select=select,
            odata_filter=odata_filter,
            expand=expand,
            orderby=orderby,
            extra=extra,
            timeout=timeout,
        )

    async def get(
        self,
        key: str | Mapping[str, str],
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self.infobase.get(self.entity, key=key, select=select, timeout=timeout)

    async def create(self, data: dict[str, Any], *, timeout: float | None = None) -> Any:
        return await self.infobase.post(self.entity, json=data, timeout=timeout)

    async def edit(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> Any:
        return await self.infobase.patch(self.entity, key=key, json=data, timeout=timeout)

    async def replace(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> Any:
        return await self.infobase.put(self.entity, key=key, json=data, timeout=timeout)

    async def delete(self, key: str | Mapping[str, str], *, timeout: float | None = None) -> Any:
        return await self.infobase.delete(self.entity, key=key, timeout=timeout)
